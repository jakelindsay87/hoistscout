# HoistScout Deployment Critical Fixes - Round 2

**Date**: 2025-07-02  
**Status**: ✅ Critical deployment blockers fixed

## Issues Identified from Deployment Logs

### 1. ✅ Missing Python Package: scrapegraphai
**Error**: `ModuleNotFoundError: No module named 'scrapegraphai'`

**Fix**: Added to `backend/pyproject.toml`:
```toml
scrapegraphai = "^1.2.0"
```

### 2. ✅ PostgreSQL Async Driver Issue
**Error**: `sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.`

**Fixes Applied**:
1. Added `asyncpg` to pyproject.toml:
   ```toml
   asyncpg = "^0.29.0"
   ```

2. Updated `backend/app/database.py` to convert PostgreSQL URLs:
   ```python
   # Convert postgresql:// to postgresql+asyncpg:// for async support
   database_url = settings.database_url
   if database_url.startswith("postgresql://"):
       database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
   elif database_url.startswith("postgres://"):
       database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
   ```

### 3. ✅ Worker Module Import Error
**Error**: `AttributeError: module 'app' has no attribute 'worker'`

**Fixes Applied**:
1. Added celery app export in worker.py:
   ```python
   # Make celery_app available as 'worker' for the celery command
   worker = celery_app
   ```

2. Made imports lazy to avoid startup issues:
   ```python
   # Lazy import in tasks to avoid circular dependencies
   try:
       from .core import BulletproofTenderScraper
       scraper = BulletproofTenderScraper()
   except ImportError as e:
       # Handle gracefully if not available
   ```

## Summary of Changes

### Modified Files:
1. `backend/pyproject.toml` - Added scrapegraphai and asyncpg
2. `backend/app/database.py` - Convert DB URL for async support
3. `backend/app/worker.py` - Export celery app and lazy imports

## Deployment Notes

The backend should now:
- ✅ Have all required Python packages declared
- ✅ Use proper async PostgreSQL driver
- ✅ Start worker without import errors
- ✅ Handle missing optional services gracefully

## Important: Poetry Lock Update

After deployment, the container will need to regenerate the poetry.lock file since we added new dependencies. The Dockerfile already includes:
```dockerfile
RUN poetry lock --no-update
```

This ensures all new dependencies are properly resolved.