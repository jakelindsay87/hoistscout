#!/bin/bash

# Exact CI Validation Script
# This runs the EXACT commands from the CI workflows

echo "🎯 Exact CI Command Validation"
echo "=============================="
echo "Running the exact commands from GitHub Actions..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track results
declare -A results

# Function to run exact CI command
run_ci_command() {
    local name=$1
    local command=$2
    echo -e "\n${BLUE}▶ $name${NC}"
    echo -e "${YELLOW}  Command: $command${NC}"
    
    # Run command and capture result
    eval "$command" &>/dev/null
    local result=$?
    
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}  ✓ Passed${NC}"
        results["$name"]="PASS"
    else
        echo -e "${RED}  ✗ Failed${NC}"
        results["$name"]="FAIL"
        # Run again with output to show error
        echo -e "${RED}  Error output:${NC}"
        eval "$command" 2>&1 | head -20
    fi
    
    return $result
}

# Test Database Tests job
echo -e "\n${YELLOW}=== Database Tests Job ===${NC}"
run_ci_command "Poetry Install (DB)" "cd backend && pip install poetry && poetry install --with dev"
run_ci_command "Database Tests" "cd backend && poetry run pytest tests/test_db.py -v --cov=hoistscraper --cov-report=term-missing"

# Test job
echo -e "\n${YELLOW}=== Test Job ===${NC}"
run_ci_command "Poetry Install" "cd backend && pip install poetry && poetry install --with dev"
run_ci_command "Install Playwright" "cd backend && poetry run playwright install --with-deps"
run_ci_command "Python Linting" "cd backend && poetry run ruff check"
run_ci_command "Python Tests" "cd backend && poetry run pytest -q"
run_ci_command "Frontend Install" "cd frontend && npm ci"
run_ci_command "Frontend Lint" "cd frontend && npm run lint"
run_ci_command "Frontend Type Check" "cd frontend && npm run type-check"
run_ci_command "Frontend Tests" "cd frontend && npm run test"

# Test Deployment job
echo -e "\n${YELLOW}=== Test Deployment Job ===${NC}"
run_ci_command "Backend Docker Build" "docker build -f backend/Dockerfile . -t backend-test"
run_ci_command "Frontend Docker Build" "docker build -f frontend/Dockerfile . -t frontend-test"
run_ci_command "Backend Imports" "cd backend && pip install fastapi sqlmodel pydantic psycopg2-binary && python -c 'import hoistscraper.main; print(\"Backend imports OK\")'"
run_ci_command "Frontend Build" "cd frontend && npm ci && NODE_OPTIONS='--max-old-space-size=1024' npm run build"
run_ci_command "Frontend Memory Build" "cd frontend && NODE_OPTIONS='--max-old-space-size=384' npm run build"

# Summary
echo -e "\n${BLUE}========== CI Validation Summary ==========${NC}"
echo ""

pass_count=0
fail_count=0

for test in "${!results[@]}"; do
    if [ "${results[$test]}" == "PASS" ]; then
        echo -e "${GREEN}✓ $test${NC}"
        ((pass_count++))
    else
        echo -e "${RED}✗ $test${NC}"
        ((fail_count++))
    fi
done

echo ""
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"

if [ $fail_count -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All CI commands passed! Safe to push.${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some CI commands failed. Fix these before pushing.${NC}"
    
    # Suggest fixes
    echo -e "\n${YELLOW}Suggested fixes:${NC}"
    
    if [[ "${results["Poetry Install"]}" == "FAIL" ]] || [[ "${results["Poetry Install (DB)]}" == "FAIL" ]]; then
        echo "• Poetry issues: cd backend && rm poetry.lock && poetry lock"
    fi
    
    if [[ "${results["Frontend Lint"]}" == "FAIL" ]]; then
        echo "• Lint issues: cd frontend && npm run lint -- --fix"
    fi
    
    if [[ "${results["Frontend Type Check"]}" == "FAIL" ]]; then
        echo "• Type issues: cd frontend && npm run type-check (fix errors shown)"
    fi
    
    if [[ "${results["Frontend Memory Build"]}" == "FAIL" ]]; then
        echo "• Memory issues: Check next.config.js has memory optimizations"
    fi
    
    exit 1
fi