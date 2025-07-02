"""FastAPI application entry point with error handling."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
import logging
import os
from contextlib import asynccontextmanager
import sys

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler with comprehensive error handling."""
    # on startup
    logger.info("Application startup...")
    
    # Check for required environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, using SQLite fallback")
        database_url = "sqlite:///./hoistscout.db"
        os.environ["DATABASE_URL"] = database_url
    
    # Initialize database with error handling
    try:
        from . import db
        logger.info("Initializing database...")
        db.create_db_and_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway - some endpoints might still work
    
    # Initialize monitoring if available
    try:
        from .monitoring import init_sentry
        init_sentry(app)
        logger.info("Sentry monitoring initialized")
    except Exception as e:
        logger.warning(f"Monitoring initialization skipped: {e}")
    
    yield
    # on shutdown
    logger.info("Application shutdown.")

# Create FastAPI app
app = FastAPI(
    title="HoistScraper API",
    description="Job opportunity scraping and analysis API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware with error handling
try:
    from .middleware import LoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(LoggingMiddleware)
    logger.info("Custom middleware added")
except Exception as e:
    logger.warning(f"Custom middleware skipped: {e}")

# Basic routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "HoistScraper API", "version": "0.1.0", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "environment": {
            "database_url": bool(os.getenv("DATABASE_URL")),
            "redis_url": bool(os.getenv("REDIS_URL")),
            "credential_passphrase": bool(os.getenv("CREDENTIAL_PASSPHRASE")),
            "render": bool(os.getenv("RENDER")),
        }
    }
    
    # Test database connection
    try:
        from . import db
        session = next(db.get_session())
        session.exec(select(1))
        health_status["database"] = "connected"
        session.close()
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    return health_status

# Include routers with error handling
try:
    from .routers import credentials, admin, debug
    app.include_router(credentials.router)
    app.include_router(admin.router)
    
    # Debug router only in development
    if os.getenv("RENDER") != "true":
        app.include_router(debug.router)
    
    logger.info("Routers included successfully")
except Exception as e:
    logger.error(f"Failed to include routers: {e}")
    
    # Add a simple error endpoint
    @app.get("/api/error")
    async def get_error():
        return {"error": f"Router initialization failed: {str(e)}"}

# API endpoints with error handling
@app.get("/api/websites")
async def list_websites(skip: int = 0, limit: int = 100):
    """List all websites with error handling."""
    try:
        from . import db, models
        session = next(db.get_session())
        websites = session.exec(
            select(models.Website)
            .offset(skip)
            .limit(limit)
        ).all()
        session.close()
        return websites
    except Exception as e:
        logger.error(f"Failed to list websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/websites")
async def create_website(url: str, name: Optional[str] = None):
    """Create a website with error handling."""
    try:
        from . import db, models
        session = next(db.get_session())
        website = models.Website(url=url, name=name or url)
        session.add(website)
        session.commit()
        session.refresh(website)
        session.close()
        return website
    except Exception as e:
        logger.error(f"Failed to create website: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)