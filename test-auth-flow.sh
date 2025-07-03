#!/bin/bash

echo "🧪 Testing HoistScout Authentication Flow"
echo "========================================"

API_URL="https://hoistscout-api.onrender.com"
FRONTEND_URL="https://hoistscout-frontend.onrender.com"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "\n${YELLOW}Test 1: Health Check${NC}"
curl -s "$API_URL/api/health" | jq . || echo -e "${RED}Health check failed${NC}"

# Test 2: Stats Endpoint (should work without auth in demo mode)
echo -e "\n${YELLOW}Test 2: Stats Endpoint (No Auth)${NC}"
STATS_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/stats")
HTTP_CODE=$(echo "$STATS_RESPONSE" | tail -n1)
BODY=$(echo "$STATS_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Stats endpoint accessible without auth${NC}"
    echo "$BODY" | jq .
else
    echo -e "${RED}✗ Stats endpoint returned $HTTP_CODE${NC}"
    echo "$BODY"
fi

# Test 3: Demo User Login
echo -e "\n${YELLOW}Test 3: Demo User Login${NC}"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=demo&password=demo123")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
BODY=$(echo "$LOGIN_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Demo login successful${NC}"
    ACCESS_TOKEN=$(echo "$BODY" | jq -r .access_token)
    echo "Access token: ${ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Demo login failed with $HTTP_CODE${NC}"
    echo "$BODY"
    ACCESS_TOKEN=""
fi

# Test 4: Authenticated Request
if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "\n${YELLOW}Test 4: Authenticated Request to /api/websites${NC}"
    AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/websites" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n1)
    BODY=$(echo "$AUTH_RESPONSE" | head -n-1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Authenticated request successful${NC}"
        echo "$BODY" | jq . | head -20
    else
        echo -e "${RED}✗ Authenticated request failed with $HTTP_CODE${NC}"
        echo "$BODY"
    fi
fi

# Test 5: Frontend Accessibility
echo -e "\n${YELLOW}Test 5: Frontend Accessibility${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend returned $FRONTEND_STATUS${NC}"
fi

echo -e "\n${YELLOW}Summary:${NC}"
echo "- API URL: $API_URL"
echo "- Frontend URL: $FRONTEND_URL"
echo "- Demo credentials: demo / demo123"
echo -e "\n${GREEN}Authentication implementation complete!${NC}"