#!/bin/bash

# Script to verify Gemini API setup on Render services
# Usage: ./verify_gemini_setup.sh [RENDER_API_KEY]

set -e

# Configuration
RENDER_API_BASE="https://api.render.com/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get Render API key
if [ -z "$1" ]; then
    if [ -z "$RENDER_API_KEY" ]; then
        echo -e "${YELLOW}RENDER_API_KEY not provided as argument or environment variable${NC}"
        read -p "Enter your Render API key: " RENDER_API_KEY
    fi
else
    RENDER_API_KEY="$1"
fi

if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}Error: RENDER_API_KEY is required${NC}"
    exit 1
fi

echo "=== Gemini API Setup Verification ==="
echo ""

# Function to check service env vars
check_service_env() {
    local service_id=$1
    local service_name=$2
    
    echo -e "${BLUE}Checking ${service_name}...${NC}"
    
    # Get environment variables
    ENV_VARS=$(curl -s -X GET "${RENDER_API_BASE}/services/${service_id}/env-vars" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}")
    
    # Check for GEMINI_API_KEY
    GEMINI_KEY=$(echo "$ENV_VARS" | jq -r '.[] | select(.key == "GEMINI_API_KEY") | .value' 2>/dev/null || echo "")
    USE_GEMINI=$(echo "$ENV_VARS" | jq -r '.[] | select(.key == "USE_GEMINI") | .value' 2>/dev/null || echo "")
    
    if [ -n "$GEMINI_KEY" ]; then
        echo -e "  ${GREEN}✓ GEMINI_API_KEY is set${NC} (${GEMINI_KEY:0:10}...${GEMINI_KEY: -4})"
    else
        echo -e "  ${RED}✗ GEMINI_API_KEY is NOT set${NC}"
    fi
    
    if [ "$USE_GEMINI" = "true" ]; then
        echo -e "  ${GREEN}✓ USE_GEMINI is set to true${NC}"
    else
        echo -e "  ${RED}✗ USE_GEMINI is NOT set to true${NC} (current value: ${USE_GEMINI:-"not set"})"
    fi
    
    # Get service status
    SERVICE_INFO=$(curl -s -X GET "${RENDER_API_BASE}/services/${service_id}" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}")
    
    STATUS=$(echo "$SERVICE_INFO" | jq -r '.status' 2>/dev/null || echo "unknown")
    echo -e "  Status: ${STATUS}"
    
    # Get latest deployment
    DEPLOYS=$(curl -s -X GET "${RENDER_API_BASE}/services/${service_id}/deploys?limit=1" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}")
    
    LATEST_DEPLOY=$(echo "$DEPLOYS" | jq -r '.[0]' 2>/dev/null)
    if [ "$LATEST_DEPLOY" != "null" ] && [ -n "$LATEST_DEPLOY" ]; then
        DEPLOY_STATUS=$(echo "$LATEST_DEPLOY" | jq -r '.status' 2>/dev/null || echo "unknown")
        DEPLOY_TIME=$(echo "$LATEST_DEPLOY" | jq -r '.createdAt' 2>/dev/null || echo "unknown")
        echo -e "  Latest deployment: ${DEPLOY_STATUS} (${DEPLOY_TIME})"
    fi
    
    echo ""
}

# Main execution
echo "Fetching services..."

# Get all services
SERVICES=$(curl -s -X GET "${RENDER_API_BASE}/services" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${RENDER_API_KEY}")

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to fetch services${NC}"
    exit 1
fi

# Extract hoistscout-api and hoistscout-worker service IDs
API_SERVICE_ID=$(echo "$SERVICES" | jq -r '.[] | select(.service.name == "hoistscout-api") | .service.id' 2>/dev/null || echo "")
WORKER_SERVICE_ID=$(echo "$SERVICES" | jq -r '.[] | select(.service.name == "hoistscout-worker") | .service.id' 2>/dev/null || echo "")

if [ -z "$API_SERVICE_ID" ] && [ -z "$WORKER_SERVICE_ID" ]; then
    echo -e "${RED}Error: Could not find hoistscout-api or hoistscout-worker services${NC}"
    exit 1
fi

echo ""

# Check each service
[ -n "$API_SERVICE_ID" ] && check_service_env "$API_SERVICE_ID" "hoistscout-api"
[ -n "$WORKER_SERVICE_ID" ] && check_service_env "$WORKER_SERVICE_ID" "hoistscout-worker"

# Test API endpoints
echo -e "${BLUE}Testing API endpoints...${NC}"
echo ""

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" https://hoistscout-api.onrender.com/api/health 2>/dev/null || echo "Failed to connect")

if echo "$HEALTH_RESPONSE" | grep -q "HTTP_STATUS:200"; then
    echo -e "${GREEN}✓ API health check passed${NC}"
    HEALTH_JSON=$(echo "$HEALTH_RESPONSE" | sed -n '1,/HTTP_STATUS/p' | sed '$d')
    echo "  Response: $HEALTH_JSON"
else
    echo -e "${RED}✗ API health check failed${NC}"
    echo "  Response: $HEALTH_RESPONSE"
fi

echo ""
echo "=== Summary ==="
echo ""

# Check if both services are properly configured
ISSUES=0

if [ -z "$API_SERVICE_ID" ]; then
    echo -e "${RED}✗ hoistscout-api service not found${NC}"
    ((ISSUES++))
fi

if [ -z "$WORKER_SERVICE_ID" ]; then
    echo -e "${RED}✗ hoistscout-worker service not found${NC}"
    ((ISSUES++))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All services found and checked${NC}"
    echo ""
    echo "Next steps:"
    echo "1. If GEMINI_API_KEY is not set, run: ./scripts/update_gemini_env.sh"
    echo "2. Monitor service logs in Render dashboard"
    echo "3. Test AI-powered features in the application"
else
    echo -e "${RED}✗ Some issues were found${NC}"
    echo ""
    echo "Please check the Render dashboard and ensure services are properly deployed."
fi