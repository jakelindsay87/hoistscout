#!/bin/bash
# Test to see where the redirects are going

API_BASE="https://hoistscout-api.onrender.com"

# Login first
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123&grant_type=password")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

echo "Testing redirects..."
echo ""

# Follow redirects and show where they lead
echo "Testing /api/websites with -L (follow redirects):"
curl -L -v -X GET "$API_BASE/api/websites" \
  -H "Authorization: Bearer $TOKEN" 2>&1 | grep -E "(< HTTP|< Location|{)"

echo ""
echo "Testing without following redirects:"
curl -v -X GET "$API_BASE/api/websites" \
  -H "Authorization: Bearer $TOKEN" 2>&1 | grep -E "(< HTTP|< Location)"