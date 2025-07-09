from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
import httpx
import sys
import os
from datetime import datetime, timedelta
import json
import traceback
try:
    import redis.asyncio as redis
except ImportError:
    import redis

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
        try:
    import redis.asyncio as redis
except ImportError:
    import redis
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


@router.get("/health/redis")
async def redis_connectivity_check():
    """
    Comprehensive Redis connectivity and Celery queue check.
    This endpoint is accessible without authentication for easy testing.
    """
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "redis_url": settings.redis_url[:30] + "..." if len(settings.redis_url) > 30 else settings.redis_url,
        "connection": {
            "status": "disconnected",
            "error": None,
            "latency_ms": None
        },
        "operations": {
            "set": {"success": False, "error": None},
            "get": {"success": False, "value": None, "error": None},
            "delete": {"success": False, "error": None}
        },
        "celery": {
            "queues": {},
            "total_tasks": 0,
            "unacked_tasks": 0,
            "error": None
        },
        "redis_info": {}
    }
    
    r = None
    try:
        # Test Redis connection
        start_time = datetime.utcnow()
        r = redis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result["connection"]["status"] = "connected"
        result["connection"]["latency_ms"] = round(latency, 2)
        
        # Test basic operations
        test_key = f"hoistscout:health:test:{datetime.utcnow().timestamp()}"
        test_value = f"test_value_{datetime.utcnow().isoformat()}"
        
        # SET operation
        try:
            await r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            result["operations"]["set"]["success"] = True
        except Exception as e:
            result["operations"]["set"]["error"] = str(e)
        
        # GET operation
        try:
            retrieved_value = await r.get(test_key)
            result["operations"]["get"]["success"] = True
            result["operations"]["get"]["value"] = retrieved_value
            if retrieved_value != test_value:
                result["operations"]["get"]["error"] = "Value mismatch"
        except Exception as e:
            result["operations"]["get"]["error"] = str(e)
        
        # DELETE operation
        try:
            await r.delete(test_key)
            result["operations"]["delete"]["success"] = True
        except Exception as e:
            result["operations"]["delete"]["error"] = str(e)
        
        # Check Celery queues
        try:
            # Get all keys
            all_keys = await r.keys("*")
            
            # Check specific Celery queues
            celery_queues = ["celery", "celery.priority.high", "celery.priority.low"]
            
            for queue_name in celery_queues:
                if queue_name in all_keys:
                    queue_length = await r.llen(queue_name)
                    result["celery"]["queues"][queue_name] = {
                        "length": queue_length,
                        "tasks": []
                    }
                    
                    # Get first few tasks for inspection
                    if queue_length > 0:
                        for i in range(min(3, queue_length)):
                            try:
                                task_data = await r.lindex(queue_name, i)
                                if task_data:
                                    task = json.loads(task_data)
                                    task_info = {
                                        "id": task.get("headers", {}).get("id", "unknown"),
                                        "name": task.get("headers", {}).get("task", "unknown"),
                                        "args": task.get("body", {}).get("args", [])
                                    }
                                    result["celery"]["queues"][queue_name]["tasks"].append(task_info)
                            except Exception as e:
                                result["celery"]["queues"][queue_name]["tasks"].append({
                                    "error": f"Failed to parse task: {str(e)}"
                                })
                    
                    result["celery"]["total_tasks"] += queue_length
            
            # Check for unacknowledged tasks
            unacked_key = "unacked"
            if unacked_key in all_keys:
                unacked_count = await r.hlen(unacked_key)
                result["celery"]["unacked_tasks"] = unacked_count
            
            # Check for Celery-related keys
            celery_related_keys = [k for k in all_keys if "celery" in k.lower()]
            result["celery"]["related_keys"] = celery_related_keys[:10]  # Limit to first 10
            
        except Exception as e:
            result["celery"]["error"] = f"Failed to check Celery queues: {str(e)}"
        
        # Get Redis server info (limited subset)
        try:
            info = await r.info()
            result["redis_info"] = {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "uptime_in_days": info.get("uptime_in_days", 0),
                "role": info.get("role", "unknown")
            }
        except Exception as e:
            result["redis_info"]["error"] = f"Failed to get Redis info: {str(e)}"
        
    except Exception as e:
        result["connection"]["status"] = "failed"
        result["connection"]["error"] = str(e)
        result["connection"]["traceback"] = traceback.format_exc()
    
    finally:
        # Clean up connection
        if r:
            try:
                await r.close()
            except:
                pass
    
    # Determine overall health
    result["healthy"] = (
        result["connection"]["status"] == "connected" and
        all(op["success"] for op in result["operations"].values())
    )
    
    return result