#!/usr/bin/env python3
import requests
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

print("\nCurrent Deployment Status:")
print("-" * 80)

# Check deployment status once
for name, service_id in hoistscout_services.items():
    # Get latest deploy
    deploys_resp = requests.get(
        f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
        headers=headers
    )
    deploys = deploys_resp.json()
    
    if deploys:
        deploy_data = deploys[0].get('deploy', deploys[0])  # Handle nested structure
        status = deploy_data.get('status', 'unknown')
        created = deploy_data.get('createdAt', '')
        commit = deploy_data.get('commit', {}).get('message', '').split('\n')[0][:50]
        
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
        
        # For worker specifically, check logs if it's live
        if name == 'hoistscout-worker' and status == 'live':
            print(f"\n  Checking worker logs...")
            
            # Get latest logs
            logs_resp = requests.get(
                f"https://api.render.com/v1/services/{service_id}/logs",
                headers=headers
            )
            
            if logs_resp.status_code == 200:
                logs_data = logs_resp.text
                # Show last 10 lines of logs
                log_lines = logs_data.strip().split('\n')[-10:]
                print("  Recent logs:")
                for line in log_lines:
                    print(f"    {line}")
    else:
        print(f"❓ {name:<20} No deploys found")

print("-" * 80)

# Check worker health directly
print("\nChecking Worker Health...")
try:
    # Try to login first
    login_resp = requests.post(
        "https://hoistscout-api.onrender.com/api/auth/login",
        data={"username": "demo", "password": "demo123"},
        timeout=10
    )
    
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Check job status
        jobs_resp = requests.get(
            "https://hoistscout-api.onrender.com/api/scraping/jobs?limit=10",
            headers=auth_headers,
            timeout=10
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
                print("\n⚠️  No jobs currently running")
                
            # Show recent jobs
            print("\nRecent Jobs:")
            for job in jobs[:5]:
                created = job.get('created_at', 'unknown')[:19]
                status = job.get('status', 'unknown')
                error = job.get('error', '')
                print(f"  {created} - {status} {f'- {error[:50]}' if error else ''}")
        else:
            print(f"❌ Failed to get jobs: {jobs_resp.status_code}")
    else:
        print(f"❌ Failed to login: {login_resp.status_code}")
        
except Exception as e:
    print(f"❌ Error checking worker health: {str(e)}")