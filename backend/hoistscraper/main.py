"""FastAPI application entry point."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
from . import models, db
from datetime import datetime, timezone, timedelta
import logging
import os
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
from pathlib import Path
# from routers import ingest, jobs  # Removed - routers deleted
from .auth.api_auth import optional_api_key
from .logging_config import setup_from_env, get_logger, log_performance, log_security_event
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from .monitoring import (
    init_sentry, get_metrics, HealthCheck, monitor_performance,
    track_api_metrics, track_scrape_job_metrics, track_opportunities_metrics,
    update_active_jobs, update_websites_metrics, update_worker_health,
    update_database_connections, update_ollama_status
)
import time

# Configure logging from environment
setup_from_env("hoistscraper")
logger = get_logger(__name__)

async def auto_seed_from_csv(csv_path: str):
    """Auto-seed database from CSV file if database is empty."""
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cli.import_csv import run
    
    # Check if path exists
    if not Path(csv_path).exists():
        logger.warning(f"CSV seed file not found: {csv_path}")
        return
    
    # Check if database is empty
    session_gen = db.get_session()
    session = next(session_gen)
    try:
        existing_count = session.exec(select(models.Website)).first()
        if existing_count:
            logger.info("Database already has data, skipping auto-seed")
            return
    finally:
        try:
            session_gen.close()
        except Exception:
            pass
    
    # Run the import
    logger.info(f"Auto-seeding from CSV: {csv_path}")
    imported = run(csv_path)
    logger.info(f"Auto-seed complete: imported {imported} websites")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup
    logger.info("Application startup...")
    
    # Initialize Sentry for error tracking
    init_sentry(app)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set!")
        raise ValueError("DATABASE_URL environment variable not set!")
    
    # The logging config will automatically mask the password
    logger.info(f"Connecting to database at: {database_url}")
        
    start_time = time.time()
    db.create_db_and_tables()
    duration = time.time() - start_time
    logger.info("Database tables created.")
    log_performance(logger, "database_initialization", duration)
    
    # Auto-seed from CSV if configured
    csv_seed_path = os.getenv("CSV_SEED_PATH")
    if csv_seed_path:
        await auto_seed_from_csv(csv_seed_path)
    
    # Start simple job queue if Redis is not available
    use_simple_queue = os.getenv("USE_SIMPLE_QUEUE", "true").lower() == "true"
    if use_simple_queue:
        try:
            from .simple_queue import job_queue
            job_queue.start()
            logger.info("Simple job queue started")
        except Exception as e:
            logger.warning(f"Failed to start simple job queue: {e}")
    
    # Update initial metrics
    try:
        session_gen = db.get_session()
        session = next(session_gen)
        active_sites = len(session.exec(select(models.Website).where(models.Website.is_active == True)).all())
        inactive_sites = len(session.exec(select(models.Website).where(models.Website.is_active == False)).all())
        update_websites_metrics(active_sites, inactive_sites)
        session_gen.close()
    except Exception as e:
        logger.warning(f"Failed to update initial metrics: {e}")
    
    yield
    # on shutdown
    logger.info("Application shutdown.")
    
    # Stop simple job queue
    if use_simple_queue:
        try:
            from .simple_queue import job_queue
            job_queue.stop()
            logger.info("Simple job queue stopped")
        except Exception as e:
            logger.warning(f"Failed to stop simple job queue: {e}")

app = FastAPI(
    title="HoistScraper API",
    description="Job opportunity scraping and analysis API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure middleware
# Add custom middleware (order matters - first added is outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
app.add_middleware(LoggingMiddleware)

# Add metrics middleware
@app.middleware("http")
async def track_metrics(request, call_next):
    """Track API metrics for each request."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Track metrics
    if request.url.path.startswith("/api/"):
        track_api_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration
        )
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://frontend:3000",
        "https://hoistscraper-fe.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .routers import credentials
app.include_router(credentials.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "HoistScraper API", "version": "0.1.0"}

@app.get("/health")
async def health_check(session: Session = Depends(db.get_session)):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "hoistscraper-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Check database
    db_health = HealthCheck.check_database(db.engine)
    health_status["checks"]["database"] = db_health
    if db_health["status"] != "healthy":
        health_status["status"] = "unhealthy"
    
    # Check Redis if configured
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis_url != "redis://localhost:6379":
        try:
            import redis
            redis_client = redis.from_url(redis_url)
            redis_health = HealthCheck.check_redis(redis_client)
            health_status["checks"]["redis"] = redis_health
            if redis_health["status"] != "healthy":
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unavailable",
                "message": str(e)
            }
    
    # Check Ollama if configured
    ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    if ollama_host:
        ollama_health = HealthCheck.check_ollama(ollama_host)
        health_status["checks"]["ollama"] = ollama_health
        update_ollama_status(ollama_health["status"] == "healthy")
    
    # Check worker queue
    if redis_url:
        try:
            import redis
            redis_client = redis.from_url(redis_url)
            worker_health = HealthCheck.check_worker_queue(redis_client)
            health_status["checks"]["worker_queue"] = worker_health
            update_worker_health(worker_health["status"] == "healthy")
        except Exception:
            health_status["checks"]["worker_queue"] = {
                "status": "unavailable",
                "message": "Worker queue not accessible"
            }
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()

@app.get("/docs")
async def get_docs():
    """Redirect to API documentation."""
    return {"message": "API documentation available at /docs"}

# Website API endpoints
@app.get("/api/websites", response_model=List[models.WebsiteRead])
def read_websites(session: Session = Depends(db.get_session)):
    """Get all websites."""
    start_time = time.time()
    websites = session.exec(select(models.Website)).all()
    duration = time.time() - start_time
    log_performance(logger, "api_read_websites", duration, count=len(websites))
    logger.info(f"Retrieved {len(websites)} websites")
    return websites

@app.get("/api/websites/{website_id}", response_model=models.WebsiteRead)
def read_website(website_id: int, session: Session = Depends(db.get_session)):
    """Get a specific website by ID."""
    website = session.get(models.Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@app.post("/api/websites", response_model=models.WebsiteRead)
def create_website(
    website: models.WebsiteCreate, 
    session: Session = Depends(db.get_session),
    auth_user: Optional[str] = Depends(optional_api_key)
):
    """Create a new website. Returns HTTP 409 if URL already exists."""
    start_time = time.time()
    logger.info(f"Creating new website: {website.name} ({website.url})")
    
    try:
        db_website = models.Website.model_validate(website)
        session.add(db_website)
        session.commit()
        session.refresh(db_website)
        
        duration = time.time() - start_time
        log_performance(logger, "api_create_website", duration, website_id=db_website.id)
        logger.info(f"Successfully created website ID {db_website.id}: {db_website.name}")
        
        return db_website
    except IntegrityError:
        session.rollback()
        logger.warning(f"Duplicate website creation attempt for URL: {website.url}")
        raise HTTPException(status_code=409, detail=f"Website with URL '{website.url}' already exists")

@app.put("/api/websites/{website_id}", response_model=models.WebsiteRead)
def update_website(
    website_id: int, 
    website: models.WebsiteCreate, 
    session: Session = Depends(db.get_session),
    auth_user: Optional[str] = Depends(optional_api_key)
):
    """Update an existing website."""
    db_website = session.get(models.Website, website_id)
    if not db_website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    website_data = website.model_dump(exclude_unset=True)
    for key, value in website_data.items():
        setattr(db_website, key, value)
    
    db_website.updated_at = datetime.now(timezone.utc)

    try:
        session.add(db_website)
        session.commit()
        session.refresh(db_website)
        return db_website
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Website with URL '{website.url}' already exists")

@app.delete("/api/websites/{website_id}")
def delete_website(
    website_id: int, 
    session: Session = Depends(db.get_session),
    auth_user: Optional[str] = Depends(optional_api_key)
):
    """Delete a website."""
    website = session.get(models.Website, website_id)
    if not website:
        logger.warning(f"Attempted to delete non-existent website ID: {website_id}")
        raise HTTPException(status_code=404, detail="Website not found")
    
    website_name = website.name
    website_url = website.url
    
    session.delete(website)
    session.commit()
    
    log_security_event(logger, "website_deleted",
                     website_id=website_id,
                     website_name=website_name,
                     website_url=website_url,
                     deleted_by=auth_user or "anonymous")
    
    return {"ok": True}

# ScrapeJob API endpoints
@app.get("/api/scrape-jobs", response_model=List[models.ScrapeJobRead])
def read_scrape_jobs(session: Session = Depends(db.get_session)):
    """Get all scrape jobs."""
    jobs = session.exec(select(models.ScrapeJob)).all()
    return jobs

@app.get("/api/scrape-jobs/{job_id}", response_model=models.ScrapeJobRead)
def read_scrape_job(job_id: int, session: Session = Depends(db.get_session)):
    """Get a specific scrape job by ID."""
    job = session.get(models.ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job

@app.post("/api/scrape-jobs", response_model=models.ScrapeJobRead)
def create_scrape_job(
    job: models.ScrapeJobCreate, 
    session: Session = Depends(db.get_session),
    auth_user: Optional[str] = Depends(optional_api_key)
):
    """Create a new scrape job."""
    # Verify website exists
    website = session.get(models.Website, job.website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    db_job = models.ScrapeJob.model_validate(job)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    
    # Track metrics
    track_scrape_job_metrics(db_job.website_id, "created")
    
    # Queue the job for processing
    queue_start = time.time()
    queue_success = False
    queue_method = "none"
    
    try:
        # Try simple queue first
        from .simple_queue import enqueue_job
        
        # Import appropriate worker based on configuration
        worker_type = os.getenv("WORKER_TYPE", "v2")
        if worker_type == "v2":
            try:
                from .worker_v2 import scrape_website_job_v2
                worker_func = scrape_website_job_v2
            except ImportError:
                from .worker import scrape_website_job
                worker_func = scrape_website_job
        else:
            from .worker import scrape_website_job
            worker_func = scrape_website_job
        
        enqueue_job(
            worker_func,
            website_id=db_job.website_id,
            job_id=db_job.id
        )
        queue_success = True
        queue_method = "simple_queue"
        logger.info(f"Enqueued scrape job {db_job.id} for website {db_job.website_id} using simple queue")
    except ImportError:
        # Fallback to Redis queue if available
        try:
            from .queue import enqueue_job as redis_enqueue
            from .worker import scrape_website_job
            
            redis_enqueue(
                scrape_website_job,
                website_id=db_job.website_id,
                job_id=db_job.id,
                queue_name="scraper"
            )
            queue_success = True
            queue_method = "redis_queue"
            logger.info(f"Enqueued scrape job {db_job.id} to Redis queue")
        except Exception as e:
            logger.error(f"Failed to enqueue job {db_job.id} to Redis: {str(e)}")
            # Don't fail the request, job is still created
    except Exception as e:
        logger.error(f"Failed to enqueue job {db_job.id}: {str(e)}", exc_info=True)
        # Don't fail the request, job is still created
    
    queue_duration = time.time() - queue_start
    log_performance(logger, "job_enqueue", queue_duration,
                  job_id=db_job.id,
                  queue_method=queue_method,
                  success=queue_success)
    
    return db_job

@app.put("/api/scrape-jobs/{job_id}", response_model=models.ScrapeJobRead)
def update_scrape_job(job_id: int, job: models.ScrapeJobCreate, session: Session = Depends(db.get_session)):
    """Update an existing scrape job."""
    db_job = session.get(models.ScrapeJob, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    
    job_data = job.model_dump(exclude_unset=True)
    for key, value in job_data.items():
        setattr(db_job, key, value)
    
    db_job.updated_at = datetime.now(timezone.utc)

    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job

# Opportunity API endpoints
@app.get("/api/opportunities", response_model=List[models.OpportunityRead])
def read_opportunities(session: Session = Depends(db.get_session)):
    """Get all scraped opportunities."""
    opportunities = session.exec(select(models.Opportunity)).all()
    return opportunities

@app.get("/api/opportunities/{opportunity_id}", response_model=models.OpportunityRead)
def read_opportunity(opportunity_id: int, session: Session = Depends(db.get_session)):
    """Get a specific opportunity by ID."""
    opportunity = session.get(models.Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@app.post("/api/opportunities", response_model=models.OpportunityRead)
def create_opportunity(opportunity: models.OpportunityCreate, session: Session = Depends(db.get_session)):
    """Create a new opportunity."""
    # Verify website and job exist
    website = session.get(models.Website, opportunity.website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    job = session.get(models.ScrapeJob, opportunity.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    
    db_opportunity = models.Opportunity.model_validate(opportunity)
    session.add(db_opportunity)
    session.commit()
    session.refresh(db_opportunity)
    return db_opportunity

@app.delete("/api/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: int, session: Session = Depends(db.get_session)):
    """Delete an opportunity."""
    opportunity = session.get(models.Opportunity, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    session.delete(opportunity)
    session.commit()
    return {"ok": True}

@app.post("/api/scrape/{website_id}/trigger")
def trigger_scrape_manual(
    website_id: int, 
    session: Session = Depends(db.get_session),
    auth_user: Optional[str] = Depends(optional_api_key)
):
    """Manually trigger a scrape job for testing."""
    # Verify website exists
    website = session.get(models.Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Create a new job
    db_job = models.ScrapeJob(website_id=website_id, status=models.JobStatus.PENDING)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    
    # Try to execute directly for immediate feedback
    try:
        from .worker import ScraperWorker
        worker = ScraperWorker()
        
        # Execute synchronously for testing
        result = worker.scrape_website(website_id=website_id, job_id=db_job.id)
        
        # Refresh job status
        session.refresh(db_job)
        
        return {
            "job": db_job,
            "result": {
                "title": result.get("title"),
                "url": result.get("url"),
                "status": "completed"
            }
        }
    except Exception as e:
        logger.error(f"Manual scrape failed: {str(e)}")
        # Update job status to failed
        db_job.status = models.JobStatus.FAILED
        db_job.error_message = str(e)
        session.commit()
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
    finally:
        if 'worker' in locals():
            worker.cleanup()

@app.get("/api/stats")
def get_stats(session: Session = Depends(db.get_session)):
    """Get overall statistics."""
    total_sites = len(session.exec(select(models.Website)).all())
    total_jobs = len(session.exec(select(models.ScrapeJob)).all())
    total_opportunities = len(session.exec(select(models.Opportunity)).all())
    
    # Get recent job activity (last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_jobs = session.exec(
        select(models.ScrapeJob).where(models.ScrapeJob.created_at >= seven_days_ago)
    ).all()
    
    # Get last scrape time
    last_job = session.exec(
        select(models.ScrapeJob).order_by(models.ScrapeJob.created_at.desc())
    ).first()
    
    return {
        "total_sites": total_sites,
        "total_jobs": total_jobs,
        "total_opportunities": total_opportunities,
        "jobs_this_week": len(recent_jobs),
        "last_scrape": last_job.created_at if last_job else None
    } 