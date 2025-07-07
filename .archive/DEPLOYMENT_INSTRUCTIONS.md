# HoistScraper Production Deployment Instructions

## Current Status

The HoistScraper application has critical database schema mismatches preventing it from functioning properly. The code has been updated but the production database needs migration.

### Issues Identified:

1. **Database Schema Mismatch** (CRITICAL)
   - Production database expects columns: `credentials`, `region`, `government_level`, `grant_type`
   - These columns were missing from the model definitions
   - All API endpoints return 500 errors due to this mismatch

2. **Frontend API Configuration**
   - Frontend was calling the wrong API URL
   - Fixed to use `https://hoistscraper.onrender.com`

3. **Worker Configuration**
   - Worker is configured to use simple queue (in-process)
   - No Redis dependency needed

## Deployment Steps

### 1. Push Code Changes

```bash
git push origin main
```

The following changes have been made:
- Updated `models.py` with missing fields
- Fixed frontend API URL configuration
- Added performance optimizations
- Created deployment and testing scripts

### 2. Deploy Backend

**Option A: Using Render Dashboard**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to the `hoistscraper` service
3. Click "Manual Deploy" → "Deploy latest commit"

**Option B: Using Render CLI**
```bash
render deploy --service hoistscraper
```

### 3. Deploy Frontend

**Option A: Using Render Dashboard**
1. Navigate to the `hoistscraper-fe` service
2. Click "Manual Deploy" → "Deploy latest commit"

**Option B: Using Render CLI**
```bash
render deploy --service hoistscraper-fe
```

### 4. Deploy Worker

**Option A: Using Render Dashboard**
1. Navigate to the `hoistscraper-worker` service
2. Click "Manual Deploy" → "Deploy latest commit"

**Option B: Using Render CLI**
```bash
render deploy --service hoistscraper-worker
```

### 5. Verify Deployment

Wait 5-10 minutes for all services to deploy, then run:

```bash
# Check deployment status
python3 check_deployment.py

# Test scraping functionality
python3 test_scraping.py

# Run integration tests
python3 integration_tests.py

# Validate worker
python3 validate_worker.py
```

## Environment Variables

Ensure these are set in Render:

### Backend Service
- `DATABASE_URL` - PostgreSQL connection string
- `USE_SIMPLE_QUEUE` - Set to "true"
- `WORKER_TYPE` - Set to "v2"
- `LOG_LEVEL` - Set to "INFO"

### Frontend Service
- `NEXT_PUBLIC_API_URL` - Set to "https://hoistscraper.onrender.com"
- `NODE_OPTIONS` - Set to "--max-old-space-size=2048"

### Worker Service
- `DATABASE_URL` - Same as backend
- `USE_SIMPLE_QUEUE` - Set to "true"
- `WORKER_TYPE` - Set to "v2"
- `DATA_DIR` - Set to "/data"

## Post-Deployment Checklist

- [ ] Backend deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] Worker deployed and processing jobs
- [ ] API endpoints returning 200 status
- [ ] Scraping functionality working
- [ ] Performance within acceptable limits

## Scripts Created

1. **deploy_production.sh** - Automated deployment script
2. **performance_analysis.py** - Performance monitoring
3. **integration_tests.py** - Full system testing
4. **validate_worker.py** - Worker health checks
5. **check_deployment.py** - Deployment verification
6. **test_scraping.py** - Scraping functionality test

## Performance Optimizations Added

1. Database query optimization with indexes
2. Response caching for frequently accessed data
3. Connection pooling configuration
4. Batch job creation support
5. Pagination improvements

## Expected Results After Deployment

- API health check should return "healthy"
- Website CRUD operations should work (200/201 status)
- Scraping jobs should process successfully
- Worker should pick up and complete jobs
- Frontend should load and display data

## Troubleshooting

If issues persist after deployment:

1. Check Render logs for each service
2. Verify environment variables are set correctly
3. Ensure database migrations completed
4. Check worker is running and processing jobs
5. Review error messages in logs

## Contact

For deployment issues, check:
- Render service logs
- Database connection settings
- Environment variable configuration