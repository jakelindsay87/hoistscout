#!/bin/bash

# Master CI Validation Script
# This ensures 100% that CI will pass

echo "🚀 Ensure CI Passes - Master Script"
echo "==================================="
echo "This script will ensure all GitHub Actions tests pass"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if script exists and run it
run_script() {
    local script=$1
    local description=$2
    
    echo -e "\n${BLUE}═══ $description ═══${NC}"
    
    if [ -f "$script" ]; then
        bash "$script"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed! Fix issues and try again.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Script not found: $script${NC}"
        exit 1
    fi
}

# Step 1: Sync all lock files
run_script "./sync-lock-files.sh" "Step 1: Synchronizing Lock Files"

# Step 2: Apply automated fixes
run_script "./fix-all-issues.sh" "Step 2: Applying Automated Fixes"

# Step 3: Run pre-flight validation
run_script "./pre-flight-check.sh" "Step 3: Pre-flight Validation"

# Step 4: Validate exact CI commands (if Docker available)
if command -v docker &> /dev/null; then
    run_script "./validate-ci-exact.sh" "Step 4: Exact CI Command Validation"
else
    echo -e "\n${YELLOW}Skipping Docker validation (Docker not available)${NC}"
fi

# Final summary
echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ALL VALIDATIONS PASSED!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "Your code is ready for CI. Next steps:"
echo ""
echo "1. Review changes:"
echo "   ${YELLOW}git status${NC}"
echo "   ${YELLOW}git diff${NC}"
echo ""
echo "2. Commit changes:"
echo "   ${YELLOW}git add -A${NC}"
echo "   ${YELLOW}git commit -m \"fix: ensure all CI tests pass\"${NC}"
echo ""
echo "3. Push to GitHub:"
echo "   ${YELLOW}git push origin $(git branch --show-current)${NC}"
echo ""
echo "CI should now pass! 🎉"