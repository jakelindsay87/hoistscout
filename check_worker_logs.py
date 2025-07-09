#!/usr/bin/env python3
"""Check worker deployment and recent logs"""
import requests
import json
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Checking HoistScout Worker Status...")
print("=" * 60)

# Get latest deployment
deploys_response = requests.get(
    f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1",
    headers=headers
)
deploys = deploys_response.json()

if deploys:
    latest = deploys[0]
    status = latest.get("deploy", {}).get("status")
    created = latest.get("deploy", {}).get("createdAt")
    commit = latest.get("deploy", {}).get("commit", {}).get("message", "N/A")
    
    # Status emoji
    status_emoji = {
        "live": "✅",
        "build_failed": "❌",
        "deactivated": "⚠️",
        "building": "🔨",
        "deploying": "🚀"
    }.get(status, "❓")
    
    print(f"Latest Deployment: {status_emoji} {status}")
    print(f"Created: {created}")
    print(f"Commit: {commit[:60]}...")
    
print("\n" + "=" * 60)
print("Worker Dashboard URL:")
print("https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")
print("\nTo view live logs:")
print("1. Click the link above")
print("2. Go to the 'Logs' tab")
print("3. Look for output from start_worker.py")
print("\nExpected debug output:")
print("- Environment variables (Redis, Database, Gemini)")
print("- Redis connection test")
print("- Database connection test")
print("- Celery configuration")
print("- Worker startup status")