from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from .config import get_settings
from .database import init_db, close_db
from .api import auth, websites, opportunities, jobs, health

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HoistScout API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down HoistScout API...")
    await close_db()


app = FastAPI(
    title="HoistScout API",
    description="Enterprise tender and grant scraping platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
if settings.environment == "production":
    Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(websites.router, prefix="/api/websites", tags=["websites"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(jobs.router, prefix="/api/scraping/jobs", tags=["jobs"])


@app.get("/")
async def root():
    return {"message": "HoistScout API", "version": "0.1.0"}