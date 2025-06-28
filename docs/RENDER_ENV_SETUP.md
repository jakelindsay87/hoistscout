# Render Environment Variables Setup

## Required Environment Variables

### Backend Service (hoistscraper)

1. **ADMIN_API_KEY** (Required for security)
   ```
   ADMIN_API_KEY=Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ
   ```
   - Used to authenticate admin endpoints
   - Store this securely and rotate regularly
   - Never commit this to version control

2. **Other Backend Variables** (Already configured)
   - `DATABASE_URL` - Auto-configured from database
   - `REDIS_URL` - Auto-configured from Redis service
   - `RENDER` - Set automatically by Render
   - `OLLAMA_HOST` - LLM service URL
   - `DATA_DIR` - Data storage directory

### Frontend Service (hoistscraper-fe)

1. **NEXT_PUBLIC_API_URL** (Already in render.yaml)
   ```
   NEXT_PUBLIC_API_URL=https://hoistscraper.onrender.com
   ```

## How to Set in Render Dashboard

1. **Navigate to your Render Dashboard**
   - Go to https://dashboard.render.com
   - Select the `hoistscraper` backend service

2. **Add Environment Variable**
   - Click on "Environment" tab
   - Click "Add Environment Variable"
   - Add:
     - Key: `ADMIN_API_KEY`
     - Value: `Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ`
   - Click "Save Changes"

3. **Service will automatically redeploy**
   - Render will restart the service with new environment variables
   - Monitor logs for any startup issues

## Testing Admin Authentication

After deployment, test admin endpoints:

```bash
# Test without auth (should fail with 401)
curl -X POST https://hoistscraper.onrender.com/api/admin/clear-database

# Test with auth (should work)
curl -X POST https://hoistscraper.onrender.com/api/admin/clear-database \
  -H "X-API-Key: Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ" \
  -d "confirm=true"

# Get admin stats
curl https://hoistscraper.onrender.com/api/admin/stats \
  -H "X-API-Key: Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ"
```

## Security Notes

1. **API Key Storage**:
   - Keep the API key secure
   - Don't share in public channels
   - Rotate regularly (monthly recommended)

2. **Access Control**:
   - Only share with authorized administrators
   - Consider using different keys for different admin users
   - Log all admin actions for audit trail

3. **Production Safety**:
   - Database clearing is disabled in production by default
   - To enable (dangerous!), set `ALLOW_PROD_DB_CLEAR=true`
   - Always backup before destructive operations