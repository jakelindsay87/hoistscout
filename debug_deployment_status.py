#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Get service IDs
print("Fetching services...")
services_resp = requests.get("https://api.render.com/v1/services", headers=headers)
print(f"Services API Status: {services_resp.status_code}")

if services_resp.status_code == 200:
    services = services_resp.json()
    print(f"Total services found: {len(services)}")
    
    # Debug: Print first service structure
    if services:
        print("\nFirst service structure:")
        print(json.dumps(services[0], indent=2)[:500] + "...")
    
    hoistscout_services = {}
    for service in services:
        # Check if this is the correct path
        service_data = service.get('service', service)  # Handle both nested and flat structures
        name = service_data.get('name', '')
        if name.startswith('hoistscout-'):
            hoistscout_services[name] = service_data.get('id')
    
    print(f"\nHoistScout Services Found: {len(hoistscout_services)}")
    for name, sid in hoistscout_services.items():
        print(f"  {name}: {sid}")
    
    # Check worker deployment in detail
    if 'hoistscout-worker' in hoistscout_services:
        worker_id = hoistscout_services['hoistscout-worker']
        print(f"\nChecking worker deployment details for {worker_id}...")
        
        deploys_resp = requests.get(
            f"https://api.render.com/v1/services/{worker_id}/deploys?limit=1",
            headers=headers
        )
        print(f"Deploys API Status: {deploys_resp.status_code}")
        
        if deploys_resp.status_code == 200:
            deploys = deploys_resp.json()
            print(f"Deploys found: {len(deploys)}")
            
            if deploys:
                print("\nLatest deploy structure:")
                print(json.dumps(deploys[0], indent=2))
                
                deploy = deploys[0]
                # Try different paths for status
                status = deploy.get('status') or deploy.get('deploy', {}).get('status') or 'unknown'
                print(f"\nWorker deployment status: {status}")
else:
    print(f"Error fetching services: {services_resp.text}")