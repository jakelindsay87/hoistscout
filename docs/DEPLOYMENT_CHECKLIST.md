# HoistScraper Deployment Checklist

## Completed Tasks ✅

### 1. Frontend Deployment Fix
- Updated Dockerfile to handle npm workspaces correctly
- Fixed Next.js standalone build configuration
- Removed restrictive buildFilter in render.yaml
- Added runtime API URL detection
- Increased memory allocation to 512MB

### 2. Backend Results API
- Implemented missing `/api/results/{job_id}` endpoint
- Endpoint reads JSON results from disk storage
- Proper error handling for missing files and incomplete jobs
- Returns data in format expected by frontend

### 3. Infrastructure Updates
- Added Redis service to render.yaml
- Added worker service for background scraping
- Configured proper environment variables
- Added persistent disk storage for results

## Pre-Deployment Testing

### Local Testing Steps
1. **Start all services locally:**
   ```bash
   docker compose up --build
   ```

2. **Test the complete flow:**
   - Navigate to http://localhost:3000
   - Add a website to scrape
   - Trigger a scrape job
   - Monitor job status
   - View results when complete

3. **Verify the results API:**
   ```bash
   # Get a job ID from the UI, then test:
   curl http://localhost:8000/api/results/{job_id}
   ```

## Deployment Steps

### 1. Commit and Push Changes
```bash
git add -A
git commit -m "feat: complete MVP with results API and deployment fixes

- Add /api/results/{job_id} endpoint for retrieving scrape results
- Fix frontend Docker build for npm workspaces
- Add Redis and worker services to render.yaml
- Improve API URL runtime detection
- Update deployment configuration for production"

git push origin main
```

### 2. Deploy to Render

#### Frontend Service (hoistscraper-fe)
1. Go to Render Dashboard → hoistscraper-fe
2. Click "Manual Deploy"
3. **CHECK**: "Clear build cache" ✅
4. Deploy

#### Backend Service (hoistscraper)
1. Ensure environment variables are set:
   - `DATABASE_URL` (from database)
   - `REDIS_URL` (from Redis service)
   - `DATA_DIR=/data`
2. Deploy latest version

#### Redis Service (NEW)
1. Create new Redis service if not exists
2. Note the internal URL for REDIS_URL

#### Worker Service (NEW)
1. Create new background worker service
2. Set same environment variables as backend
3. Ensure disk mount at `/data`

### 3. Post-Deployment Verification

#### Health Checks
- [ ] Frontend loads: https://hoistscraper-fe.onrender.com
- [ ] Backend health: https://hoistscraper.onrender.com/health
- [ ] API docs: https://hoistscraper.onrender.com/docs

#### Functional Tests
- [ ] Create a new website via UI
- [ ] Upload CSV file
- [ ] Trigger a scrape job
- [ ] Job status updates properly
- [ ] Results load when job completes

#### Monitoring
- [ ] Check Render logs for errors
- [ ] Verify Redis connection
- [ ] Confirm worker is processing jobs
- [ ] Check disk usage for results storage

## Troubleshooting

### Frontend Shows Old Content
1. Clear build cache in Render
2. Check build logs for errors
3. Verify NEXT_PUBLIC_API_URL is set
4. Test in incognito mode

### Results Not Loading
1. Check job completed successfully
2. Verify result file exists on disk
3. Check worker logs for scraping errors
4. Ensure DATA_DIR is consistent across services

### Worker Not Processing Jobs
1. Verify Redis connection
2. Check worker logs
3. Ensure RQ is installed
4. Verify job enqueuing

### API Connection Issues
1. Check CORS settings
2. Verify API URL in frontend
3. Check network tab for errors
4. Test API directly with curl

## Next Steps

After successful deployment:

1. **Monitor for 24 hours**
   - Check error rates
   - Monitor performance
   - Verify data persistence

2. **Set up alerts**
   - Health check failures
   - High error rates
   - Disk space warnings

3. **Plan next features**
   - UI polish (feature/ux-refresh)
   - Site credentials (feature/site-credentials)
   - Performance optimizations

## Rollback Plan

If issues occur:
1. Revert to previous deployment in Render
2. Check logs to identify root cause
3. Fix locally and test thoroughly
4. Re-deploy with fixes

## Success Criteria

Deployment is successful when:
- ✅ All services are running
- ✅ Complete scraping flow works end-to-end
- ✅ Results are viewable in UI
- ✅ No critical errors in logs
- ✅ Performance is acceptable (<3s page loads)