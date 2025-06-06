"""FastAPI application entry point."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
from . import models, db

app = FastAPI(
    title="HoistScraper API",
    description="Job opportunity scraping and analysis API",
    version="0.1.0"
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

@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()

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
    db_site = models.Site.from_orm(site)
    session.add(db_site)
    session.commit()
    session.refresh(db_site)
    return db_site

@app.put("/api/sites/{site_id}", response_model=models.SiteRead)
def update_site(site_id: int, site: models.SiteCreate, session: Session = Depends(db.get_session)):
    db_site = session.get(models.Site, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_data = site.dict(exclude_unset=True)
    for key, value in site_data.items():
        setattr(db_site, key, value)
    
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