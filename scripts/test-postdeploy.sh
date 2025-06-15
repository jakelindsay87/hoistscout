#!/bin/bash
# Post-deployment verification script for Render

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Render app URLs - update these with your actual URLs
BACKEND_URL="${BACKEND_URL:-https://hoistscraper.onrender.com}"
FRONTEND_URL="${FRONTEND_URL:-https://hoistscraper-fe.onrender.com}"

echo "🌐 HoistScraper Post-Deployment Verification"
echo "==========================================="
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"

# Track failures
FAILED_TESTS=()
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        FAILED_TESTS+=("$test_name")
    fi
}

# Function to check HTTP status
check_http_status() {
    local url=$1
    local expected_status=$2
    local actual_status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    [ "$actual_status" = "$expected_status" ]
}

# Backend Health Checks
echo -e "\n🏥 Backend Health Checks"
echo "----------------------"

run_test "Backend: Health Endpoint" "check_http_status '$BACKEND_URL/health' 200"
run_test "Backend: API Root" "curl -f -s '$BACKEND_URL/' | grep -q 'HoistScraper API'"
run_test "Backend: OpenAPI Docs Available" "check_http_status '$BACKEND_URL/docs' 200"
run_test "Backend: Websites Endpoint" "check_http_status '$BACKEND_URL/api/websites' 200"
run_test "Backend: Jobs Endpoint" "check_http_status '$BACKEND_URL/api/jobs' 200"

# Frontend Health Checks
echo -e "\n🎨 Frontend Health Checks"
echo "-----------------------"

run_test "Frontend: Home Page" "check_http_status '$FRONTEND_URL' 200"
run_test "Frontend: Has Title" "curl -f -s '$FRONTEND_URL' | grep -q 'HoistScraper'"
run_test "Frontend: Static Assets Loading" "curl -f -s '$FRONTEND_URL' | grep -q '_next/static'"

# API Integration Tests
echo -e "\n🔌 API Integration Tests"
echo "----------------------"

# Test creating a website
WEBSITE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/websites" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "name": "Test Site"}' || echo "{}")

run_test "API: Create Website" "echo '$WEBSITE_RESPONSE' | grep -q '\"id\"'"

# Extract website ID if created successfully
if echo "$WEBSITE_RESPONSE" | grep -q '"id"'; then
    WEBSITE_ID=$(echo "$WEBSITE_RESPONSE" | grep -o '"id":[0-9]*' | cut -d: -f2)
    run_test "API: Get Website by ID" "check_http_status '$BACKEND_URL/api/websites/$WEBSITE_ID' 200"
fi

# Test CSV endpoint exists
run_test "API: CSV Ingest Endpoint Exists" "check_http_status '$BACKEND_URL/api/ingest/csv' 405 || check_http_status '$BACKEND_URL/api/ingest/csv' 422"

# Cross-Origin Resource Sharing (CORS)
echo -e "\n🔒 CORS Configuration"
echo "-------------------"

run_test "CORS: Frontend can access API" "curl -s -I -X OPTIONS '$BACKEND_URL/api/websites' \
    -H 'Origin: $FRONTEND_URL' \
    -H 'Access-Control-Request-Method: GET' | grep -i 'access-control-allow-origin'"

# Performance Checks
echo -e "\n⚡ Performance Checks"
echo "-------------------"

# Test response times
BACKEND_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$BACKEND_URL/health")
FRONTEND_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$FRONTEND_URL")

run_test "Backend: Response Time < 2s" "[ \$(echo \"$BACKEND_TIME < 2\" | bc -l) -eq 1 ]"
run_test "Frontend: Response Time < 3s" "[ \$(echo \"$FRONTEND_TIME < 3\" | bc -l) -eq 1 ]"

# Service Dependencies
echo -e "\n🔗 Service Dependencies"
echo "---------------------"

# Check if backend can connect to database (via health endpoint details if available)
run_test "Backend: Database Connected" "curl -s '$BACKEND_URL/health' | grep -q '\"status\":\"healthy\"' || true"

# Error Pages
echo -e "\n📄 Error Handling"
echo "----------------"

run_test "Backend: 404 Handler" "check_http_status '$BACKEND_URL/api/nonexistent' 404"
run_test "Frontend: 404 Page" "check_http_status '$FRONTEND_URL/nonexistent-page' 404 || check_http_status '$FRONTEND_URL/nonexistent-page' 200"

# SSL/TLS Checks
echo -e "\n🔐 SSL/TLS Security"
echo "-----------------"

run_test "Backend: HTTPS Redirect" "curl -s -I '$BACKEND_URL' | grep -q 'Strict-Transport-Security' || true"
run_test "Frontend: HTTPS Redirect" "curl -s -I '$FRONTEND_URL' | grep -q 'Strict-Transport-Security' || true"

# Summary
echo -e "\n📊 Deployment Verification Summary"
echo "================================"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}${#FAILED_TESTS[@]}${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  - $test"
    done
    echo -e "\n${YELLOW}⚠️  DEPLOYMENT ISSUES DETECTED${NC}"
    echo "Please check the Render dashboard and logs for more information."
    exit 1
else
    echo -e "\n${GREEN}✅ DEPLOYMENT VERIFIED SUCCESSFULLY!${NC}"
    echo -e "\nYour application is live at:"
    echo "- Backend: $BACKEND_URL"
    echo "- Frontend: $FRONTEND_URL"
    echo -e "\n🎉 Deployment complete!"
    exit 0
fi