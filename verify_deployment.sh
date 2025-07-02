#\!/bin/bash

# Deployment Verification Script for HoistScout
# This script checks all critical paths and configurations before deployment

echo "=== HoistScout Deployment Verification ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 missing"
        return 1
    fi
}

# Function to check directory
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 directory exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 directory missing"
        return 1
    fi
}

# Track overall status
ERRORS=0

echo "1. Checking Repository Structure"
echo "================================"

# Root level checks
check_file "render.yaml" || ((ERRORS++))
check_dir "backend" || ((ERRORS++))
check_dir "frontend" || ((ERRORS++))

echo
echo "2. Checking Backend Structure"
echo "============================="

# Backend checks
check_file "backend/Dockerfile" || ((ERRORS++))
check_file "backend/pyproject.toml" || ((ERRORS++))
check_dir "backend/app" || ((ERRORS++))
check_file "backend/app/__init__.py" || ((ERRORS++))
check_file "backend/app/main.py" || ((ERRORS++))
check_file "backend/app/worker.py" || ((ERRORS++))
check_dir "backend/app/api" || ((ERRORS++))
check_dir "backend/app/core" || ((ERRORS++))
check_dir "backend/app/models" || ((ERRORS++))

# Check for old hoistscraper code
if [ -d "backend/hoistscraper" ]; then
    echo -e "${RED}✗${NC} Old hoistscraper directory still exists\!"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC} No old hoistscraper code found"
fi

echo
echo "3. Checking Frontend Structure"
echo "=============================="

# Frontend checks
check_file "frontend/Dockerfile" || ((ERRORS++))
check_file "frontend/package.json" || ((ERRORS++))
check_file "frontend/package-lock.json" || ((ERRORS++))
check_file "frontend/next.config.js" || ((ERRORS++))
check_dir "frontend/src" || ((ERRORS++))
check_dir "frontend/public" || ((ERRORS++))

echo
echo "4. Checking Dockerfile Paths"
echo "============================"

# Check backend Dockerfile for correct paths
echo -n "Backend Dockerfile COPY paths: "
if grep -q "COPY backend/" backend/Dockerfile; then
    echo -e "${GREEN}✓${NC} Using correct 'backend/' prefix"
else
    echo -e "${RED}✗${NC} Missing 'backend/' prefix in COPY commands"
    ((ERRORS++))
fi

# Check frontend Dockerfile for correct paths
echo -n "Frontend Dockerfile COPY paths: "
if grep -q "COPY frontend/" frontend/Dockerfile; then
    echo -e "${GREEN}✓${NC} Using correct 'frontend/' prefix"
else
    echo -e "${RED}✗${NC} Missing 'frontend/' prefix in COPY commands"
    ((ERRORS++))
fi

echo
echo "5. Checking render.yaml Configuration"
echo "====================================="

# Check dockerfilePath values
echo -n "Backend dockerfilePath: "
if grep -q "dockerfilePath: backend/Dockerfile" render.yaml; then
    echo -e "${GREEN}✓${NC} Correct path (no leading ./)"
else
    echo -e "${RED}✗${NC} Incorrect dockerfilePath"
    ((ERRORS++))
fi

echo -n "Frontend dockerfilePath: "
if grep -q "dockerfilePath: frontend/Dockerfile" render.yaml; then
    echo -e "${GREEN}✓${NC} Correct path (no leading ./)"
else
    echo -e "${RED}✗${NC} Incorrect dockerfilePath"
    ((ERRORS++))
fi

echo -n "Worker dockerCommand: "
if grep -q "dockerCommand: celery -A app.worker" render.yaml; then
    echo -e "${GREEN}✓${NC} Correct worker command"
else
    echo -e "${RED}✗${NC} Incorrect worker command"
    ((ERRORS++))
fi

echo
echo "6. Checking Dependencies"
echo "======================="

# Check pyproject.toml for problematic dependencies
echo -n "Pre-commit version: "
if grep -q 'pre-commit = "\^3.3.0"' backend/pyproject.toml; then
    echo -e "${GREEN}✓${NC} Valid version (^3.3.0)"
else
    echo -e "${YELLOW}⚠${NC} Check pre-commit version in pyproject.toml"
fi

# Check if package.json has next dependency
echo -n "Next.js dependency: "
if grep -q '"next":' frontend/package.json; then
    echo -e "${GREEN}✓${NC} Next.js is listed as dependency"
else
    echo -e "${RED}✗${NC} Next.js missing from dependencies"
    ((ERRORS++))
fi

echo
echo "==============================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed\!${NC} Ready for deployment."
else
    echo -e "${RED}✗ Found $ERRORS errors.${NC} Fix these before deploying."
fi
echo "==============================="

exit $ERRORS
EOF < /dev/null
