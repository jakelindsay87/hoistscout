#!/usr/bin/env python3
"""
Comprehensive deployment validation script for HoistScout backend.
Run this before deployment to catch all potential issues.
"""

import sys
import os
import asyncio
from typing import List, Tuple, Optional

# Set up environment
os.environ.setdefault("PYTHONPATH", "/app")

def check_imports() -> List[str]:
    """Test all critical imports."""
    errors = []
    
    # Core framework imports
    try:
        import fastapi
        print("✓ FastAPI import successful")
    except ImportError as e:
        errors.append(f"FastAPI import failed: {e}")
    
    try:
        import uvicorn
        print("✓ Uvicorn import successful")
    except ImportError as e:
        errors.append(f"Uvicorn import failed: {e}")
    
    # Database imports
    try:
        import sqlalchemy
        from sqlalchemy.ext.asyncio import create_async_engine
        print("✓ SQLAlchemy async import successful")
    except ImportError as e:
        errors.append(f"SQLAlchemy import failed: {e}")
    
    try:
        import asyncpg
        print("✓ AsyncPG import successful")
    except ImportError as e:
        errors.append(f"AsyncPG import failed: {e}")
    
    # Redis and Celery
    try:
        import redis
        print("✓ Redis import successful")
    except ImportError as e:
        errors.append(f"Redis import failed: {e}")
    
    try:
        import celery
        print("✓ Celery import successful")
    except ImportError as e:
        errors.append(f"Celery import failed: {e}")
    
    # Scraping dependencies
    try:
        import httpx
        print("✓ HTTPX import successful")
    except ImportError as e:
        errors.append(f"HTTPX import failed: {e}")
    
    try:
        import bs4
        print("✓ BeautifulSoup import successful")
    except ImportError as e:
        errors.append(f"BeautifulSoup import failed: {e}")
    
    try:
        import playwright
        print("✓ Playwright import successful")
    except ImportError as e:
        errors.append(f"Playwright import failed: {e}")
    
    # Optional but important
    try:
        from scrapegraph_ai import SmartScraperGraph
        print("✓ ScrapeGraph-AI import successful")
    except ImportError as e:
        print("⚠ ScrapeGraph-AI import failed (optional): {e}")
    
    # MinIO (optional)
    try:
        import minio
        print("✓ MinIO import successful")
    except ImportError as e:
        print("⚠ MinIO import failed (optional): {e}")
    
    # PDF processing
    try:
        import pypdf2
        print("✓ PyPDF2 import successful")
    except ImportError as e:
        print("⚠ PyPDF2 import failed (optional): {e}")
    
    return errors


def check_app_imports() -> List[str]:
    """Test app-specific imports."""
    errors = []
    
    try:
        from app.config import get_settings
        settings = get_settings()
        print(f"✓ Settings loaded successfully")
        print(f"  - Environment: {settings.environment}")
        print(f"  - Database URL: {settings.database_url[:20]}...")
    except Exception as e:
        errors.append(f"Settings import failed: {e}")
        return errors
    
    try:
        from app.main import app
        print("✓ FastAPI app import successful")
    except Exception as e:
        errors.append(f"FastAPI app import failed: {e}")
    
    try:
        from app.database import engine, AsyncSessionLocal
        print("✓ Database module import successful")
    except Exception as e:
        errors.append(f"Database import failed: {e}")
    
    try:
        from app.worker import celery_app, worker
        print("✓ Worker module import successful")
        print(f"  - Celery app configured: {bool(celery_app)}")
        print(f"  - Worker alias available: {bool(worker)}")
    except Exception as e:
        errors.append(f"Worker import failed: {e}")
    
    # Test core modules
    try:
        from app.core.scraper import BulletproofTenderScraper
        print("✓ Core scraper import successful")
    except Exception as e:
        print(f"⚠ Core scraper import failed (will use fallback): {e}")
    
    return errors


async def check_database_connection() -> Optional[str]:
    """Test database connectivity."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return None
    except Exception as e:
        return f"Database connection failed: {e}"


def check_redis_connection() -> Optional[str]:
    """Test Redis connectivity."""
    try:
        from app.config import get_settings
        import redis
        
        settings = get_settings()
        if not settings.redis_url:
            return "Redis URL not configured"
        
        # Parse Redis URL
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("✓ Redis connection successful")
        return None
    except Exception as e:
        return f"Redis connection failed: {e}"


def check_environment_variables() -> List[str]:
    """Check critical environment variables."""
    errors = []
    warnings = []
    
    # Critical variables
    if not os.environ.get('DATABASE_URL'):
        errors.append("DATABASE_URL not set")
    else:
        print("✓ DATABASE_URL configured")
    
    if not os.environ.get('REDIS_URL'):
        errors.append("REDIS_URL not set")
    else:
        print("✓ REDIS_URL configured")
    
    # Important but can use defaults
    if not os.environ.get('SECRET_KEY'):
        warnings.append("SECRET_KEY not set (will use default - INSECURE)")
    else:
        print("✓ SECRET_KEY configured")
    
    # Optional services
    if not os.environ.get('MINIO_ENDPOINT'):
        print("⚠ MinIO not configured (optional)")
    
    if not os.environ.get('OLLAMA_BASE_URL'):
        print("⚠ Ollama not configured (optional)")
    
    return errors


def check_worker_command() -> Optional[str]:
    """Test if worker can be started."""
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-c", "from app.worker import worker; print('Worker ready')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Worker command test successful")
            return None
        else:
            return f"Worker command failed: {result.stderr}"
    except Exception as e:
        return f"Worker command test failed: {e}"


async def main():
    """Run all deployment checks."""
    print("=" * 60)
    print("HoistScout Deployment Validation")
    print("=" * 60)
    
    all_errors = []
    
    # Check imports
    print("\n1. Checking Python package imports...")
    import_errors = check_imports()
    all_errors.extend(import_errors)
    
    print("\n2. Checking app-specific imports...")
    app_errors = check_app_imports()
    all_errors.extend(app_errors)
    
    # Check environment
    print("\n3. Checking environment variables...")
    env_errors = check_environment_variables()
    all_errors.extend(env_errors)
    
    # Check connections (only if imports succeeded)
    if not import_errors and not app_errors:
        print("\n4. Checking database connection...")
        db_error = await check_database_connection()
        if db_error:
            all_errors.append(db_error)
        
        print("\n5. Checking Redis connection...")
        redis_error = check_redis_connection()
        if redis_error:
            all_errors.append(redis_error)
        
        print("\n6. Checking worker command...")
        worker_error = check_worker_command()
        if worker_error:
            all_errors.append(worker_error)
    else:
        print("\n⚠ Skipping connection tests due to import errors")
    
    # Summary
    print("\n" + "=" * 60)
    print("DEPLOYMENT VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_errors:
        print(f"\n❌ VALIDATION FAILED - {len(all_errors)} critical errors found:\n")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}")
        print("\n⚠️  FIX THESE ISSUES BEFORE DEPLOYMENT!")
        sys.exit(1)
    else:
        print("\n✅ ALL CHECKS PASSED - Ready for deployment!")
        print("\nOptional services not configured:")
        print("- MinIO (file storage)")
        print("- Ollama (AI scraping)")
        print("- ScrapeGraph-AI (AI scraping)")
        print("\nThese can be configured later if needed.")
        sys.exit(0)


if __name__ == "__main__":
    # For async main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)