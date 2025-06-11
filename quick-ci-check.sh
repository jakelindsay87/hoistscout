#!/bin/bash

# Quick CI Check - Fast validation of most common issues
echo "⚡ Quick CI Check"
echo "================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

errors=0

# 1. Check Poetry lock exists and is valid
echo -n "Checking poetry.lock... "
if [ -f "backend/poetry.lock" ]; then
    cd backend && poetry lock --check &>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Out of sync${NC}"
        ((errors++))
    fi
    cd ..
else
    echo -e "${RED}✗ Missing${NC}"
    ((errors++))
fi

# 2. Check for ESLint errors
echo -n "Checking for ESLint errors... "
cd frontend && npm run lint &>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Lint errors found${NC}"
    ((errors++))
fi
cd ..

# 3. Check for TypeScript errors
echo -n "Checking TypeScript... "
cd frontend && npm run type-check &>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Type errors found${NC}"
    ((errors++))
fi
cd ..

# 4. Check Node memory settings
echo -n "Checking memory optimization... "
if grep -q "workerThreads: false" frontend/next.config.js; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Missing memory optimization${NC}"
    ((errors++))
fi

# 5. Check for package-lock.json
echo -n "Checking package-lock.json... "
if [ -f "frontend/package-lock.json" ] && [ -f "package-lock.json" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Missing lock files${NC}"
    ((errors++))
fi

# Summary
echo ""
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ Quick check passed! Run ./ensure-ci-passes.sh for full validation.${NC}"
else
    echo -e "${RED}❌ Found $errors issues. Run ./fix-all-issues.sh to fix automatically.${NC}"
fi

exit $errors