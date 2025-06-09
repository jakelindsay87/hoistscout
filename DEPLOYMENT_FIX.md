# 🚀 Complete Deployment Fix Guide

## Overview of Issues Fixed

1. **Ollama Service**: Added proper configuration with custom Dockerfile
2. **Memory Issues**: Upgraded Ollama to `standard` plan for more memory
3. **Daily Crawl**: Added as a cron job service
4. **YAML Configuration**: Fixed all indentation and structure issues
5. **Environment Variables**: Added all missing configurations

## What's Changed

### 1. Ollama Service (NEW)
- Created custom Dockerfile in `ollama/Dockerfile`
- Auto-pulls mistral model on startup
- Configured with persistent storage (10GB)
- Uses standard plan to avoid memory issues

### 2. Backend API Updates
- Added `OLLAMA_HOST` environment variable
- Added `SMTP_PORT` configuration
- Changed `ANALYZE_TERMS` to `true`
- Proper health check endpoint

### 3. Frontend Updates
- Added `NEXT_TELEMETRY_DISABLED` to reduce build size
- Proper Docker configuration
- Correct API URL pointing

### 4. Daily Crawl Cron Job (NEW)
- Runs daily at 2 AM
- Uses backend Docker image
- Configured with all necessary environment variables

### 5. Database
- Added PostgreSQL major version specification

## Deployment Steps

### 1. Delete Existing Failed Services
In your Render Dashboard:
1. Delete the existing `ollama` service
2. Delete the existing `daily-crawl` service
3. Clear build cache for all services

### 2. Commit and Push Changes
```bash
git add render.yaml
git add ollama/Dockerfile
git add backend/hoistscraper/extractor/llm_extractor.py
git add DEPLOYMENT_FIX.md
git commit -m "fix: Complete deployment configuration with Ollama, daily-crawl, and all services"
git push origin main
```

### 3. Deploy Services in Order

1. **Database First** (`hoistscraper-db`)
   - Should already be available
   - Get the internal connection string

2. **Ollama Service** (`ollama`)
   - Will take ~5-10 minutes to pull the model
   - Monitor logs for "Pulling mistral:7b-q4_K_M model..."
   - Wait for health check to pass

3. **Backend API** (`hoistscraper-api`)
   - Set environment variables in dashboard:
     - `DATABASE_URL` (from step 1)
     - `SMTP_USER` (your Gmail)
     - `SMTP_PASSWORD` (Gmail app password)
     - `NOTIFY_EMAIL` (notification recipient)

4. **Frontend** (`hoistscraper-fe`)
   - Should auto-deploy after backend is ready

5. **Daily Crawl** (`daily-crawl`)
   - Set same environment variables as backend
   - Will run automatically at 2 AM daily

### 4. Environment Variables Summary

Set these in Render Dashboard for both `hoistscraper-api` and `daily-crawl`:
```
DATABASE_URL=<from-database-service>
SMTP_USER=<your-gmail>
SMTP_PASSWORD=<gmail-app-password>
NOTIFY_EMAIL=<recipient-email>
```

### 5. Verify Deployment

```bash
# Check Ollama
curl https://ollama.onrender.com/api/tags

# Check Backend
curl https://hoistscraper-api.onrender.com/health

# Check Frontend
curl https://hoistscraper-fe.onrender.com
```

## Important Notes

1. **Ollama Memory**: Using `standard` plan to avoid 8GB memory limit
2. **Model Download**: First deploy of Ollama will take time to download the model
3. **Persistent Storage**: Ollama uses 10GB disk to store models
4. **Cron Schedule**: Daily crawl runs at 2 AM UTC

## Troubleshooting

### If Ollama fails to deploy:
- Check logs for memory issues
- Ensure the model download completes
- Verify health check endpoint responds

### If Backend fails:
- Ensure DATABASE_URL is set correctly
- Check Ollama is accessible at the configured URL
- Verify SMTP credentials are correct

### If Frontend fails:
- Ensure backend is deployed and healthy first
- Check NEXT_PUBLIC_API_URL is correct

### If Daily Crawl fails:
- Check the same environment variables as backend
- Verify the sites.yml file exists in backend directory

## Next Steps After Deployment

1. Test the extraction by visiting the frontend
2. Verify email notifications work
3. Check that daily crawl runs at scheduled time
4. Monitor Ollama memory usage in Render metrics 