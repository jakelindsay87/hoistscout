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

def get_service_details(service_id):
    """Get detailed information about a service"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching service details: {response.status_code}")
        return None
    
    return response.json()

def get_deploys(service_id, limit=5):
    """Get recent deploys for a service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    params = {"limit": limit}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching deploys: {response.status_code}")
        return []
    
    return response.json()

def main():
    service_ids = {
        "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
        "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g",
        "hoistscout-worker": "srv-d1hlvanfte5s73ad476g",
        "hoistscout-info": "srv-d1hlrhjuibrs73fen260"
    }
    
    print(f"Render Service Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    issues_found = []
    
    for service_name, service_id in service_ids.items():
        print(f"\n{service_name.upper()}")
        print("-" * 50)
        
        # Get service details
        details = get_service_details(service_id)
        if details:
            service = details
            
            # Basic info
            print(f"Status: {'SUSPENDED' if service.get('suspended') else 'ACTIVE'}")
            print(f"Created: {service.get('createdAt', 'N/A')}")
            print(f"Updated: {service.get('updatedAt', 'N/A')}")
            print(f"Plan: {service.get('plan', 'N/A')}")
            print(f"Region: {service.get('region', 'N/A')}")
            
            if service.get('suspended'):
                issues_found.append(f"{service_name} is SUSPENDED")
            
            # Environment info
            if service.get('serviceDetails'):
                details = service['serviceDetails']
                print(f"Docker Command: {details.get('dockerCommand', 'N/A')}")
                print(f"Health Check Path: {details.get('healthCheckPath', 'N/A')}")
                
                # Check environment variables
                env_vars = details.get('envVars', [])
                print(f"Environment Variables: {len(env_vars)} configured")
                
                # Check for missing critical vars
                critical_vars = ['DATABASE_URL', 'REDIS_URL', 'SECRET_KEY']
                configured_vars = [ev['key'] for ev in env_vars]
                missing_vars = [cv for cv in critical_vars if cv not in configured_vars]
                
                if missing_vars:
                    issues_found.append(f"{service_name} missing env vars: {', '.join(missing_vars)}")
            
            # Recent deploys
            print("\nRecent Deploys:")
            deploys = get_deploys(service_id, 3)
            
            if deploys:
                for deploy in deploys[:3]:
                    deploy_data = deploy
                    status = deploy_data.get('status', 'unknown')
                    created = deploy_data.get('createdAt', 'N/A')
                    commit = deploy_data.get('commit', {})
                    
                    status_symbol = "✅" if status == "live" else "❌"
                    print(f"  {status_symbol} {status} - {created}")
                    print(f"     Commit: {commit.get('message', 'N/A')[:50]}...")
                    
                    if status in ['build_failed', 'deploy_failed', 'canceled']:
                        issues_found.append(f"{service_name} deploy failed: {status}")
            else:
                print("  No deploy history available")
                issues_found.append(f"{service_name} has no deploy history")
    
    # Summary
    print("\n" + "=" * 100)
    print("ISSUES SUMMARY")
    print("=" * 100)
    
    if issues_found:
        print("\n🚨 Issues Found:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found")
    
    print("\n📋 Recommended Actions:")
    print("  1. Resume suspended services in Render dashboard")
    print("  2. Check billing status - suspended services often indicate payment issues")
    print("  3. Verify GitHub repository connection")
    print("  4. Check environment variable configuration")
    print("  5. Review recent deploy failures if any")

if __name__ == "__main__":
    main()