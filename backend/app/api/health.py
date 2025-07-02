from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
import httpx
import sys
import os
from datetime import datetime, timedelta

from ..database import get_db
from ..config import get_settings
from ..models.website import Website
from ..models.job import ScrapingJob
from ..models.opportunity import Opportunity

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy", 
        "service": "HoistScout API",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "python_version": sys.version
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    checks = {
        "database": False,
        "redis": False,
        "minio": False
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    
    # Check Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        checks["redis"] = True
    except Exception:
        pass
    
    # Check MinIO (only if configured)
    if settings.minio_endpoint:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{settings.minio_endpoint}/minio/health/ready")
                checks["minio"] = response.status_code == 200
        except Exception:
            pass
    else:
        checks["minio"] = None  # Not configured
    
    # Only check services that are configured (not None)
    configured_checks = {k: v for k, v in checks.items() if v is not None}
    all_healthy = all(configured_checks.values()) if configured_checks else True
    return {
        "ready": all_healthy,
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check():
    return {"alive": True}


@router.get("/health/diagnostic")
async def diagnostic_check():
    """Comprehensive diagnostic endpoint for deployment debugging."""
    diagnostics = {
        "service": "HoistScout API",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "python_version": sys.version,
        "imports": {},
        "environment_vars": {},
        "optional_services": {}
    }
    
    # Check critical imports
    import_checks = [
        ("fastapi", "FastAPI framework"),
        ("sqlalchemy", "Database ORM"),
        ("asyncpg", "PostgreSQL async driver"),
        ("redis", "Redis client"),
        ("celery", "Task queue"),
        ("httpx", "HTTP client"),
        ("bs4", "BeautifulSoup"),
        ("playwright", "Browser automation"),
    ]
    
    for module_name, description in import_checks:
        try:
            __import__(module_name)
            diagnostics["imports"][module_name] = {"status": "ok", "description": description}
        except ImportError as e:
            diagnostics["imports"][module_name] = {"status": "error", "description": description, "error": str(e)}
    
    # Check optional imports
    optional_imports = [
        ("scrapegraph_ai", "AI scraping"),
        ("minio", "Object storage"),
        ("pypdf2", "PDF processing"),
    ]
    
    for module_name, description in optional_imports:
        try:
            __import__(module_name)
            diagnostics["optional_services"][module_name] = {"status": "available", "description": description}
        except ImportError:
            diagnostics["optional_services"][module_name] = {"status": "not_available", "description": description}
    
    # Check environment variables (sanitized)
    env_vars = [
        ("DATABASE_URL", "Database connection"),
        ("REDIS_URL", "Redis connection"),
        ("SECRET_KEY", "Security key"),
        ("MINIO_ENDPOINT", "MinIO endpoint"),
        ("OLLAMA_BASE_URL", "Ollama AI service"),
    ]
    
    for var_name, description in env_vars:
        value = os.environ.get(var_name)
        if value:
            # Sanitize sensitive values
            if var_name in ["DATABASE_URL", "REDIS_URL"]:
                sanitized = value[:20] + "..." if len(value) > 20 else value
            elif var_name == "SECRET_KEY":
                sanitized = "***configured***"
            else:
                sanitized = value
            diagnostics["environment_vars"][var_name] = {"status": "set", "value": sanitized, "description": description}
        else:
            diagnostics["environment_vars"][var_name] = {"status": "not_set", "description": description}
    
    # Check app imports
    try:
        from ..core.scraper import SCRAPEGRAPH_AVAILABLE
        diagnostics["optional_services"]["scrapegraph_integration"] = {
            "status": "available" if SCRAPEGRAPH_AVAILABLE else "disabled",
            "description": "AI scraping integration"
        }
    except Exception as e:
        diagnostics["optional_services"]["scrapegraph_integration"] = {
            "status": "error",
            "description": "AI scraping integration",
            "error": str(e)
        }
    
    return diagnostics


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics for the frontend."""
    try:
        # Get total sites count
        sites_stmt = select(func.count(Website.id))
        sites_result = await db.execute(sites_stmt)
        total_sites = sites_result.scalar() or 0
        
        # Get total jobs count
        jobs_stmt = select(func.count(ScrapingJob.id))
        jobs_result = await db.execute(jobs_stmt)
        total_jobs = jobs_result.scalar() or 0
        
        # Get total opportunities count
        opps_stmt = select(func.count(Opportunity.id))
        opps_result = await db.execute(opps_stmt)
        total_opportunities = opps_result.scalar() or 0
        
        # Get jobs created this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_jobs_stmt = select(func.count(ScrapingJob.id)).where(
            ScrapingJob.created_at >= week_ago
        )
        week_jobs_result = await db.execute(week_jobs_stmt)
        jobs_this_week = week_jobs_result.scalar() or 0
        
        # Get last scrape time (most recent completed job)
        last_scrape_stmt = select(ScrapingJob.completed_at).where(
            ScrapingJob.completed_at.isnot(None)
        ).order_by(ScrapingJob.completed_at.desc()).limit(1)
        last_scrape_result = await db.execute(last_scrape_stmt)
        last_scrape_time = last_scrape_result.scalar()
        
        return {
            "total_sites": total_sites,
            "total_jobs": total_jobs,
            "total_opportunities": total_opportunities,
            "jobs_this_week": jobs_this_week,
            "last_scrape": last_scrape_time.isoformat() if last_scrape_time else None
        }
    except Exception as e:
        # Return zeros if there's an error to prevent frontend from breaking
        return {
            "total_sites": 0,
            "total_jobs": 0,
            "total_opportunities": 0,
            "jobs_this_week": 0,
            "last_scrape": None
        }