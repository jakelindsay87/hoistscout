#!/bin/bash
# Test all services with Docker Compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🐳 HoistScraper Docker Testing Suite"
echo "===================================="

# Track failures
FAILED_TESTS=()
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "\n${YELLOW}Running: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        FAILED_TESTS+=("$test_name")
    fi
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${BLUE}Waiting for $service to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}$service is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    echo -e "\n${RED}$service failed to start${NC}"
    return 1
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker compose -f docker-compose.test.yml down -v
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Start Docker Compose
echo -e "\n${BLUE}Starting Docker Compose...${NC}"
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml build --no-cache
docker compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo -e "\n${BLUE}Waiting for services to start...${NC}"
sleep 10  # Initial wait

# Service Health Checks
echo -e "\n🏥 Service Health Checks"
echo "----------------------"

run_test "PostgreSQL Health" "docker compose -f docker-compose.test.yml exec -T postgres pg_isready -U hoistscraper_user -d hoistscraper_test"
run_test "Redis Health" "docker compose -f docker-compose.test.yml exec -T redis redis-cli ping | grep -q PONG"
run_test "Backend Health" "wait_for_service 'Backend API' 'http://localhost:8000/health'"
run_test "Frontend Health" "wait_for_service 'Frontend' 'http://localhost:3000'"

# API Endpoint Tests
echo -e "\n🔌 API Endpoint Tests"
echo "-------------------"

run_test "API: Root Endpoint" "curl -f -s http://localhost:8000/ | grep -q 'HoistScraper API'"
run_test "API: OpenAPI Docs" "curl -f -s http://localhost:8000/docs > /dev/null"
run_test "API: List Websites" "curl -f -s http://localhost:8000/api/websites | grep -q '\\['"
run_test "API: List Jobs" "curl -f -s http://localhost:8000/api/jobs | grep -q '\\['"

# Frontend Tests
echo -e "\n🎨 Frontend Tests"
echo "----------------"

run_test "Frontend: Home Page" "curl -f -s http://localhost:3000 | grep -q 'HoistScraper'"
run_test "Frontend: Static Assets" "curl -f -s http://localhost:3000/_next/static/chunks/main.js > /dev/null"

# Integration Tests
echo -e "\n🔗 Integration Tests"
echo "------------------"

# Create a test website
run_test "Integration: Create Website" "curl -X POST http://localhost:8000/api/websites \
    -H 'Content-Type: application/json' \
    -d '{\"url\": \"https://example.com\", \"name\": \"Test Site\"}' \
    -f -s > /dev/null"

# Check logs for errors
echo -e "\n📋 Checking Logs for Errors"
echo "-------------------------"

run_test "Backend: No Critical Errors" "! docker compose -f docker-compose.test.yml logs backend | grep -i 'error\\|critical\\|fatal' | grep -v 'INFO'"
run_test "Worker: No Critical Errors" "! docker compose -f docker-compose.test.yml logs worker | grep -i 'error\\|critical\\|fatal' | grep -v 'INFO'"
run_test "Frontend: No Build Errors" "! docker compose -f docker-compose.test.yml logs frontend | grep -i 'error\\|failed' | grep -v 'node_modules'"

# Container Status
echo -e "\n📦 Container Status"
echo "-----------------"

run_test "All Containers Running" "[ \$(docker compose -f docker-compose.test.yml ps -q | wc -l) -eq 5 ]"

# Summary
echo -e "\n📊 Test Summary"
echo "==============="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}${#FAILED_TESTS[@]}${NC}"

if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  - $test"
    done
    
    echo -e "\n${YELLOW}Debug Information:${NC}"
    echo "View logs with: docker compose -f docker-compose.test.yml logs"
    exit 1
else
    echo -e "\n${GREEN}All tests passed! ✨${NC}"
    exit 0
fi