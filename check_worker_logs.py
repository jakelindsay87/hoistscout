#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Worker service ID
worker_id = "srv-d1hlvanfte5s73ad476g"

print("Fetching worker logs...")
print("-" * 80)

# Get logs
logs_resp = requests.get(
    f"https://api.render.com/v1/services/{worker_id}/logs?tail=100",
    headers=headers
)

print(f"Logs API Status: {logs_resp.status_code}")

if logs_resp.status_code == 200:
    logs_text = logs_resp.text
    
    # Parse and display logs
    for line in logs_text.strip().split('\n'):
        if line.strip():
            print(line)
else:
    print(f"Error fetching logs: {logs_resp.text}")

# Also check recent deployment logs
print("\n" + "-" * 80)
print("Checking deployment build logs...")

# Get latest deployment
deploys_resp = requests.get(
    f"https://api.render.com/v1/services/{worker_id}/deploys?limit=1",
    headers=headers
)

if deploys_resp.status_code == 200:
    deploys = deploys_resp.json()
    if deploys:
        deploy_id = deploys[0]['deploy']['id']
        print(f"Latest deployment: {deploy_id}")
        
        # Get deployment logs
        deploy_logs_resp = requests.get(
            f"https://api.render.com/v1/services/{worker_id}/deploys/{deploy_id}/logs",
            headers=headers
        )
        
        if deploy_logs_resp.status_code == 200:
            deploy_logs = deploy_logs_resp.text
            print("\nDeployment logs (last 50 lines):")
            print("-" * 80)
            for line in deploy_logs.strip().split('\n')[-50:]:
                if line.strip():
                    print(line)