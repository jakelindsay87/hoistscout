# HoistScout Worker Debug Script

## Overview

The `debug_worker.py` script provides comprehensive diagnostics for troubleshooting HoistScout worker issues on Render. It helps identify why workers might not be processing jobs by checking multiple aspects of the deployment.

## Usage

```bash
cd /root/hoistscout-repo
python scripts/debug_worker.py
```

## What It Checks

1. **Service Status** - Verifies if the worker service is active on Render
2. **Latest Deployment** - Checks deployment status and recent commits
3. **Environment Variables** - Validates critical environment variables are configured
4. **Redis Connection** - Tests Redis connectivity if REDIS_URL is available
5. **Log Analysis** - Attempts to fetch and analyze worker logs for errors
6. **Worker Startup Simulation** - Tests if the worker module can be imported locally
7. **Startup Commands** - Shows the correct commands to start the worker
8. **Action Items** - Provides clear steps to fix identified issues

## Key Findings from Current Diagnosis

The script identified that the worker is failing because **required environment variables are not set**:

- ❌ `REDIS_URL` - Not configured
- ❌ `DATABASE_URL` - Not configured  
- ❌ `GEMINI_API_KEY` - Not configured
- ❌ `USE_GEMINI` - Not configured

## How to Fix Worker Issues

1. **Set Environment Variables in Render Dashboard:**
   - Go to: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/env
   - Add the required variables:
     - `REDIS_URL`: Your Redis connection string
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `GEMINI_API_KEY`: Your Google Gemini API key
     - `USE_GEMINI`: Set to `true`

2. **Verify Worker Start Command:**
   - Go to: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/settings
   - Ensure start command is: `celery -A app.worker worker --loglevel=info`

3. **Redeploy the Worker:**
   - After adding environment variables, trigger a manual deploy
   - Monitor the deployment logs for any errors

## Script Features

- **Color-coded output** for easy reading
- **Direct links** to Render dashboard pages
- **Connection testing** for Redis when URL is available
- **Local simulation** of worker startup to catch import errors
- **Clear action items** based on diagnosis results

## Common Issues Detected

1. **Missing Environment Variables** - The most common issue
2. **Redis Connection Failures** - Invalid Redis URL or service down
3. **Import Errors** - Missing dependencies or code issues
4. **Incorrect Start Command** - Wrong command in Render settings

## Monitoring After Fix

Once environment variables are set and worker is redeployed:

1. Check worker logs: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/logs
2. Look for successful Celery startup messages
3. Verify Redis connection established
4. Test job submission through the API

## Notes

- The Render API doesn't expose environment variable values for security reasons
- Logs must be checked manually through the Render dashboard
- The script can test Redis connections if the URL is available locally