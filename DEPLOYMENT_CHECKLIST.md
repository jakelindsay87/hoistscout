# HoistScout Deployment Checklist

## Pre-Deployment Steps

### 1. Environment Variables to Set in Render Dashboard

#### API Service (hoistscout-api)
- [ ] `GEMINI_API_KEY` - Set your actual Google Gemini API key

#### Worker Service (hoistscout-worker) 
- [ ] `GEMINI_API_KEY` - Set your actual Google Gemini API key (same as API service)

### 2. Verify Configuration

#### render.yaml Updates Applied:
- ✅ Added missing logger import in worker.py
- ✅ Fixed worker dockerCommand to include `cd /app`
- ✅ Added missing environment variables for worker (SECRET_KEY, ENVIRONMENT)
- ✅ Commented out ollama-proxy service (not needed with Gemini)
- ✅ Changed GEMINI_API_KEY from generateValue to sync: false

### 3. Service Dependencies

#### Required Services:
- PostgreSQL database (hoistscout-db) - Free tier
- Redis instance (using existing: redis://red-d1hljoruibrs73fe7vkg:6379)
- API service (hoistscout-api)
- Worker service (hoistscout-worker)
- Frontend service (hoistscout-frontend)

#### Optional Services:
- Ollama proxy (commented out - using Gemini instead)

### 4. Worker Configuration

The worker is configured to:
- Use Celery with Redis as broker/backend
- Run periodic tasks:
  - Scrape all active websites every 6 hours
  - Clean up old jobs daily at 2 AM
- Process individual website scraping tasks
- Use Gemini for AI processing (when USE_GEMINI=true)

### 5. Post-Deployment Verification

1. Check API health: `https://hoistscout-api.onrender.com/api/health`
2. Verify worker logs show "Connected to Redis" and "Ready to process tasks"
3. Test scraping by adding a website through the frontend
4. Monitor worker logs to ensure tasks are being processed

### 6. Common Issues and Solutions

#### Worker Not Starting:
- Ensure GEMINI_API_KEY is set correctly
- Check worker logs for import errors
- Verify Redis connection string is correct

#### Scraping Not Working:
- Check if worker is processing tasks (look for "Received task" in logs)
- Verify Gemini API key has proper permissions
- Check for rate limiting from Gemini API

#### Build Failures:
- If ollama-proxy fails to build, ensure it's commented out in render.yaml
- Check Docker build logs for missing dependencies

### 7. Manual Steps After Deployment

1. Set the GEMINI_API_KEY environment variable in Render dashboard for both API and Worker services
2. Trigger a manual deploy if auto-deploy doesn't start
3. Add demo websites through the frontend to test the system

## Important Notes

- The system now uses Google Gemini instead of Ollama for AI processing
- The ollama-proxy service is no longer needed and has been commented out
- Worker must have the same environment variables as the API service for consistency
- Redis URL is hardcoded but should ideally be moved to a Render Redis service