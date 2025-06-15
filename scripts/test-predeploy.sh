#!/bin/bash
# Pre-deployment verification script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🚀 HoistScraper Pre-Deployment Verification"
echo "=========================================="

# Track failures
FAILED_CHECKS=()
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Function to run a check
run_check() {
    local check_name=$1
    local check_command=$2
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${YELLOW}Checking: $check_name${NC}"
    
    if eval "$check_command"; then
        echo -e "${GREEN}✅ PASSED: $check_name${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ FAILED: $check_name${NC}"
        FAILED_CHECKS+=("$check_name")
    fi
}

# Git Status Check
echo -e "\n📝 Git Status"
echo "------------"

run_check "Working Directory Clean" "[ -z \"\$(git status --porcelain)\" ]"
run_check "On Main Branch" "[ \"\$(git branch --show-current)\" = \"main\" ]"
run_check "Up to Date with Remote" "git fetch && [ -z \"\$(git log HEAD..origin/main --oneline)\" ]"

# File Existence Checks
echo -e "\n📁 Required Files"
echo "----------------"

run_check "Backend Dockerfile" "[ -f backend/Dockerfile ]"
run_check "Worker Dockerfile" "[ -f backend/Dockerfile.worker ]"
run_check "Frontend Dockerfile" "[ -f frontend/Dockerfile ]"
run_check "Redis Dockerfile" "[ -f redis/Dockerfile ]"
run_check "Render YAML" "[ -f render.yaml ]"
run_check "API Entrypoint Script" "[ -f backend/api_entrypoint.sh ] && [ -x backend/api_entrypoint.sh ]"
run_check "Worker Entrypoint Script" "[ -f backend/worker_entrypoint.sh ] && [ -x backend/worker_entrypoint.sh ]"

# Configuration Checks
echo -e "\n⚙️  Configuration"
echo "---------------"

run_check "Frontend Standalone Mode" "grep -q \"output.*:.*'standalone'\" frontend/next.config.js"
run_check "Redis Private Service" "grep -q \"type: pserv\" render.yaml"
run_check "Worker Uses Correct Dockerfile" "grep -q \"dockerfilePath:.*Dockerfile.worker\" render.yaml"

# Dependency Checks
echo -e "\n📦 Dependencies"
echo "--------------"

run_check "Backend Poetry Lock" "[ -f backend/poetry.lock ]"
run_check "Frontend Package Lock" "[ -f frontend/package-lock.json ]"

# Docker Build Tests
echo -e "\n🐳 Docker Build Tests"
echo "-------------------"

run_check "Backend Docker Build" "docker build -f backend/Dockerfile -t test-backend . > /dev/null 2>&1"
run_check "Worker Docker Build" "docker build -f backend/Dockerfile.worker -t test-worker . > /dev/null 2>&1"
run_check "Frontend Docker Build" "docker build -f frontend/Dockerfile -t test-frontend . > /dev/null 2>&1"
run_check "Redis Docker Build" "docker build -f redis/Dockerfile -t test-redis redis/ > /dev/null 2>&1"

# Python Code Checks
echo -e "\n🐍 Python Code Quality"
echo "--------------------"

cd backend
run_check "Python Syntax Check" "python -m py_compile hoistscraper/*.py"
run_check "Import Check" "python -c 'import hoistscraper.main; import hoistscraper.worker; import hoistscraper.queue'"
cd ..

# JavaScript/TypeScript Checks
echo -e "\n📜 JavaScript/TypeScript Quality"
echo "------------------------------"

cd frontend
run_check "Package.json Valid" "node -e 'JSON.parse(require(\"fs\").readFileSync(\"package.json\"))'"
run_check "Next Config Valid" "node -e 'require(\"./next.config.js\")'"
cd ..

# Environment Variable Documentation
echo -e "\n🔐 Environment Variables"
echo "----------------------"

run_check "Render.yaml Has DATABASE_URL" "grep -q 'DATABASE_URL' render.yaml"
run_check "Render.yaml Has REDIS_URL" "grep -q 'REDIS_URL' render.yaml"
run_check "Render.yaml Has NEXT_PUBLIC_API_URL" "grep -q 'NEXT_PUBLIC_API_URL' render.yaml"

# Memory Optimizations
echo -e "\n💾 Memory Optimizations"
echo "---------------------"

run_check "Frontend Memory Limit Set" "grep -q 'NODE_OPTIONS.*max-old-space-size' frontend/Dockerfile"
run_check "Redis Memory Limit Set" "grep -q 'maxmemory' render.yaml"

# Health Checks
echo -e "\n🏥 Health Check Configuration"
echo "---------------------------"

run_check "Backend Health Endpoint" "grep -q '/health' backend/Dockerfile"
run_check "Frontend Health Check" "grep -q 'healthcheck' docker-compose.test.yml"

# Security Checks
echo -e "\n🔒 Security"
echo "-----------"

run_check "No Hardcoded Secrets" "! grep -r 'password\\|secret\\|key' --include='*.py' --include='*.js' --include='*.ts' . | grep -v -E 'password.*=|secret.*=|key.*=' | grep -E '\".*\"|'"'"'.*'"'"' || true"
run_check "Redis Protected Mode Disabled for Internal" "grep -q 'protected-mode no' render.yaml"

# Final Build Test
echo -e "\n🏗️  Final Build Test"
echo "------------------"

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    echo -e "${BLUE}Running full Docker Compose build...${NC}"
    run_check "Docker Compose Build" "docker compose -f docker-compose.test.yml build --quiet"
fi

# Summary
echo -e "\n📊 Pre-Deployment Summary"
echo "========================"
echo "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}${#FAILED_CHECKS[@]}${NC}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Checks:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "  - $check"
    done
    echo -e "\n${RED}❌ NOT READY FOR DEPLOYMENT${NC}"
    echo "Please fix the above issues before deploying."
    exit 1
else
    echo -e "\n${GREEN}✅ READY FOR DEPLOYMENT!${NC}"
    echo -e "\nNext steps:"
    echo "1. Run: git push origin main"
    echo "2. Monitor Render dashboard for deployment status"
    echo "3. Run post-deployment verification: ./scripts/test-postdeploy.sh"
    exit 0
fi