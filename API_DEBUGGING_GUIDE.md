# API Debugging Guide

## Current Issue
The API service builds successfully but fails during runtime startup on Render.

## Fixes Already Applied
1. ✅ Fixed `postgres://` to `postgresql://` URL conversion
2. ✅ Added error handling for missing CLI imports  
3. ✅ Added all missing dependencies (prometheus-client, sentry-sdk)
4. ✅ Created error handling for monitoring initialization

## Debugging Options

### Option 1: Use Minimal API (Recommended)
Replace the Dockerfile temporarily with the minimal version:
```bash
# In render.yaml or Render dashboard, change:
dockerfilePath: ./Dockerfile.hoistscout-api
# To:
dockerfilePath: ./Dockerfile.hoistscout-api-minimal
```

This will deploy a basic API that should definitely work, confirming the infrastructure is correct.

### Option 2: Check Render Logs
Access detailed logs in Render dashboard:
1. Go to the API service page
2. Click on "Logs" tab
3. Look for the specific error after "Application startup..."

### Option 3: Local Testing
Test the Docker image locally before deploying:
```bash
# Build the image
docker build -f Dockerfile.hoistscout-api -t hoistscout-api .

# Run with environment variables
docker run -p 10000:10000 \
  -e DATABASE_URL="postgresql://user:pass@host/db" \
  -e REDIS_URL="redis://localhost:6379" \
  -e CREDENTIAL_PASSPHRASE="test123" \
  hoistscout-api
```

### Option 4: Use Safe Main
The repository now includes `main_safe.py` which has extensive error handling:
1. Rename `main.py` to `main_original.py`
2. Rename `main_safe.py` to `main.py`
3. Push and deploy

## Most Likely Causes

### 1. Database Connection
- Render's DATABASE_URL might use `postgres://` instead of `postgresql://`
- Connection timeout to PostgreSQL
- Missing database permissions

### 2. Import Issues
The app imports many modules that might have circular dependencies or missing files:
- `monitoring.py` imports might fail
- Router imports might have issues
- Middleware initialization might fail

### 3. Environment Variables
Missing or incorrectly formatted environment variables:
- `CREDENTIAL_PASSPHRASE` (required)
- `DATABASE_URL` (required)
- `REDIS_URL` (optional but checked)

## Quick Fix Script
Create this as `fix_api.sh` and run locally:
```bash
#!/bin/bash
# Test imports
python3 -c "
import sys
sys.path.append('backend')
try:
    from hoistscraper.main import app
    print('✅ Main app imports successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
"
```

## Nuclear Option
If all else fails, use the minimal Dockerfile which creates a simple API inline:
- No complex imports
- No database initialization
- Just basic endpoints
- This WILL work and proves the infrastructure is correct

## Cost-Saving Tips
1. Suspend the API service until the issue is resolved
2. Test locally with Docker before pushing
3. Use the minimal API to verify infrastructure
4. Only deploy when confident the fix will work