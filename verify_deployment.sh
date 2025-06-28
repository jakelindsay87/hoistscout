#!/bin/bash

# Deployment Verification Script for HoistScraper

echo "=== HoistScraper Deployment Verification ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API Key (update this after setting in Render)
API_KEY="Qwl5vPbcrDnhci4Q6MzPPKLRahoJ-rP7j9F3eQzXqpQ"
BACKEND_URL="https://hoistscraper.onrender.com"
FRONTEND_URL="https://hoistscraper-1-wf9y.onrender.com"

echo "1. Testing Backend Health Check..."
if curl -s "${BACKEND_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi
echo

echo "2. Testing Security Headers..."
HEADERS=$(curl -sI "${BACKEND_URL}/health")
if echo "$HEADERS" | grep -q "X-Content-Type-Options: nosniff"; then
    echo -e "${GREEN}✓ Security headers present${NC}"
else
    echo -e "${RED}✗ Security headers missing${NC}"
fi
echo

echo "3. Testing Admin Endpoint Without Auth..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BACKEND_URL}/api/admin/clear-database")
if [ "$RESPONSE" = "401" ]; then
    echo -e "${GREEN}✓ Admin endpoint properly protected (401 Unauthorized)${NC}"
else
    echo -e "${RED}✗ Admin endpoint not protected! Response: $RESPONSE${NC}"
fi
echo

echo "4. Testing Admin Endpoint With Auth..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BACKEND_URL}/api/admin/stats" -H "X-API-Key: ${API_KEY}")
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ Admin authentication working${NC}"
else
    echo -e "${YELLOW}⚠ Admin auth failed (Response: $RESPONSE) - Check if API key is set in Render${NC}"
fi
echo

echo "5. Testing Debug Endpoint (Should be blocked in production)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/api/debug")
if [ "$RESPONSE" = "404" ]; then
    echo -e "${GREEN}✓ Debug endpoints properly blocked${NC}"
else
    echo -e "${RED}✗ Debug endpoint accessible! Response: $RESPONSE${NC}"
fi
echo

echo "6. Testing API Documentation (Should be disabled in production)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/docs")
if [ "$RESPONSE" = "404" ]; then
    echo -e "${GREEN}✓ API docs properly disabled${NC}"
else
    echo -e "${RED}✗ API docs accessible! Response: $RESPONSE${NC}"
fi
echo

echo "7. Testing Frontend..."
if curl -s "${FRONTEND_URL}" | grep -q "HoistScraper"; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend not accessible${NC}"
fi
echo

echo "8. Testing CORS Headers..."
RESPONSE=$(curl -sI -X OPTIONS "${BACKEND_URL}/api/websites" \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: GET")
if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ CORS properly configured${NC}"
else
    echo -e "${RED}✗ CORS not configured${NC}"
fi
echo

echo "=== Verification Complete ==="
echo
echo "Next Steps:"
echo "1. If any tests failed, check the Render logs for errors"
echo "2. Ensure ADMIN_API_KEY is set in Render environment variables"
echo "3. Monitor the service for any issues"
echo "4. Test the frontend functionality manually"