from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx

from ..database import get_db
from ..config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "HoistScout API"}


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
    
    # Check MinIO
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{settings.minio_endpoint}/minio/health/ready")
            checks["minio"] = response.status_code == 200
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    return {
        "ready": all_healthy,
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check():
    return {"alive": True}