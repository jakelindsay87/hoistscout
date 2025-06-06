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

@app.get("/api/opportunities")
async def get_opportunities():
    """Get scraped opportunities."""
    return [] 