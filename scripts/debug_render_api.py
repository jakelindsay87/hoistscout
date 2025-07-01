#!/usr/bin/env python3
import requests
import json
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def debug_api_response():
    """Debug the API response structure"""
    url = f"{RENDER_API_BASE}/services"
    params = {
        "limit": 20
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\nResponse type: {type(data)}")
            
            if isinstance(data, list):
                print(f"Response is a list with {len(data)} items")
                if data:
                    print("\nFirst item structure:")
                    print(json.dumps(data[0], indent=2))
                    
                    # List all services with proper field access
                    print("\n\nAll Services:")
                    print("=" * 80)
                    for idx, item in enumerate(data):
                        if isinstance(item, dict):
                            # Check if data is nested under 'service' key
                            if 'service' in item:
                                service = item['service']
                            else:
                                service = item
                                
                            name = service.get('name', 'Unknown')
                            sid = service.get('id', 'Unknown')
                            stype = service.get('type', 'Unknown')
                            repo = service.get('repo', 'N/A')
                            suspended = service.get('suspended', False)
                            
                            print(f"\n{idx + 1}. {name}")
                            print(f"   ID: {sid}")
                            print(f"   Type: {stype}")
                            print(f"   Repo: {repo}")
                            print(f"   Status: {'SUSPENDED' if suspended else 'ACTIVE'}")
            else:
                print(f"Unexpected response format: {data}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text[:500]}")
    else:
        print(f"Error response: {response.text}")

if __name__ == "__main__":
    debug_api_response()