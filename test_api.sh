#!/bin/bash
# API testing script for HoistScraper

echo "🧪 HoistScraper API Test Suite"
echo "=============================="

BASE_URL="http://localhost:8000"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo ""
    echo "Testing: $description"
    echo "Method: $method $endpoint"
    
    if [ -n "$data" ]; then
        response=$(curl -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -s -w "\nHTTP_STATUS:%{http_code}")
    else
        response=$(curl -X $method "$BASE_URL$endpoint" \
            -s -w "\nHTTP_STATUS:%{http_code}")
    fi
    
    http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    if [ "$http_status" = "200" ] || [ "$http_status" = "201" ]; then
        echo -e "${GREEN}✅ Success (HTTP $http_status)${NC}"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Failed (HTTP $http_status)${NC}"
        echo "$body"
    fi
}

# 1. Health check
test_endpoint "GET" "/health" "" "Health check"

# 2. Get all websites
test_endpoint "GET" "/api/websites" "" "List all websites"

# 3. Get tenders.gov.au website details
test_endpoint "GET" "/api/websites/2" "" "Get tenders.gov.au details"

# 4. Get all scrape jobs
test_endpoint "GET" "/api/scrape-jobs" "" "List all scrape jobs"

# 5. Get opportunities
test_endpoint "GET" "/api/opportunities" "" "List all opportunities"

# 6. Create a new scrape job
echo ""
echo -e "${YELLOW}Creating a new scrape job for tenders.gov.au...${NC}"
test_endpoint "POST" "/api/scrape-jobs" '{"website_id": 2}' "Create scrape job"

# 7. Trigger manual scrape
echo ""
echo -e "${YELLOW}Triggering manual scrape (this may take a while)...${NC}"
test_endpoint "POST" "/api/scrape/2/trigger" "" "Manual scrape trigger"

# Summary
echo ""
echo "=============================="
echo "API Test Suite Complete!"
echo ""
echo "To monitor scraping progress:"
echo "- Check jobs: curl $BASE_URL/api/scrape-jobs | jq"
echo "- Check opportunities: curl $BASE_URL/api/opportunities | jq"
echo "- View logs: docker logs hoistscraper-backend --tail 50"