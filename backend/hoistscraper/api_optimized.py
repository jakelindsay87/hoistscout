"""Optimized API endpoints with caching and performance improvements."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps
import redis
import os

from hoistscraper.db_optimized import get_session, QueryOptimizer
from hoistscraper.models_optimized import (
    Website, WebsiteCreate, WebsiteRead,
    ScrapeJob, ScrapeJobCreate, ScrapeJobRead,
    Opportunity, OpportunityRead,
    JobStatus
)
from hoistscraper.logging_config import get_logger, log_performance
import time

logger = get_logger(__name__)

# Redis configuration for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    CACHE_ENABLED = True
except Exception as e:
    logger.warning(f"Redis not available for caching: {e}")
    redis_client = None
    CACHE_ENABLED = False

# Cache decorator
def cache_response(expire_seconds: int = 300, key_prefix: str = ""):
    """Decorator to cache API responses in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_data = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(cache_data.encode()).hexdigest()
            
            # Try to get from cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Cache get error: {e}")
            
            # Get fresh data
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Cache the result
            try:
                redis_client.setex(cache_key, expire_seconds, json.dumps(result, default=str))
                logger.debug(f"Cached {cache_key} for {expire_seconds}s")
            except Exception as e:
                logger.error(f"Cache set error: {e}")
            
            log_performance(logger, f"api_{func.__name__}", duration)
            return result
        
        return wrapper
    return decorator

# Optimized routers
router = APIRouter()

# Website endpoints with caching
@router.get("/websites", response_model=List[WebsiteRead])
@cache_response(expire_seconds=60)
async def get_websites(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    region: Optional[str] = None,
    grant_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get websites with optimized query and caching."""
    query = select(Website)
    
    # Apply filters efficiently
    if active_only:
        query = query.where(Website.active == True)
    if region:
        query = query.where(Website.region == region)
    if grant_type:
        query = query.where(Website.grant_type == grant_type)
    
    # Order by created_at for consistent pagination
    query = query.order_by(Website.created_at.desc())
    
    # Apply pagination
    query = QueryOptimizer.paginate(query, page=(skip // limit) + 1, per_page=limit)
    
    websites = session.exec(query).all()
    return websites

@router.get("/websites/{website_id}", response_model=WebsiteRead)
@cache_response(expire_seconds=300)
async def get_website(website_id: int, session: Session = Depends(get_session)):
    """Get single website with caching."""
    website = session.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@router.post("/websites", response_model=WebsiteRead)
async def create_website(
    website: WebsiteCreate,
    session: Session = Depends(get_session)
):
    """Create website and invalidate cache."""
    db_website = Website.from_orm(website)
    session.add(db_website)
    session.commit()
    session.refresh(db_website)
    
    # Invalidate related caches
    if CACHE_ENABLED:
        try:
            for key in redis_client.scan_iter("*:get_websites:*"):
                redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    return db_website

# Scrape job endpoints with optimization
@router.get("/scrape-jobs", response_model=List[ScrapeJobRead])
@cache_response(expire_seconds=30)  # Short cache for job status
async def get_scrape_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[JobStatus] = None,
    website_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get scrape jobs with filters and caching."""
    query = select(ScrapeJob)
    
    if status:
        query = query.where(ScrapeJob.status == status)
    if website_id:
        query = query.where(ScrapeJob.website_id == website_id)
    
    # Order by created_at descending
    query = query.order_by(ScrapeJob.created_at.desc())
    
    # Apply pagination
    query = QueryOptimizer.paginate(query, page=(skip // limit) + 1, per_page=limit)
    
    jobs = session.exec(query).all()
    return jobs

@router.get("/scrape-jobs/stats")
@cache_response(expire_seconds=60)
async def get_job_stats(session: Session = Depends(get_session)):
    """Get job statistics with caching."""
    # Use aggregation for efficiency
    stats_query = select(
        ScrapeJob.status,
        func.count(ScrapeJob.id).label('count')
    ).group_by(ScrapeJob.status)
    
    results = session.exec(stats_query).all()
    
    stats = {
        "total": 0,
        "by_status": {}
    }
    
    for status, count in results:
        stats["by_status"][status] = count
        stats["total"] += count
    
    # Add processing metrics
    recent_completed = session.exec(
        select(ScrapeJob)
        .where(ScrapeJob.status == JobStatus.COMPLETED)
        .where(ScrapeJob.completed_at > datetime.now() - timedelta(hours=1))
    ).all()
    
    if recent_completed:
        processing_times = []
        for job in recent_completed:
            if job.started_at and job.completed_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                processing_times.append(duration)
        
        if processing_times:
            stats["avg_processing_time"] = sum(processing_times) / len(processing_times)
            stats["jobs_per_hour"] = len(recent_completed)
    
    return stats

# Opportunity endpoints with advanced filtering
@router.get("/opportunities", response_model=List[OpportunityRead])
@cache_response(expire_seconds=300)
async def get_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    website_id: Optional[int] = None,
    search: Optional[str] = None,
    deadline_after: Optional[datetime] = None,
    session: Session = Depends(get_session)
):
    """Get opportunities with advanced filtering and caching."""
    query = select(Opportunity)
    
    if website_id:
        query = query.where(Opportunity.website_id == website_id)
    
    if search:
        # Use ILIKE for case-insensitive search (PostgreSQL)
        search_pattern = f"%{search}%"
        query = query.where(
            (Opportunity.title.ilike(search_pattern)) |
            (Opportunity.description.ilike(search_pattern))
        )
    
    if deadline_after:
        query = query.where(Opportunity.deadline > deadline_after)
    
    # Order by created_at descending
    query = query.order_by(Opportunity.created_at.desc())
    
    # Apply pagination
    query = QueryOptimizer.paginate(query, page=(skip // limit) + 1, per_page=limit)
    
    opportunities = session.exec(query).all()
    return opportunities

@router.get("/opportunities/export")
async def export_opportunities(
    format: str = Query("json", regex="^(json|csv)$"),
    website_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Export opportunities in different formats."""
    query = select(Opportunity)
    
    if website_id:
        query = query.where(Opportunity.website_id == website_id)
    
    opportunities = session.exec(query).all()
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'title', 'description', 'funding_amount', 
            'deadline', 'eligibility', 'application_url', 'source_url'
        ])
        writer.writeheader()
        
        for opp in opportunities:
            writer.writerow({
                'id': opp.id,
                'title': opp.title,
                'description': opp.description,
                'funding_amount': opp.funding_amount,
                'deadline': opp.deadline,
                'eligibility': opp.eligibility,
                'application_url': opp.application_url,
                'source_url': opp.source_url
            })
        
        return {
            "content": output.getvalue(),
            "filename": f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    
    else:  # JSON
        return {
            "opportunities": [opp.dict() for opp in opportunities],
            "count": len(opportunities),
            "exported_at": datetime.now().isoformat()
        }

# Health check with detailed metrics
@router.get("/health")
async def health_check(session: Session = Depends(get_session)):
    """Health check with performance metrics."""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        session.exec(select(func.count(Website.id))).one()
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Redis check
    if CACHE_ENABLED:
        try:
            redis_client.ping()
            health["checks"]["cache"] = "ok"
        except Exception as e:
            health["checks"]["cache"] = f"error: {str(e)}"
    else:
        health["checks"]["cache"] = "disabled"
    
    # Add performance metrics
    if CACHE_ENABLED:
        try:
            info = redis_client.info()
            health["metrics"] = {
                "cache_hits": info.get("keyspace_hits", 0),
                "cache_misses": info.get("keyspace_misses", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception:
            pass
    
    return health