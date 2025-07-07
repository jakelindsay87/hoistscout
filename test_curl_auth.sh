#!/bin/bash
# Test authentication with curl

API_BASE="https://hoistscout-api.onrender.com"

echo "=== Testing HoistScout Auth with curl ==="
echo ""

# Step 1: Login
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123&grant_type=password")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
  echo "✗ Login failed"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Login successful"
echo "  Token: ${TOKEN:0:30}..."
echo ""

# Step 2: Test endpoints
echo "2. Testing endpoints with Bearer token..."
echo ""

# Test /api/auth/me
echo "Testing /api/auth/me:"
curl -s -X GET "$API_BASE/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"

echo ""
echo "Testing /api/websites:"
curl -s -X GET "$API_BASE/api/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"

echo ""
echo "Testing /api/opportunities:"  
curl -s -X GET "$API_BASE/api/opportunities" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"

echo ""
echo "Testing /api/scraping/jobs:"
curl -s -X GET "$API_BASE/api/scraping/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nStatus: %{http_code}\n"