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

def get_all_services():
    """Get all services from Render"""
    url = f"{RENDER_API_BASE}/services"
    params = {
        "limit": 20
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching services: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def get_service_logs(service_id, service_name):
    """Get logs for a specific service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/logs"
    params = {
        "tail": 50  # Get last 50 log lines
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching logs for {service_name}: {response.status_code}")
        return None
    
    return response.text  # Return raw text for logs

def main():
    print(f"\nFetching ALL Render services at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    services = get_all_services()
    
    if not services:
        print("No services found")
        return
    
    # Show all services first
    print(f"\nTotal services found: {len(services)}\n")
    
    active_services = []
    suspended_services = []
    
    for service in services:
        name = service.get('name', 'Unknown')
        service_type = service.get('type', 'Unknown')
        suspended = service.get('suspended', False)
        status = 'SUSPENDED' if suspended else 'ACTIVE'
        repo = service.get('repo', 'N/A')
        
        print(f"- {name} ({service_type}) - {status} - Repo: {repo}")
        
        if not suspended:
            active_services.append(service)
        else:
            suspended_services.append(service)
    
    print(f"\n\nActive Services: {len(active_services)}")
    print(f"Suspended Services: {len(suspended_services)}")
    
    # Now get logs for active hoistscout services
    print("\n" + "=" * 80)
    print("LOGS FOR ACTIVE HOISTSCOUT SERVICES")
    print("=" * 80)
    
    hoistscout_services = [s for s in active_services if 'hoistscout' in s.get('name', '').lower()]
    
    if not hoistscout_services:
        print("\nNo active hoistscout services found!")
        print("\nLooking for any services that might be hoistscout-related...")
        
        # Check all active services
        for service in active_services:
            print(f"\nChecking: {service.get('name')} - {service.get('repo', 'N/A')}")
    else:
        for service in hoistscout_services:
            service_id = service.get('id')
            service_name = service.get('name')
            
            print(f"\n{'='*80}")
            print(f"Service: {service_name}")
            print(f"ID: {service_id}")
            print(f"Type: {service.get('type')}")
            print(f"Repository: {service.get('repo')}")
            print(f"{'='*80}")
            
            # Get logs
            logs = get_service_logs(service_id, service_name)
            
            if logs:
                print("\nRecent logs:")
                print("-" * 80)
                print(logs)
            else:
                print("\nNo logs available")

if __name__ == "__main__":
    main()