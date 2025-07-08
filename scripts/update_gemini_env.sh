#!/bin/bash

# Script to update GEMINI_API_KEY in Render services using curl
# Usage: ./update_gemini_env.sh [RENDER_API_KEY]

set -e

# Configuration
GEMINI_API_KEY="AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA"
RENDER_API_BASE="https://api.render.com/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get Render API key
if [ -z "$1" ]; then
    if [ -z "$RENDER_API_KEY" ]; then
        echo -e "${YELLOW}RENDER_API_KEY not provided as argument or environment variable${NC}"
        echo "To get your Render API key:"
        echo "1. Go to https://dashboard.render.com/u/settings"
        echo "2. Scroll to 'API Keys' section"
        echo "3. Create a new API key or copy an existing one"
        echo ""
        read -p "Enter your Render API key: " RENDER_API_KEY
    fi
else
    RENDER_API_KEY="$1"
fi

if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}Error: RENDER_API_KEY is required${NC}"
    exit 1
fi

echo "=== Render Environment Variables Updater ==="
echo ""

# Function to get services
get_services() {
    echo "Fetching Render services..."
    SERVICES=$(curl -s -X GET "${RENDER_API_BASE}/services" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}")
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to fetch services${NC}"
        exit 1
    fi
    
    echo "$SERVICES"
}

# Function to update environment variable
update_env_var() {
    local service_id=$1
    local service_name=$2
    local key=$3
    local value=$4
    
    echo "Updating ${key} for ${service_name}..."
    
    # First, get existing env vars to check if key exists
    ENV_VARS=$(curl -s -X GET "${RENDER_API_BASE}/services/${service_id}/env-vars" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}")
    
    # Check if the key already exists
    EXISTING_ID=$(echo "$ENV_VARS" | jq -r '.[] | select(.key == "'${key}'") | .id' 2>/dev/null || echo "")
    
    if [ -n "$EXISTING_ID" ]; then
        # Update existing variable
        RESPONSE=$(curl -s -X PUT "${RENDER_API_BASE}/services/${service_id}/env-vars/${EXISTING_ID}" \
            -H "Accept: application/json" \
            -H "Authorization: Bearer ${RENDER_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "{\"value\": \"${value}\"}")
    else
        # Add new variable
        RESPONSE=$(curl -s -X POST "${RENDER_API_BASE}/services/${service_id}/env-vars" \
            -H "Accept: application/json" \
            -H "Authorization: Bearer ${RENDER_API_KEY}" \
            -H "Content-Type: application/json" \
            -d "{\"key\": \"${key}\", \"value\": \"${value}\"}")
    fi
    
    # Check if successful
    if echo "$RESPONSE" | grep -q "\"key\":\"${key}\""; then
        echo -e "${GREEN}✓ Successfully updated ${key} for ${service_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to update ${key} for ${service_name}${NC}"
        echo "Response: $RESPONSE"
        return 1
    fi
}

# Function to trigger deployment
trigger_deploy() {
    local service_id=$1
    local service_name=$2
    
    echo "Triggering deployment for ${service_name}..."
    
    RESPONSE=$(curl -s -X POST "${RENDER_API_BASE}/services/${service_id}/deploys" \
        -H "Accept: application/json" \
        -H "Authorization: Bearer ${RENDER_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{}")
    
    if echo "$RESPONSE" | grep -q "\"id\""; then
        echo -e "${GREEN}✓ Deployment triggered for ${service_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to trigger deployment for ${service_name}${NC}"
        echo "Response: $RESPONSE"
        return 1
    fi
}

# Main execution
echo "Fetching services..."
SERVICES=$(get_services)

# Extract hoistscout-api and hoistscout-worker service IDs
API_SERVICE_ID=$(echo "$SERVICES" | jq -r '.[] | select(.service.name == "hoistscout-api") | .service.id' 2>/dev/null || echo "")
WORKER_SERVICE_ID=$(echo "$SERVICES" | jq -r '.[] | select(.service.name == "hoistscout-worker") | .service.id' 2>/dev/null || echo "")

if [ -z "$API_SERVICE_ID" ] && [ -z "$WORKER_SERVICE_ID" ]; then
    echo -e "${RED}Error: Could not find hoistscout-api or hoistscout-worker services${NC}"
    echo "Available services:"
    echo "$SERVICES" | jq -r '.[] | .service.name' 2>/dev/null || echo "Unable to parse services"
    exit 1
fi

echo ""
echo "Found services:"
[ -n "$API_SERVICE_ID" ] && echo "  - hoistscout-api (ID: ${API_SERVICE_ID})"
[ -n "$WORKER_SERVICE_ID" ] && echo "  - hoistscout-worker (ID: ${WORKER_SERVICE_ID})"

echo ""
echo "Updating environment variables..."

# Update environment variables
UPDATED_COUNT=0

if [ -n "$API_SERVICE_ID" ]; then
    if update_env_var "$API_SERVICE_ID" "hoistscout-api" "GEMINI_API_KEY" "$GEMINI_API_KEY"; then
        update_env_var "$API_SERVICE_ID" "hoistscout-api" "USE_GEMINI" "true"
        ((UPDATED_COUNT++))
    fi
fi

if [ -n "$WORKER_SERVICE_ID" ]; then
    if update_env_var "$WORKER_SERVICE_ID" "hoistscout-worker" "GEMINI_API_KEY" "$GEMINI_API_KEY"; then
        update_env_var "$WORKER_SERVICE_ID" "hoistscout-worker" "USE_GEMINI" "true"
        ((UPDATED_COUNT++))
    fi
fi

if [ $UPDATED_COUNT -gt 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Successfully updated environment variables for ${UPDATED_COUNT} services${NC}"
    echo ""
    echo -e "${YELLOW}Note: Environment variable changes require a new deployment to take effect.${NC}"
    
    read -p "Would you like to trigger deployments now? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Triggering deployments..."
        
        [ -n "$API_SERVICE_ID" ] && trigger_deploy "$API_SERVICE_ID" "hoistscout-api"
        [ -n "$WORKER_SERVICE_ID" ] && trigger_deploy "$WORKER_SERVICE_ID" "hoistscout-worker"
        
        echo ""
        echo -e "${GREEN}✓ Deployments triggered. Monitor progress at https://dashboard.render.com${NC}"
    else
        echo ""
        echo "Environment variables updated but not deployed."
        echo "To deploy manually, visit https://dashboard.render.com and click 'Manual Deploy' for each service."
    fi
else
    echo ""
    echo -e "${RED}✗ No services were updated successfully.${NC}"
fi

echo ""
echo "=== Summary ==="
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}...${GEMINI_API_KEY: -4}"
echo "USE_GEMINI: true"
echo "Services updated: ${UPDATED_COUNT}"