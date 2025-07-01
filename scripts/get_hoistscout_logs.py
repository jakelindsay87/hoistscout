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

# Service IDs for hoistscout services
HOISTSCOUT_SERVICES = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g", 
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g"
}

def get_service_logs(service_id, service_name):
    """Get logs for a specific service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/logs"
    
    response = requests.get(url, headers=headers, stream=True)
    
    print(f"\n{'='*80}")
    print(f"Fetching logs for: {service_name}")
    print(f"Service ID: {service_id}")
    print(f"Status Code: {response.status_code}")
    print(f"{'='*80}")
    
    if response.status_code == 200:
        # Render logs come as a stream
        logs = []
        for line in response.iter_lines():
            if line:
                try:
                    log_entry = json.loads(line.decode('utf-8'))
                    logs.append(log_entry)
                except:
                    # If not JSON, just print the line
                    print(line.decode('utf-8'))
        
        if logs:
            print(f"\nFound {len(logs)} log entries:")
            print("-" * 80)
            
            # Show last 30 logs
            for entry in logs[-30:]:
                timestamp = entry.get('timestamp', 'N/A')
                message = entry.get('message', entry)
                level = entry.get('level', 'info')
                
                if isinstance(message, dict):
                    message = json.dumps(message)
                
                print(f"[{timestamp}] {level.upper()}: {message}")
        else:
            print("No structured logs found")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def get_deploy_logs(service_id, service_name):
    """Get deployment logs"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    params = {"limit": 1}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        deploys = response.json()
        if deploys:
            latest_deploy = deploys[0]
            deploy_id = latest_deploy.get('id')
            
            if deploy_id:
                print(f"\nLatest deploy ID: {deploy_id}")
                
                # Get deploy logs
                log_url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}/logs"
                log_response = requests.get(log_url, headers=headers, stream=True)
                
                if log_response.status_code == 200:
                    print("\nDeploy logs:")
                    print("-" * 80)
                    for line in log_response.iter_lines():
                        if line:
                            print(line.decode('utf-8'))

def main():
    print(f"Fetching Hoistscout Service Logs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        try:
            # Get service logs
            get_service_logs(service_id, service_name)
            
            # Try to get deploy logs
            get_deploy_logs(service_id, service_name)
            
        except Exception as e:
            print(f"\nError processing {service_name}: {e}")
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print("\n⚠️  All hoistscout services appear to be SUSPENDED")
    print("⚠️  Services are pointing to old repository: hoistscraper")
    print("\nRequired Actions:")
    print("1. Update service configurations to point to correct repository")
    print("2. Resume suspended services in Render dashboard")
    print("3. Trigger new deployments after configuration update")

if __name__ == "__main__":
    main()