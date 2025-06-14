# Frontend Deployment Fix Guide

## Problem Summary
Render is showing old frontend content due to:
1. Docker build issues with npm workspaces
2. Build cache not being invalidated
3. Complex monorepo structure causing build failures

## Solution Applied

### 1. Fixed Dockerfile Issues
- Updated frontend/Dockerfile to properly handle Next.js standalone mode
- Fixed workspace navigation issues during build
- Increased memory allocation to 512MB

### 2. Updated render.yaml
- Removed restrictive `buildFilter` that prevented rebuilds
- Added Redis service for job queue
- Added worker service for background tasks
- Added cache-busting environment variables

### 3. Improved API URL Handling
- Added runtime detection for API URL
- Better localhost detection
- Development logging for debugging

## Deployment Steps

### Step 1: Commit Changes
```bash
git add -A
git commit -m "fix: resolve frontend deployment issues on Render

- Fix Docker build for npm workspaces
- Add Redis and worker services
- Improve API URL runtime detection
- Remove build filters for proper cache invalidation"
git push origin main
```

### Step 2: Clear Render Build Cache
1. Go to Render Dashboard
2. Select the frontend service (hoistscraper-fe)
3. Click "Manual Deploy"
4. **Important**: Check "Clear build cache"
5. Deploy

### Step 3: Verify Environment Variables
Ensure these are set in Render:
- `NEXT_PUBLIC_API_URL=https://hoistscraper.onrender.com`
- `NODE_OPTIONS=--max-old-space-size=512`

### Step 4: Monitor Build Logs
Watch for:
- "Generating static pages" message
- ".next/standalone" being created
- No build errors

### Step 5: Test Deployment
1. Open in incognito/private browsing mode
2. Check Network tab to verify API calls go to correct URL
3. Check browser console for any errors

## If Issues Persist

### 1. Force Rebuild
```bash
# Make a trivial change to force rebuild
echo "// Build: $(date)" >> frontend/src/app/page.tsx
git add frontend/src/app/page.tsx
git commit -m "chore: force rebuild"
git push
```

### 2. Check Build Logs
Look for:
- Memory errors → Increase NODE_OPTIONS memory
- Module not found → Check Docker COPY commands
- Build timeout → Optimize build or increase timeout

### 3. Verify Standalone Build
The Next.js standalone build should create:
- `.next/standalone/server.js`
- `.next/standalone/node_modules/`
- `.next/static/` directory

### 4. Debug API Connection
In browser console:
```javascript
// Check what API URL is being used
console.log(process.env.NEXT_PUBLIC_API_URL)

// Test API connection
fetch('/api/websites').then(r => console.log(r.status))
```

## Long-term Improvements

1. **CI/CD Pipeline**: Add GitHub Actions to validate builds before deployment
2. **Health Checks**: Add frontend health endpoint
3. **Monitoring**: Add error tracking (Sentry)
4. **CDN**: Configure proper cache headers for static assets

## Testing Checklist

- [ ] Frontend loads without errors
- [ ] API calls work (check Network tab)
- [ ] CSV upload functions properly
- [ ] Job status updates in real-time
- [ ] No console errors
- [ ] Proper styling (no missing CSS)