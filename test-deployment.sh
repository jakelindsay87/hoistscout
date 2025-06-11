#!/bin/bash

echo "🚀 Starting deployment test..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Checking $service..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to check memory usage
check_memory() {
    local container=$1
    echo "Memory usage for $container:"
    docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep "$container" || echo "Container not found"
}

echo "1. Building and starting services with memory limits..."
docker-compose -f docker-compose.test.yml up -d --build

echo -e "\n2. Waiting for services to start..."
sleep 10

echo -e "\n3. Checking service health..."
all_healthy=true

if ! check_service "Database" "http://localhost:5433"; then
    all_healthy=false
fi

if ! check_service "Backend" "http://localhost:8001/health"; then
    all_healthy=false
fi

if ! check_service "Frontend" "http://localhost:3001"; then
    all_healthy=false
fi

if ! check_service "Ollama" "http://localhost:11435/api/tags"; then
    echo -e "${YELLOW}Warning: Ollama not responding (optional service)${NC}"
fi

echo -e "\n4. Checking memory usage..."
check_memory "frontend-test"
check_memory "backend-test"
check_memory "ollama-test"

echo -e "\n5. Testing API endpoints..."
# Test backend API
if curl -s http://localhost:8001/sites | jq . > /dev/null 2>&1; then
    echo -e "Backend API: ${GREEN}✓${NC}"
else
    echo -e "Backend API: ${RED}✗${NC}"
    all_healthy=false
fi

echo -e "\n6. Checking logs for errors..."
echo "Frontend logs:"
docker-compose -f docker-compose.test.yml logs frontend-test | tail -20 | grep -i error || echo "No errors found"

echo -e "\nBackend logs:"
docker-compose -f docker-compose.test.yml logs backend-test | tail -20 | grep -i error || echo "No errors found"

if [ "$all_healthy" = true ]; then
    echo -e "\n${GREEN}✅ All services are healthy!${NC}"
    echo "You can access:"
    echo "  - Frontend: http://localhost:3001"
    echo "  - Backend API: http://localhost:8001"
else
    echo -e "\n${RED}❌ Some services failed health checks${NC}"
fi

echo -e "\nTo stop the test deployment, run:"
echo "docker-compose -f docker-compose.test.yml down"

echo -e "\nTo monitor memory usage in real-time, run:"
echo "docker stats"