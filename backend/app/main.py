from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from .config import get_settings
from .database import init_db, close_db
from .api import auth, websites, opportunities, jobs, health
from .utils.demo_user import ensure_demo_user

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HoistScout API...")
    await init_db()
    
    # Create demo user if enabled
    if settings.demo_user_enabled:
        try:
            from .database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await ensure_demo_user(db)
        except Exception as e:
            logger.warning(f"Failed to create demo user: {e}. Continuing without demo user.")
    
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
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://hoistscout-frontend.onrender.com"  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to handle trailing slash redirects with auth headers preserved
@app.middleware("http")
async def preserve_auth_on_redirect(request: Request, call_next):
    # Skip middleware for paths that already have trailing slash or are not API paths
    if request.url.path.endswith("/") or not request.url.path.startswith("/api/"):
        response = await call_next(request)
        return response
    
    # For API paths without trailing slash, check if adding a slash would match a route
    path_with_slash = request.url.path + "/"
    
    # List of known API paths that should have trailing slashes
    api_paths_with_slash = [
        "/api/websites/",
        "/api/opportunities/", 
        "/api/scraping/jobs/"
    ]
    
    if path_with_slash in api_paths_with_slash:
        # Instead of redirecting, just add the slash and continue
        request.scope["path"] = path_with_slash
    
    response = await call_next(request)
    return response


# Prometheus metrics
if settings.environment == "production":
    Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(websites.router, prefix="/api/websites", tags=["websites"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(jobs.router, prefix="/api/scraping/jobs", tags=["jobs"])


@app.get("/")
async def root():
    return {"message": "HoistScout API", "version": "0.1.0"}