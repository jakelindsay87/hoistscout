# Deployment Troubleshooting Guide

## Complete Fix Applied (Latest)

### All Services Properly Configured
1. **Ollama Service** - Added with custom Dockerfile and standard plan
2. **Daily Crawl** - Added as cron job service
3. **Backend/Frontend** - Fixed all configuration issues
4. **Database** - PostgreSQL 16 with proper configuration

## Issues Fixed

### 1. YAML Indentation Issues in render.yaml
- **Problem**: Inconsistent indentation causing YAML parsing errors
- **Solution**: Completely rewrote render.yaml with proper structure

### 2. Frontend Runtime Issues
- **Problem**: Node.js runtime having issues with TypeScript compilation
- **Solution**: Using Docker runtime with proper Dockerfile configuration

### 3. CORS Configuration
- **Problem**: Backend CORS only allowing localhost, blocking production frontend
- **Solution**: Already configured correctly in main.py

### 4. Ollama Service Missing
- **Problem**: Ollama not defined in render.yaml but required by backend
- **Solution**: Added Ollama service with custom Dockerfile and persistent storage

### 5. Daily Crawl Service Missing
- **Problem**: Cron job service not defined
- **Solution**: Added as cron type service running at 2 AM daily

### 6. Memory Issues
- **Problem**: Ollama running out of memory (8GB limit)
- **Solution**: Using `standard` plan for Ollama service

## Current Configuration

### Ollama Service (ollama)
- Runtime: Docker
- Dockerfile: `./ollama/Dockerfile`
- Plan: Standard (more memory)
- Storage: 10GB persistent disk
- Health Check: `/api/tags`

### Backend (hoistscraper-api)
- Runtime: Docker
- Dockerfile: `./backend/Dockerfile`
- Health Check: `/health`
- Port: 8000

### Frontend (hoistscraper-fe)
- Runtime: Docker
- Dockerfile: `./frontend/Dockerfile`
- Port: 3000
- Environment: `NEXT_PUBLIC_API_URL=https://hoistscraper-api.onrender.com`

### Daily Crawl (daily-crawl)
- Type: Cron Job
- Schedule: 2 AM UTC daily
- Uses backend Docker image
- Command: `python scripts/run_crawl.py --config sites.yml`

### Database (hoistscraper-db)
- PostgreSQL 16
- Free plan

## Environment Variables to Set in Render Dashboard

### Backend Service AND Daily Crawl
Set these in the Render dashboard (marked as `sync: false` in render.yaml):

1. `DATABASE_URL` - PostgreSQL connection string
2. `SMTP_USER` - Gmail SMTP username
3. `SMTP_PASSWORD` - Gmail app password
4. `NOTIFY_EMAIL` - Email for notifications

### Frontend Service
These are already configured in render.yaml:
- `NEXT_PUBLIC_API_URL=https://hoistscraper-api.onrender.com`
- `NODE_ENV=production`
- `NEXT_TELEMETRY_DISABLED=1`

## Deployment Order

1. **Database** - Should already be available
2. **Ollama** - Deploy and wait for model download
3. **Backend** - Deploy after Ollama is healthy
4. **Frontend** - Deploy after Backend is healthy
5. **Daily Crawl** - Deploy last

## Common Issues and Solutions

### Ollama Issues
- **Memory errors**: Using standard plan resolves this
- **Model download**: First deploy takes ~10 minutes
- **Health check failing**: Wait for model to download

### Backend Issues
- **Can't reach Ollama**: Ensure Ollama is deployed and healthy
- **Database connection**: Set `DATABASE_URL` in environment variables
- **SMTP errors**: Configure SMTP environment variables

### Frontend Issues
- **API connection**: Verify `NEXT_PUBLIC_API_URL` points to backend
- **Build errors**: Docker runtime handles TypeScript properly
- **CORS errors**: Already configured in backend

### Daily Crawl Issues
- **Not running**: Check cron schedule and logs
- **Environment variables**: Must match backend configuration
- **File not found**: Ensure sites.yml exists in backend directory

## Testing Deployment

### Ollama Health Check
```bash
curl https://ollama.onrender.com/api/tags
```

### Backend Health Check
```bash
curl https://hoistscraper-api.onrender.com/health
```
Expected response:
```json
{"status": "healthy", "service": "hoistscraper-api"}
```

### Frontend Access
Visit: https://hoistscraper-fe.onrender.com

### API Documentation
Visit: https://hoistscraper-api.onrender.com/docs

## Service Dependencies

```
Database (hoistscraper-db)
    ↓
Ollama (ollama)
    ↓
Backend API (hoistscraper-api)
    ↓
Frontend (hoistscraper-fe)
    ↓
Daily Crawl (daily-crawl)
```

## Next Steps

1. Delete failed services in Render dashboard
2. Clear build cache for all services
3. Commit and push the updated configuration
4. Deploy services in the correct order
5. Set environment variables as needed
6. Monitor deployment logs for each service 