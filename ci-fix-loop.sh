#!/bin/bash

# CI Fix Loop - Iterate until all tests pass
# This script helps you quickly fix CI failures

echo "🔧 CI Fix Loop - Push, Check, Fix, Repeat"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    echo "Or use: winget install --id GitHub.cli"
    exit 1
fi

# Function to push and wait for CI
push_and_check() {
    echo -e "\n${YELLOW}Pushing to GitHub...${NC}"
    git push origin HEAD
    
    echo -e "\n${YELLOW}Waiting for CI to start...${NC}"
    sleep 10
    
    # Get the latest workflow run
    echo -e "\n${YELLOW}Checking CI status...${NC}"
    gh run list --limit 1
    
    # Watch the latest run
    RUN_ID=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
    
    if [ -n "$RUN_ID" ]; then
        echo -e "\n${YELLOW}Watching run #$RUN_ID...${NC}"
        gh run watch $RUN_ID
        
        # Get the status
        STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
        
        if [ "$STATUS" = "success" ]; then
            echo -e "\n${GREEN}✅ All CI tests passed!${NC}"
            return 0
        else
            echo -e "\n${RED}❌ CI tests failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}Could not find workflow run${NC}"
        return 1
    fi
}

# Function to view logs
view_logs() {
    echo -e "\n${YELLOW}Fetching failure logs...${NC}"
    
    # Get the latest failed run
    RUN_ID=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
    
    if [ -n "$RUN_ID" ]; then
        # Download logs
        echo "Downloading logs..."
        gh run download $RUN_ID -n logs 2>/dev/null || true
        
        # View failed jobs
        echo -e "\n${YELLOW}Failed jobs:${NC}"
        gh run view $RUN_ID --log-failed
        
        echo -e "\n${YELLOW}Options:${NC}"
        echo "1. View full logs in browser"
        echo "2. Download all logs"
        echo "3. Continue to fix"
        read -p "Choose (1-3): " choice
        
        case $choice in
            1)
                gh run view $RUN_ID --web
                ;;
            2)
                gh run download $RUN_ID
                echo "Logs downloaded to current directory"
                ;;
        esac
    fi
}

# Function to help with common fixes
suggest_fixes() {
    echo -e "\n${YELLOW}Common CI fixes:${NC}"
    echo "1. Poetry issues: Check pyproject.toml versions"
    echo "2. Import errors: Missing dependencies" 
    echo "3. Lint errors: Run 'cd frontend && npm run lint'"
    echo "4. Type errors: Run 'cd frontend && npm run type-check'"
    echo "5. Test failures: Check test files"
    echo ""
    echo "After fixing, use: git add -A && git commit --amend --no-edit"
}

# Main loop
while true; do
    echo -e "\n${YELLOW}What would you like to do?${NC}"
    echo "1. Push and check CI"
    echo "2. View last failure logs"
    echo "3. Amend last commit and push"
    echo "4. Show common fixes"
    echo "5. Exit"
    read -p "Choose (1-5): " action
    
    case $action in
        1)
            if push_and_check; then
                echo -e "${GREEN}Success! All tests are green.${NC}"
                exit 0
            fi
            ;;
        2)
            view_logs
            ;;
        3)
            echo -e "\n${YELLOW}Amending commit and force pushing...${NC}"
            git add -A
            git commit --amend --no-edit
            git push --force-with-lease origin HEAD
            ;;
        4)
            suggest_fixes
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
    esac
done