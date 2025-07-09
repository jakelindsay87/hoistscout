#!/usr/bin/env python3
"""
Trigger manual deployments for HoistScout services
"""
import requests
import time

RENDER_API_KEY = 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow'
RENDER_API_URL = 'https://api.render.com/v1'

services = [
    ('srv-d1hltovfte5s73ad16tg', 'hoistscout-api'),
    ('srv-d1hlvanfte5s73ad476g', 'hoistscout-worker')
]

def trigger_deployment(service_id, service_name):
    """Trigger a deployment for a service"""
    print(f"\nTriggering deployment for {service_name}...")
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Clear build cache to ensure env vars are refreshed
    response = requests.post(
        f'{RENDER_API_URL}/services/{service_id}/deploys',
        headers=headers,
        json={'clearCache': 'clear'}
    )
    
    if response.status_code in [200, 201, 202]:
        deploy = response.json()
        print(f"✅ Deployment triggered: {deploy.get('id', 'unknown')}")
        return deploy.get('id')
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return None

def main():
    print("=" * 80)
    print("TRIGGERING HOISTSCOUT DEPLOYMENTS")
    print("=" * 80)
    
    deploy_ids = []
    for service_id, service_name in services:
        deploy_id = trigger_deployment(service_id, service_name)
        if deploy_id:
            deploy_ids.append((service_name, deploy_id))
    
    print("\n" + "=" * 80)
    if deploy_ids:
        print("✅ Deployments triggered successfully!")
        print("\nDeployment IDs:")
        for name, deploy_id in deploy_ids:
            print(f"  - {name}: {deploy_id}")
        print("\nMonitor progress at:")
        print("  https://dashboard.render.com/")
        print("\nWait 3-5 minutes for deployments to complete.")
    else:
        print("❌ Failed to trigger deployments")

if __name__ == "__main__":
    main()