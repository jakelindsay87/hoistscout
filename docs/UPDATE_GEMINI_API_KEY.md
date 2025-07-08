# Update Gemini API Key on Render

This guide explains how to update the Gemini API key for HoistScout services deployed on Render.

## Overview

The HoistScout application uses the Gemini API for AI-powered features. To update the API key on deployed services, you need to:

1. Update the `GEMINI_API_KEY` environment variable on both services:
   - `hoistscout-api` (Backend API service)
   - `hoistscout-worker` (Background worker service)

2. Ensure `USE_GEMINI=true` is set on both services

3. Trigger a new deployment for the changes to take effect

## Prerequisites

- A Render account with access to the HoistScout services
- A Render API key (get it from https://dashboard.render.com/u/settings)
- The Gemini API key: `AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA`

## Method 1: Using the Python Script

The Python script provides a more robust way to update environment variables with better error handling.

```bash
# Navigate to the repository
cd /root/hoistscout-repo

# Run the script
python scripts/update_render_env_vars.py

# Or with the API key as environment variable
export RENDER_API_KEY="your-render-api-key"
python scripts/update_render_env_vars.py
```

The script will:
1. Prompt for your Render API key if not provided
2. Fetch all services and find hoistscout-api and hoistscout-worker
3. Update GEMINI_API_KEY and USE_GEMINI for both services
4. Optionally trigger deployments

## Method 2: Using the Bash Script

The bash script provides a simpler command-line interface using curl.

```bash
# Navigate to the repository
cd /root/hoistscout-repo

# Run with API key as argument
./scripts/update_gemini_env.sh "your-render-api-key"

# Or with API key as environment variable
export RENDER_API_KEY="your-render-api-key"
./scripts/update_gemini_env.sh
```

## Method 3: Manual Update via Render Dashboard

1. Go to https://dashboard.render.com
2. Navigate to each service (hoistscout-api and hoistscout-worker)
3. Click on the "Environment" tab
4. Update or add these environment variables:
   - `GEMINI_API_KEY`: `AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA`
   - `USE_GEMINI`: `true`
5. Click "Save Changes"
6. Click "Manual Deploy" to apply the changes

## Method 4: Using Render API Directly

You can also use curl commands directly:

```bash
# Set your API key
export RENDER_API_KEY="your-render-api-key"

# Get service IDs
curl -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services

# Update environment variable (replace SERVICE_ID)
curl -X POST https://api.render.com/v1/services/SERVICE_ID/env-vars \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "GEMINI_API_KEY", "value": "AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA"}'

# Trigger deployment
curl -X POST https://api.render.com/v1/services/SERVICE_ID/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Verification

After deployment completes:

1. Check service logs in Render dashboard for any startup errors
2. Test the API endpoints that use Gemini:
   ```bash
   # Test health endpoint
   curl https://hoistscout-api.onrender.com/api/health
   
   # Monitor worker logs for Gemini usage
   ```

3. Verify environment variables are set:
   - In Render dashboard, go to each service
   - Check the Environment tab
   - Confirm GEMINI_API_KEY and USE_GEMINI are present

## Troubleshooting

### Common Issues

1. **Authentication Error (401)**
   - Verify your Render API key is correct
   - Ensure the API key has not expired
   - Check you have permissions to update the services

2. **Service Not Found**
   - Verify service names are exactly `hoistscout-api` and `hoistscout-worker`
   - Check you're using the correct Render account

3. **Deployment Fails**
   - Check service logs for startup errors
   - Verify the Gemini API key is valid
   - Ensure all required environment variables are set

### Getting Help

- Render API Documentation: https://api-docs.render.com/
- Render Support: https://render.com/support

## Security Notes

- Never commit API keys to version control
- Rotate API keys regularly
- Use environment-specific keys for production vs development
- Monitor API usage for anomalies