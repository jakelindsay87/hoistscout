#!/usr/bin/env python3
"""
Update Render environment variables using the correct API endpoints
"""
import os
import sys
import requests
import json
import time

RENDER_API_KEY = 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow'
RENDER_API_URL = 'https://api.render.com/v1'

def update_service_env(service_id, env_vars):
    """Update service environment variables using the correct endpoint"""
    print(f"\nUpdating service {service_id}...")
    
    # First, get the service details
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Accept': 'application/json'
    }
    
    # Get service info
    service_resp = requests.get(
        f'{RENDER_API_URL}/services/{service_id}',
        headers=headers
    )
    
    if service_resp.status_code != 200:
        print(f"Failed to get service info: {service_resp.status_code}")
        return False
    
    service_data = service_resp.json()
    print(f"Service name: {service_data.get('name', 'Unknown')}")
    
    # Update environment variables by triggering a new deployment with env vars
    deploy_data = {
        'clearCache': False
    }
    
    # For Render, we need to update the service's environment variables
    # This is done through the service update endpoint
    update_data = {
        'envVars': env_vars
    }
    
    update_resp = requests.patch(
        f'{RENDER_API_URL}/services/{service_id}',
        headers={**headers, 'Content-Type': 'application/json'},
        json=update_data
    )
    
    if update_resp.status_code == 200:
        print("✅ Environment variables updated")
        
        # Trigger a new deployment
        deploy_resp = requests.post(
            f'{RENDER_API_URL}/services/{service_id}/deploys',
            headers={**headers, 'Content-Type': 'application/json'},
            json=deploy_data
        )
        
        if deploy_resp.status_code in [200, 201]:
            print("✅ Deployment triggered")
            return True
        else:
            print(f"⚠️  Failed to trigger deployment: {deploy_resp.status_code}")
            return True  # Env vars still updated
    else:
        print(f"❌ Failed to update env vars: {update_resp.status_code}")
        print(f"Response: {update_resp.text}")
        return False

def main():
    redis_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv('REDIS_URL')
    
    if not redis_url:
        print("Usage: python update_render_env.py <redis_url>")
        sys.exit(1)
    
    print("=" * 80)
    print("UPDATING RENDER SERVICES WITH REDIS URL")
    print("=" * 80)
    print(f"Redis URL: {redis_url[:30]}...")
    
    # Service IDs from previous output
    services = [
        ('srv-d1hltovfte5s73ad16tg', 'hoistscout-api'),
        ('srv-d1hlvanfte5s73ad476g', 'hoistscout-worker')
    ]
    
    # Environment variables to set
    env_vars = [
        {'key': 'REDIS_URL', 'value': redis_url}
    ]
    
    success_count = 0
    for service_id, service_name in services:
        print(f"\n{'='*40}")
        print(f"Service: {service_name}")
        if update_service_env(service_id, env_vars):
            success_count += 1
    
    print("\n" + "=" * 80)
    print(f"COMPLETE: {success_count}/{len(services)} services updated")
    
    if success_count == len(services):
        print("\n✅ All services updated successfully!")
        print("\nWait 2-3 minutes for deployments to complete, then run:")
        print("  python scripts/monitor_jobs_simple.py --api-url https://hoistscout-api.onrender.com")
    else:
        print("\n⚠️  Some updates failed. Check the Render dashboard.")

if __name__ == "__main__":
    main()