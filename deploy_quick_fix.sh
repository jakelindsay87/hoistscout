#!/bin/bash
# Quick deployment script for HoistScraper demo

echo "🚀 HoistScraper Quick Fix Deployment"
echo "===================================="

# Step 1: Rebuild backend with Playwright
echo ""
echo "Step 1: Rebuilding backend container with Playwright..."
docker-compose build backend

# Step 2: Restart backend
echo ""
echo "Step 2: Restarting backend service..."
docker-compose up -d backend

# Step 3: Wait for backend to be ready
echo ""
echo "Step 3: Waiting for backend to start..."
sleep 10

# Check if backend is healthy
echo ""
echo "Checking backend health..."
curl -f http://localhost:8000/health && echo "✅ Backend is healthy!" || echo "❌ Backend health check failed"

# Step 4: Test scraping with manual trigger
echo ""
echo "Step 4: Testing scraping with tenders.gov.au..."
echo ""
echo "Triggering scrape job for website ID 2 (tenders.gov.au)..."
response=$(curl -X POST http://localhost:8000/api/scrape/2/trigger -s -w "\nHTTP_STATUS:%{http_code}")
http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_STATUS:/d')

if [ "$http_status" = "200" ]; then
    echo "✅ Scrape job triggered successfully!"
    echo "Response: $body"
else
    echo "❌ Failed to trigger scrape job (HTTP $http_status)"
    echo "Response: $body"
fi

# Step 5: Check opportunities after a delay
echo ""
echo "Step 5: Waiting 30 seconds for scraping to complete..."
sleep 30

echo ""
echo "Checking for opportunities..."
opportunities=$(curl -s http://localhost:8000/api/opportunities)
opportunity_count=$(echo "$opportunities" | jq '. | length' 2>/dev/null || echo "0")

if [ "$opportunity_count" -gt "0" ]; then
    echo "✅ Found $opportunity_count opportunities!"
    echo ""
    echo "First 3 opportunities:"
    echo "$opportunities" | jq '.[0:3] | .[] | {title: .title, deadline: .deadline, url: .source_url}' 2>/dev/null || echo "$opportunities"
else
    echo "⚠️  No opportunities found yet. The scraper might still be processing."
    echo "Try checking again with: curl http://localhost:8000/api/opportunities | jq"
fi

# Step 6: Show logs
echo ""
echo "Step 6: Recent backend logs:"
docker logs hoistscraper-backend --tail 20

echo ""
echo "========================================="
echo "✅ Quick fix deployment complete!"
echo ""
echo "Next steps:"
echo "1. Check opportunities: curl http://localhost:8000/api/opportunities | jq"
echo "2. View all jobs: curl http://localhost:8000/api/scrape-jobs | jq"
echo "3. Open opportunities.html in your browser to see the UI"
echo ""
echo "For production deployment with Ollama, run:"
echo "docker-compose -f docker-compose.prod.yml up -d"