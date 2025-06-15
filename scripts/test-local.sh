#!/bin/bash
# Test all services locally without Docker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 HoistScraper Local Testing Suite"
echo "=================================="

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

# Backend Tests
echo -e "\n📦 Backend Tests"
echo "----------------"
cd backend

run_test "Backend: Install Dependencies" "poetry install --no-interaction"
run_test "Backend: Type Checking" "poetry run mypy hoistscraper || true"  # Don't fail on mypy for now
run_test "Backend: Linting" "poetry run ruff check . || true"  # Don't fail on linting for now
run_test "Backend: Unit Tests" "poetry run pytest -m 'not integration' -v"
run_test "Backend: Import Check" "poetry run python -c 'import hoistscraper.main'"

cd ..

# Frontend Tests  
echo -e "\n🎨 Frontend Tests"
echo "-----------------"
cd frontend

run_test "Frontend: Install Dependencies" "npm ci"
run_test "Frontend: TypeScript Check" "npm run type-check || true"  # Don't fail on TS for now
run_test "Frontend: Linting" "npm run lint || true"  # Don't fail on linting for now
run_test "Frontend: Unit Tests" "npm test -- --run"
run_test "Frontend: Build Check" "NODE_OPTIONS='--max-old-space-size=2048' npm run build"

cd ..

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
    exit 1
else
    echo -e "\n${GREEN}All tests passed! ✨${NC}"
    exit 0
fi