#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Get service IDs
services_resp = requests.get("https://api.render.com/v1/services", headers=headers)
services = services_resp.json()

hoistscout_services = {}
for service in services:
    if service['service']['name'].startswith('hoistscout-'):
        hoistscout_services[service['service']['name']] = service['service']['id']

print("HoistScout Services:")
for name, sid in hoistscout_services.items():
    print(f"  {name}: {sid}")

print("\nMonitoring deployments...")
print("-" * 80)

# Monitor deployments
while True:
    all_live = True
    
    for name, service_id in hoistscout_services.items():
        # Get latest deploy
        deploys_resp = requests.get(
            f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
            headers=headers
        )
        deploys = deploys_resp.json()
        
        if deploys:
            deploy = deploys[0]
            status = deploy.get('status', 'unknown')
            created = deploy.get('createdAt', '')
            commit = deploy.get('commit', {}).get('message', '').split('\n')[0][:50]
            
            # Status emoji
            emoji = {
                'live': '✅',
                'build_in_progress': '🔨',
                'update_in_progress': '🔄',
                'deactivated': '❌',
                'build_failed': '🔴',
                'update_failed': '🔴',
                'canceled': '⚠️'
            }.get(status, '❓')
            
            print(f"{emoji} {name:<20} {status:<20} {created[:19]} {commit}")
            
            if status not in ['live', 'deactivated']:
                all_live = False
        else:
            print(f"❓ {name:<20} No deploys found")
            all_live = False
    
    print("-" * 80)
    
    if all_live:
        print("\n✅ All services deployed successfully!")
        break
    
    time.sleep(10)  # Check every 10 seconds
    print("\033[F" * (len(hoistscout_services) + 2))  # Move cursor up to overwrite

print("\nChecking worker status...")
time.sleep(5)

# Check if jobs are being processed
login_resp = requests.post(
    "https://hoistscout-api.onrender.com/api/auth/login",
    data={"username": "demo", "password": "demo123"}
)

if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    jobs_resp = requests.get(
        "https://hoistscout-api.onrender.com/api/scraping/jobs?limit=10",
        headers=headers
    )
    
    if jobs_resp.status_code == 200:
        jobs = jobs_resp.json()
        
        # Count job statuses
        status_counts = {}
        for job in jobs:
            status = job.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nJob Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Check if any are running
        running = [j for j in jobs if j.get('status') == 'running']
        if running:
            print(f"\n✅ Worker is processing! {len(running)} jobs running")
        else:
            print("\n⚠️  No jobs currently running - worker may still be starting up")