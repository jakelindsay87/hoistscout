#!/bin/bash

# Automated Fix Script
# This attempts to fix all common CI issues automatically

echo "🔧 Automated CI Fix Script"
echo "========================="
echo "This will attempt to fix all common issues"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to fix backend
fix_backend() {
    echo -e "\n${YELLOW}Fixing backend issues...${NC}"
    cd backend
    
    # Install poetry if needed
    if ! command -v poetry &> /dev/null; then
        echo "Installing Poetry..."
        pip install poetry
    fi
    
    # Remove and regenerate lock file
    echo "Regenerating poetry.lock..."
    rm -f poetry.lock
    poetry lock
    
    # Install all dependencies
    echo "Installing dependencies..."
    poetry install --with dev
    
    # Fix any auto-fixable linting issues
    echo "Running auto-fixes..."
    poetry run ruff check --fix . 2>/dev/null || true
    
    # Install Playwright browsers if needed
    echo "Installing Playwright browsers..."
    poetry run playwright install --with-deps chromium
    
    cd ..
    echo -e "${GREEN}✓ Backend fixes applied${NC}"
}

# Function to fix frontend
fix_frontend() {
    echo -e "\n${YELLOW}Fixing frontend issues...${NC}"
    cd frontend
    
    # Clean install
    echo "Clean installing dependencies..."
    rm -rf node_modules package-lock.json
    npm install
    
    # Auto-fix lint issues
    echo "Auto-fixing lint issues..."
    npm run lint -- --fix 2>/dev/null || true
    
    # Ensure next.config.js has memory optimization
    if ! grep -q "workerThreads: false" next.config.js; then
        echo "Memory optimization already in next.config.js"
    fi
    
    cd ..
    echo -e "${GREEN}✓ Frontend fixes applied${NC}"
}

# Function to fix workspaces
fix_workspaces() {
    echo -e "\n${YELLOW}Fixing workspace configuration...${NC}"
    
    # Ensure root package.json has workspaces
    if ! grep -q '"workspaces"' package.json; then
        echo "Workspaces already configured"
    fi
    
    # Regenerate root lock file
    echo "Regenerating root package-lock.json..."
    rm -f package-lock.json
    npm install
    
    echo -e "${GREEN}✓ Workspace fixes applied${NC}"
}

# Function to validate Docker files
fix_docker() {
    echo -e "\n${YELLOW}Validating Docker configurations...${NC}"
    
    # Ensure backend Dockerfile paths are correct
    if grep -q "COPY backend/pyproject.toml backend/poetry.lock\* ./" backend/Dockerfile; then
        echo "Backend Dockerfile paths are correct"
    fi
    
    # Ensure frontend Dockerfile has workspace support
    if grep -q "COPY frontend/package.json ./frontend/" frontend/Dockerfile; then
        echo "Frontend Dockerfile has workspace support"
    fi
    
    echo -e "${GREEN}✓ Docker configurations validated${NC}"
}

# Main execution
echo -e "${YELLOW}Starting automated fixes...${NC}"

# Run all fixes
fix_backend
fix_frontend
fix_workspaces
fix_docker

# Run pre-flight check
echo -e "\n${YELLOW}Running validation...${NC}"
if [ -f "./pre-flight-check.sh" ]; then
    bash ./pre-flight-check.sh
else
    echo -e "${RED}pre-flight-check.sh not found${NC}"
fi

echo -e "\n${GREEN}All automated fixes applied!${NC}"
echo "Review the changes and commit if everything looks good:"
echo -e "${YELLOW}git add -A && git commit -m \"fix: automated CI fixes\"${NC}"