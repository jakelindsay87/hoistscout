#!/usr/bin/env python3
"""Check deployment status once and exit"""
import requests
import json
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Checking HoistScout deployment status...")
print("=" * 60)

# Get all services
response = requests.get(f"{RENDER_API_URL}/services", headers=headers)
services = response.json()

# Find our services
if isinstance(services, list):
    service_list = services
else:
    service_list = services.get("services", [])

for service in service_list:
    if "hoistscout" in service.get("name", "").lower():
        name = service["name"]
        service_type = service["type"]
        
        # Get deployments
        service_id = service["id"]
        deploys_response = requests.get(
            f"{RENDER_API_URL}/services/{service_id}/deploys?limit=1",
            headers=headers
        )
        deploys = deploys_response.json()
        
        print(f"\n📦 {name} ({service_type})")
        print(f"   Status: {service.get('suspended', 'unknown')}")
        
        if deploys:
            latest = deploys[0]
            status = latest["status"]
            created = datetime.fromisoformat(latest["createdAt"].replace("Z", "+00:00"))
            
            # Status emoji
            if status == "live":
                emoji = "✅"
            elif status == "build_failed":
                emoji = "❌"
            elif status in ["building", "deploying"]:
                emoji = "🔄"
            else:
                emoji = "⚠️"
            
            print(f"   Latest Deploy: {emoji} {status}")
            print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # For worker, check if it's processing
            if "worker" in name.lower() and status == "live":
                print(f"   🔍 Worker is deployed - check Render dashboard logs to see debug output")

print("\n" + "=" * 60)
print("To view worker logs:")
print("1. Go to: https://dashboard.render.com/")
print("2. Click on 'hoistscout-worker' service")
print("3. Click on 'Logs' tab")
print("4. Look for the debug output from start_worker.py")