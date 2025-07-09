#!/usr/bin/env python3
"""Debug deployment status check"""
import requests
import json

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Debugging Render API...")

# Get all services
response = requests.get(f"{RENDER_API_URL}/services", headers=headers)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
    
    if isinstance(data, list):
        services = data
    else:
        services = data.get("services", [])
    
    print(f"\nFound {len(services)} services")
    
    # Show first service structure
    if services:
        print(f"\nFirst service structure:")
        print(json.dumps(services[0], indent=2))
    
    # Show all hoistscout services
    print("\n=== HoistScout Services ===")
    for service in services:
        if isinstance(service, dict):
            # Try different possible structures
            name = service.get('service', {}).get('name') or service.get('name', '')
            if 'hoistscout' in name.lower():
                print(f"\nService: {name}")
                print(f"  Full data: {json.dumps(service, indent=2)}")
        else:
            print(f"Unexpected service type: {type(service)}")
else:
    print(f"Error: {response.text}")