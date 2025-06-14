#!/bin/bash
# Deployment verification and cache clearing script

echo "🚀 HoistScraper Deployment Verification"
echo "======================================="

# Force rebuild on Render
echo "1. Forcing cache clear and rebuild..."
echo "   - Clear build cache in Render dashboard"
echo "   - Or trigger manual deploy with 'Clear build cache' option"

# Check frontend build
echo -e "\n2. Verifying frontend build locally..."
cd frontend
npm run build
if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    exit 1
fi

# Check for common issues
echo -e "\n3. Checking for common deployment issues..."

# Check if .next directory exists
if [ -d ".next/standalone" ]; then
    echo "✅ Standalone build created"
else
    echo "❌ Standalone build missing - check next.config.js"
fi

# Check environment variables
echo -e "\n4. Required environment variables for Render:"
echo "   - NEXT_PUBLIC_API_URL (set to your backend URL)"
echo "   - NODE_OPTIONS='--max-old-space-size=512'"
echo "   - BUILD_ID (auto-generated for cache busting)"

# Deployment checklist
echo -e "\n5. Deployment Checklist:"
echo "   [ ] Commit all changes"
echo "   [ ] Push to main branch"
echo "   [ ] Check Render build logs"
echo "   [ ] Clear browser cache when testing"
echo "   [ ] Verify API URL is correct in Network tab"

echo -e "\n✨ If old content persists:"
echo "   1. In Render Dashboard: Manual Deploy → Clear build cache"
echo "   2. Check build logs for any errors"
echo "   3. Verify NEXT_PUBLIC_API_URL is set correctly"
echo "   4. Test in incognito/private browsing mode"