#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import time

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

# Deploy IDs from the previous run
DEPLOY_IDS = {
    "hoistscout-api": {
        "service_id": "srv-d1hltovfte5s73ad16tg",
        "deploy_id": "dep-d1hnjojuibrs73fi4ek0"
    },
    "hoistscout-frontend": {
        "service_id": "srv-d1hlum6r433s73avdn6g",
        "deploy_id": "dep-d1hnjpjipnbc73fb3i6g"
    },
    "hoistscout-worker": {
        "service_id": "srv-d1hlvanfte5s73ad476g",
        "deploy_id": "dep-d1hnjqffte5s73ag98n0"
    }
}

def get_deploy_status(service_id, deploy_id):
    """Get deployment status"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        deploy = response.json()
        return {
            'status': deploy.get('status', 'unknown'),
            'createdAt': deploy.get('createdAt', 'N/A'),
            'finishedAt': deploy.get('finishedAt', 'N/A'),
            'commit': deploy.get('commit', {})
        }
    return None

def get_deploy_logs(service_id, deploy_id, service_name):
    """Get deployment logs"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}/logs"
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        print(f"\n📜 Deploy logs for {service_name}:")
        print("-" * 60)
        
        line_count = 0
        last_lines = []
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                last_lines.append(decoded_line)
                if len(last_lines) > 50:  # Keep last 50 lines
                    last_lines.pop(0)
                line_count += 1
        
        # Show last 30 lines
        for line in last_lines[-30:]:
            print(line)
        
        print(f"\n(Showing last 30 of {line_count} total lines)")
        return True
    return False

def main():
    print(f"Deployment Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_complete = False
    check_count = 0
    max_checks = 30  # Max 5 minutes (30 * 10 seconds)
    
    while not all_complete and check_count < max_checks:
        check_count += 1
        print(f"\n🔍 Check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        statuses = {}
        
        for service_name, info in DEPLOY_IDS.items():
            status = get_deploy_status(info['service_id'], info['deploy_id'])
            
            if status:
                statuses[service_name] = status
                
                status_symbol = {
                    'live': '✅',
                    'build_in_progress': '🔨',
                    'update_in_progress': '🔄',
                    'build_failed': '❌',
                    'update_failed': '❌',
                    'canceled': '🚫',
                    'created': '📋'
                }.get(status['status'], '❓')
                
                print(f"{service_name}: {status_symbol} {status['status']}")
                
                # If failed, show logs
                if status['status'] in ['build_failed', 'update_failed']:
                    get_deploy_logs(info['service_id'], info['deploy_id'], service_name)
            else:
                print(f"{service_name}: ❓ Unable to get status")
        
        # Check if all are complete
        all_statuses = [s['status'] for s in statuses.values()]
        complete_statuses = ['live', 'build_failed', 'update_failed', 'canceled']
        all_complete = all([status in complete_statuses for status in all_statuses])
        
        if not all_complete and check_count < max_checks:
            print("\n⏳ Waiting 10 seconds before next check...")
            time.sleep(10)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("📊 FINAL DEPLOYMENT STATUS")
    print("=" * 80)
    
    for service_name, info in DEPLOY_IDS.items():
        status = get_deploy_status(info['service_id'], info['deploy_id'])
        
        if status:
            if status['status'] == 'live':
                print(f"\n✅ {service_name}: DEPLOYED SUCCESSFULLY")
            else:
                print(f"\n❌ {service_name}: DEPLOYMENT FAILED - {status['status']}")
                # Show logs for failed deployments
                get_deploy_logs(info['service_id'], info['deploy_id'], service_name)
    
    # Get service URLs
    print("\n\n🌐 Service URLs:")
    print("-" * 40)
    
    for service_name, info in DEPLOY_IDS.items():
        service_url = f"{RENDER_API_BASE}/services/{info['service_id']}"
        response = requests.get(service_url, headers=headers)
        
        if response.status_code == 200:
            service = response.json()
            if 'serviceDetails' in service and 'url' in service['serviceDetails']:
                url = service['serviceDetails']['url']
                print(f"{service_name}: {url}")

if __name__ == "__main__":
    main()