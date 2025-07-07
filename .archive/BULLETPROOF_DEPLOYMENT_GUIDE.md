# Bulletproof Deployment Guide for HoistScout

This guide ensures zero-failure deployments by catching all issues before they happen.

## Pre-Deployment Checklist

### 1. Run Local Validation

```bash
# From backend directory
cd backend
python app/deployment_check.py
```

This script checks:
- ✅ All Python package imports
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Environment variables
- ✅ Worker module exports

**DO NOT DEPLOY if any checks fail!**

### 2. Critical Package Names

⚠️ **IMPORTANT**: The correct package names are:
- `scrapegraph-ai` (NOT `scrapegraphai`)
- `asyncpg` (for PostgreSQL async support)
- `redis` with `[asyncio]` extras

### 3. Environment Variables

#### Required for Deployment:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
PYTHONUNBUFFERED=1
PYTHONPATH=/app
```

#### Optional Services (can be added later):
```bash
MINIO_ENDPOINT=minio.example.com:9000
MINIO_ACCESS_KEY=minioaccess
MINIO_SECRET_KEY=miniosecret
OLLAMA_BASE_URL=http://ollama:11434
FLARESOLVERR_URL=http://flaresolverr:8191
```

### 4. Dockerfile Requirements

The Dockerfile MUST include:
```dockerfile
# Install Playwright browsers (for scrapegraph-ai)
RUN poetry run playwright install-deps chromium
RUN poetry run playwright install chromium
```

### 5. Database URL Conversion

The backend automatically converts PostgreSQL URLs for async support:
- `postgresql://` → `postgresql+asyncpg://`
- `postgres://` → `postgresql+asyncpg://`

## Common Deployment Failures and Fixes

### Issue 1: ModuleNotFoundError
**Error**: `ModuleNotFoundError: No module named 'scrapegraphai'`
**Fix**: Update pyproject.toml to use `scrapegraph-ai = "^1.60.0"`

### Issue 2: PostgreSQL Async Driver
**Error**: `The asyncio extension requires an async driver`
**Fix**: Ensure `asyncpg = "^0.29.0"` is in pyproject.toml

### Issue 3: Worker Import Error
**Error**: `module 'app' has no attribute 'worker'`
**Fix**: Worker.py must export: `worker = celery_app`

### Issue 4: Missing Dependencies
**Error**: Various import errors
**Fix**: Run `poetry lock --no-update` in Dockerfile

### Issue 5: Pydantic Validation Errors
**Error**: `ValidationError` for MinIO/Ollama settings
**Fix**: Make these settings Optional[str] in config.py

## Deployment Verification

### 1. Health Check Endpoints

After deployment, verify these endpoints:

```bash
# Basic health
curl https://your-api.onrender.com/api/health

# Readiness check (DB, Redis, etc.)
curl https://your-api.onrender.com/api/health/ready

# Comprehensive diagnostics
curl https://your-api.onrender.com/api/health/diagnostic
```

### 2. Expected Health Response

```json
{
  "status": "healthy",
  "service": "HoistScout API",
  "timestamp": "2025-07-02T12:00:00",
  "environment": "production",
  "python_version": "3.11.x"
}
```

### 3. Diagnostic Response Structure

The `/api/health/diagnostic` endpoint provides:
- Import status for all critical packages
- Environment variable configuration
- Optional service availability
- Integration status

## Service Start Order

1. **Database** - Must be ready first
2. **Redis** - Required for API and worker
3. **API** - Can start once DB and Redis are ready
4. **Worker** - Can start once Redis is ready
5. **Frontend** - Can start independently

## Graceful Degradation

The system is designed to run without optional services:

| Service | Required | Fallback Behavior |
|---------|----------|-------------------|
| PostgreSQL | ✅ Yes | No fallback - critical |
| Redis | ✅ Yes | No fallback - critical |
| MinIO | ❌ No | File storage disabled |
| Ollama | ❌ No | AI scraping disabled |
| ScrapeGraph-AI | ❌ No | Basic scraping only |
| FlareSolverr | ❌ No | No captcha bypass |

## Deployment Commands

### Render.com Deployment

```bash
# Ensure render.yaml is configured correctly
git add -A
git commit -m "fix: bulletproof deployment configuration"
git push origin main
```

### Manual Docker Deployment

```bash
# Build and test locally first
docker build -f backend/Dockerfile -t hoistscout-api .
docker run -e DATABASE_URL=... -e REDIS_URL=... hoistscout-api

# Run deployment check inside container
docker run hoistscout-api python app/deployment_check.py
```

## Post-Deployment Monitoring

1. Check service logs for startup errors
2. Monitor `/api/health/ready` endpoint
3. Verify worker is processing jobs
4. Test a simple scraping job

## Emergency Rollback

If deployment fails:

1. Check `/api/health/diagnostic` for specific failures
2. Review service logs for detailed errors
3. Run `deployment_check.py` locally with production ENV vars
4. Rollback to previous working deployment
5. Fix issues and retry

## Continuous Deployment Safety

Add these GitHub Actions checks:

```yaml
- name: Run deployment validation
  run: |
    cd backend
    poetry install
    python app/deployment_check.py
```

This ensures no broken code reaches production.

---

**Remember**: A successful deployment starts with successful local validation!