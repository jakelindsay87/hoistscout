#!/usr/bin/env python3
import requests
import json
import sys
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def get_services():
    """Get all services from Render"""
    url = f"{RENDER_API_BASE}/services"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching services: {response.status_code}")
        print(response.text)
        return []
    
    services = response.json()
    hoistscout_services = [s for s in services if 'hoistscout' in s['service']['name'].lower()]
    
    return hoistscout_services

def get_service_logs(service_id, service_name):
    """Get logs for a specific service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/logs"
    params = {
        "tail": 100  # Get last 100 log lines
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching logs for {service_name}: {response.status_code}")
        return None
    
    return response.json()

def main():
    print(f"Fetching Render services at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    services = get_services()
    
    if not services:
        print("No hoistscout services found on Render")
        return
    
    print(f"Found {len(services)} hoistscout services:\n")
    
    for service in services:
        service_data = service['service']
        service_id = service_data['id']
        service_name = service_data['name']
        service_type = service_data['type']
        status = service_data.get('suspended', False)
        
        print(f"\n{'='*80}")
        print(f"Service: {service_name}")
        print(f"Type: {service_type}")
        print(f"ID: {service_id}")
        print(f"Status: {'Suspended' if status else 'Active'}")
        print(f"Repository: {service_data.get('repo', 'N/A')}")
        print(f"Branch: {service_data.get('branch', 'N/A')}")
        print(f"{'='*80}")
        
        # Get logs
        logs = get_service_logs(service_id, service_name)
        
        if logs:
            print(f"\nRecent logs:")
            print("-" * 80)
            for log_entry in logs:
                timestamp = log_entry.get('timestamp', '')
                message = log_entry.get('message', '')
                level = log_entry.get('level', '')
                
                # Format timestamp if present
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        timestamp_str = timestamp
                else:
                    timestamp_str = "N/A"
                
                # Color code by level
                if level == 'error':
                    print(f"\033[91m[{timestamp_str}] ERROR: {message}\033[0m")
                elif level == 'warning':
                    print(f"\033[93m[{timestamp_str}] WARN: {message}\033[0m")
                else:
                    print(f"[{timestamp_str}] {level.upper() if level else 'INFO'}: {message}")
        else:
            print("\nNo logs available or error fetching logs")
    
    print(f"\n{'='*80}")
    print("Log fetch complete")

if __name__ == "__main__":
    main()