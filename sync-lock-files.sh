#!/bin/bash

# Lock File Sync Script
# Ensures all lock files are properly synchronized

echo "🔒 Lock File Synchronization"
echo "==========================="
echo "This ensures poetry.lock and package-lock.json are in sync"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Backend lock file
echo -e "${YELLOW}Syncing backend poetry.lock...${NC}"
cd backend

# Remove existing lock
rm -f poetry.lock

# Generate fresh lock file
poetry lock --no-update
echo -e "${GREEN}✓ poetry.lock regenerated${NC}"

# Install to verify
poetry install --with dev
echo -e "${GREEN}✓ Backend dependencies verified${NC}"

cd ..

# Frontend lock file
echo -e "\n${YELLOW}Syncing frontend package-lock.json...${NC}"
cd frontend

# Remove existing lock
rm -f package-lock.json

# Generate fresh lock file
npm install
echo -e "${GREEN}✓ package-lock.json regenerated${NC}"

cd ..

# Root lock file (for workspaces)
echo -e "\n${YELLOW}Syncing root package-lock.json...${NC}"

# Remove existing lock
rm -f package-lock.json

# Generate fresh lock file
npm install
echo -e "${GREEN}✓ Root package-lock.json regenerated${NC}"

# Git status
echo -e "\n${YELLOW}Changes to lock files:${NC}"
git status --porcelain | grep -E "(poetry\.lock|package-lock\.json)" || echo "No changes to lock files"

echo -e "\n${GREEN}✅ All lock files synchronized!${NC}"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Add files: git add -A"
echo "3. Commit: git commit -m \"chore: sync lock files\""
echo "4. Run validation: ./pre-flight-check.sh"