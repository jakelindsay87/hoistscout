"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Placeholder endpoints for the QA suite
@app.get("/api/sites")
async def get_sites():
    """Get configured sites."""
    return []

@app.post("/api/sites")
async def create_site(site_data: dict):
    """Create a new site configuration."""
    return {"id": 1, "url": site_data.get("url"), "status": "created"}

@app.get("/api/opportunities")
async def get_opportunities():
    """Get scraped opportunities."""
    return [] 