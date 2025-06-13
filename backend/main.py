"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .db import init_db
from .routers import sites

# Create FastAPI app
app = FastAPI(
    title="HoistScraper API",
    version="0.1.0",
    description="Web scraping API for funding opportunities"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Include routers
app.include_router(sites.router)