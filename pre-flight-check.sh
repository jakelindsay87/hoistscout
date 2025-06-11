#!/bin/bash

# Pre-flight CI Validation Script
# This ensures all tests will pass before pushing to GitHub

echo "✈️  Pre-flight CI Check"
echo "======================"
echo "This script validates everything locally before pushing"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track failures
FAILURES=0

# Function to check command result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        FAILURES=$((FAILURES + 1))
    fi
}

# Function to run a check
run_check() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

echo -e "${YELLOW}Starting comprehensive validation...${NC}"

# 1. Check Prerequisites
run_check "Checking prerequisites"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ "$python_version" == "3.11" ]] || [[ "$python_version" == "3.12" ]]; then
    check_result 0 "Python version: $python_version"
else
    check_result 1 "Python version: $python_version (need 3.11+)"
fi

# Check Node version
node_version=$(node --version 2>&1 | grep -oE '[0-9]+' | head -1)
if [ "$node_version" -ge 20 ]; then
    check_result 0 "Node version: $(node --version)"
else
    check_result 1 "Node version: $(node --version) (need 20+)"
fi

# 2. Backend Validation
run_check "Backend validation"

cd backend 2>/dev/null || { echo -e "${RED}Backend directory not found${NC}"; exit 1; }

# Check if Poetry is installed
if command -v poetry &> /dev/null; then
    check_result 0 "Poetry is installed"
    
    # Validate pyproject.toml
    poetry check &>/dev/null
    check_result $? "pyproject.toml is valid"
    
    # Check if lock file is in sync
    poetry lock --check &>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}  → Regenerating poetry.lock...${NC}"
        poetry lock --no-update &>/dev/null
        check_result $? "poetry.lock regenerated"
    else
        check_result 0 "poetry.lock is in sync"
    fi
    
    # Install dependencies
    echo -e "${YELLOW}  → Installing dependencies...${NC}"
    poetry install --with dev &>/dev/null
    check_result $? "Dependencies installed"
    
    # Run ruff (linter)
    poetry run ruff check . &>/dev/null
    check_result $? "Ruff linting"
    
    # Run mypy (type checker)
    poetry run mypy . &>/dev/null
    check_result $? "MyPy type checking"
    
    # Test imports
    poetry run python -c "import hoistscraper.main" &>/dev/null
    check_result $? "Backend imports"
    
    # Run pytest
    poetry run pytest tests/test_basic.py -q &>/dev/null
    check_result $? "Backend tests"
else
    echo -e "${YELLOW}Poetry not installed - installing...${NC}"
    pip install poetry
    FAILURES=$((FAILURES + 1))
fi

cd ..

# 3. Frontend Validation
run_check "Frontend validation"

cd frontend 2>/dev/null || { echo -e "${RED}Frontend directory not found${NC}"; exit 1; }

# Check package.json
if [ -f "package.json" ]; then
    check_result 0 "package.json exists"
else
    check_result 1 "package.json not found"
fi

# Install dependencies
echo -e "${YELLOW}  → Installing frontend dependencies...${NC}"
npm ci &>/dev/null
check_result $? "Dependencies installed"

# Run ESLint
npm run lint &>/dev/null
check_result $? "ESLint"

# Run TypeScript check
npm run type-check &>/dev/null
check_result $? "TypeScript"

# Run tests
npm run test &>/dev/null
check_result $? "Frontend tests"

# Test build with memory limit
echo -e "${YELLOW}  → Testing build with memory constraints...${NC}"
NODE_OPTIONS="--max-old-space-size=384" npm run build &>/dev/null
check_result $? "Build with memory limit"

cd ..

# 4. CI Workflow Validation
run_check "CI workflow validation"

# Check workflow files
for workflow in .github/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        # Basic YAML validation
        python3 -c "import yaml; yaml.safe_load(open('$workflow'))" &>/dev/null
        check_result $? "$(basename $workflow) syntax"
    fi
done

# 5. Docker Build Test (if Docker available)
run_check "Docker build test"

if command -v docker &> /dev/null; then
    # Test backend Dockerfile
    docker build -f backend/Dockerfile . -t test-backend &>/dev/null
    check_result $? "Backend Docker build"
    
    # Test frontend Dockerfile
    docker build -f frontend/Dockerfile . -t test-frontend &>/dev/null
    check_result $? "Frontend Docker build"
    
    # Clean up
    docker rmi test-backend test-frontend &>/dev/null
else
    echo -e "${YELLOW}Docker not available - skipping${NC}"
fi

# 6. Final Summary
echo -e "\n${BLUE}========== Summary ==========${NC}"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Safe to push.${NC}"
    echo -e "\nRun: ${YELLOW}git push origin $(git branch --show-current)${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES checks failed${NC}"
    echo -e "\nFix the issues above before pushing to avoid CI failures."
    
    # Provide fix suggestions
    echo -e "\n${YELLOW}Quick fixes:${NC}"
    echo "• Poetry issues: cd backend && poetry lock --no-update"
    echo "• Lint issues: cd frontend && npm run lint -- --fix"
    echo "• Type issues: Check TypeScript errors in frontend/src"
    echo "• Test issues: Run tests locally to see detailed errors"
    
    exit 1
fi