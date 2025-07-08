#!/bin/bash

echo "🔍 Monitoring HoistScout Deployment"
echo "=================================="
echo ""

while true; do
    echo -e "\n📊 Checking at $(date '+%H:%M:%S')..."
    
    # Check API health
    API_STATUS=$(curl -s https://hoistscout-api.onrender.com/api/health | jq -r '.status' 2>/dev/null || echo "down")
    echo "API Status: $API_STATUS"
    
    # Check pending jobs using our script
    echo -e "\nRunning production check..."
    python3 /root/hoistscout-repo/check_production_pipeline.py 2>/dev/null | grep -E "(pending|running|completed|SUCCESS)" || echo "Check failed"
    
    echo -e "\n---"
    echo "Press Ctrl+C to stop monitoring"
    echo "Worker rebuild URL: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/events"
    
    sleep 30
done