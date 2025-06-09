"""FastAPI application entry point."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
from . import models, db, ingest
from datetime import datetime, UTC
import logging
import os
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup
    logger.info("Application startup...")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set!")
        raise ValueError("DATABASE_URL environment variable not set!")
    
    logger.info(f"DATABASE_URL: {database_url}")
    
    # Mask password for logging
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(database_url)
    if parsed_url.password:
        safe_url = parsed_url._replace(netloc=f"{parsed_url.username}:***@{parsed_url.hostname}")
        logger.info(f"Connecting to database at: {urlunparse(safe_url)}")
    else:
        logger.info(f"Connecting to database at: {database_url}")
        
    db.create_db_and_tables()
    logger.info("Database tables created.")
    yield
    # on shutdown
    logger.info("Application shutdown.")

app = FastAPI(
    title="HoistScraper API",
    description="Job opportunity scraping and analysis API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://frontend:3000",
        "https://hoistscraper-fe.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "HoistScraper API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks."""
    return {"status": "healthy", "service": "hoistscraper-api"}

@app.get("/docs")
async def get_docs():
    """Redirect to API documentation."""
    return {"message": "API documentation available at /docs"}

@app.get("/api/sites", response_model=List[models.SiteRead])
def read_sites(session: Session = Depends(db.get_session)):
    sites = session.exec(select(models.Site)).all()
    return sites

@app.get("/api/sites/{site_id}", response_model=models.SiteRead)
def read_site(site_id: int, session: Session = Depends(db.get_session)):
    site = session.get(models.Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@app.post("/api/sites", response_model=models.SiteRead)
def create_site(site: models.SiteCreate, session: Session = Depends(db.get_session)):
    db_site = models.Site.model_validate(site)
    session.add(db_site)
    session.commit()
    session.refresh(db_site)
    return db_site

@app.put("/api/sites/{site_id}", response_model=models.SiteRead)
def update_site(site_id: int, site: models.SiteCreate, session: Session = Depends(db.get_session)):
    db_site = session.get(models.Site, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_data = site.model_dump(exclude_unset=True)
    for key, value in site_data.items():
        setattr(db_site, key, value)
    
    db_site.updated_at = datetime.now(UTC)

    session.add(db_site)
    session.commit()
    session.refresh(db_site)
    return db_site

@app.delete("/api/sites/{site_id}")
def delete_site(site_id: int, session: Session = Depends(db.get_session)):
    site = session.get(models.Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    session.delete(site)
    session.commit()
    return {"ok": True}

# Website API endpoints (new models)
@app.get("/api/websites", response_model=List[models.WebsiteRead])
def read_websites(session: Session = Depends(db.get_session)):
    """Get all websites."""
    websites = session.exec(select(models.Website)).all()
    return websites

@app.get("/api/websites/{website_id}", response_model=models.WebsiteRead)
def read_website(website_id: int, session: Session = Depends(db.get_session)):
    """Get a specific website by ID."""
    website = session.get(models.Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@app.post("/api/websites", response_model=models.WebsiteRead)
def create_website(website: models.WebsiteCreate, session: Session = Depends(db.get_session)):
    """Create a new website. Returns HTTP 409 if URL already exists."""
    try:
        db_website = models.Website.model_validate(website)
        session.add(db_website)
        session.commit()
        session.refresh(db_website)
        return db_website
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Website with URL '{website.url}' already exists")

@app.put("/api/websites/{website_id}", response_model=models.WebsiteRead)
def update_website(website_id: int, website: models.WebsiteCreate, session: Session = Depends(db.get_session)):
    """Update an existing website."""
    db_website = session.get(models.Website, website_id)
    if not db_website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    website_data = website.model_dump(exclude_unset=True)
    for key, value in website_data.items():
        setattr(db_website, key, value)
    
    db_website.updated_at = datetime.now(UTC)

    try:
        session.add(db_website)
        session.commit()
        session.refresh(db_website)
        return db_website
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=f"Website with URL '{website.url}' already exists")

@app.delete("/api/websites/{website_id}")
def delete_website(website_id: int, session: Session = Depends(db.get_session)):
    """Delete a website."""
    website = session.get(models.Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    session.delete(website)
    session.commit()
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
def create_scrape_job(job: models.ScrapeJobCreate, session: Session = Depends(db.get_session)):
    """Create a new scrape job."""
    # Verify website exists
    website = session.get(models.Website, job.website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    db_job = models.ScrapeJob.model_validate(job)
    session.add(db_job)
    session.commit()
    session.refresh(db_job)
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
    
    db_job.updated_at = datetime.now(UTC)

    session.add(db_job)
    session.commit()
    session.refresh(db_job)
    return db_job

@app.get("/api/opportunities")
async def get_opportunities():
    """Get scraped opportunities."""
    return [] 