#!/usr/bin/env python3
"""
Update all required environment variables for HoistScout services on Render
"""
import os
import requests
import json

RENDER_API_KEY = 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow'
RENDER_API_URL = 'https://api.render.com/v1'

# Get Redis URL from our previous setup
with open('/tmp/redis_url.txt', 'r') as f:
    REDIS_URL = f.read().strip()

# Environment variables for both API and Worker
ENV_VARS = {
    'REDIS_URL': REDIS_URL,
    'DATABASE_URL': 'postgresql://hoistscout:jN3k41MjJu7jABNnhItKwwEEOQoN3QGT@dpg-d1hlpcvnte5s73actmq0-a.oregon-postgres.render.com/hoistscout',
    'USE_GEMINI': 'true',
    'GEMINI_API_KEY': 'AIzaSyDsEGE0opuH5BhfQRGBzQ7mQ1UXJNdKMx0',  # Demo key
    'SECRET_KEY': 'hoistscout-prod-secret-key-2024',
    'ENABLE_DEMO_MODE': 'true',
    'ENVIRONMENT': 'production'
}

# Services to update
SERVICES = [
    ('srv-d1hltovfte5s73ad16tg', 'hoistscout-api'),
    ('srv-d1hlvanfte5s73ad476g', 'hoistscout-worker')
]

def update_service_env_vars(service_id, service_name):
    """Update all environment variables for a service"""
    print(f"\n{'='*60}")
    print(f"Updating {service_name} (ID: {service_id})")
    print('='*60)
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Get current env vars
    response = requests.get(
        f'{RENDER_API_URL}/services/{service_id}/env-vars',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get current env vars: {response.status_code}")
        return False
    
    current_vars = response.json()
    current_keys = {var.get('key'): var.get('id') for var in current_vars}
    
    success_count = 0
    
    for key, value in ENV_VARS.items():
        if key in current_keys:
            # Update existing variable
            var_id = current_keys[key]
            update_response = requests.patch(
                f'{RENDER_API_URL}/services/{service_id}/env-vars/{var_id}',
                headers=headers,
                json={'value': value}
            )
            if update_response.status_code == 200:
                print(f"  ✅ Updated {key}")
                success_count += 1
            else:
                print(f"  ❌ Failed to update {key}: {update_response.status_code}")
        else:
            # Create new variable
            create_response = requests.post(
                f'{RENDER_API_URL}/services/{service_id}/env-vars',
                headers=headers,
                json={'key': key, 'value': value}
            )
            if create_response.status_code in [200, 201]:
                print(f"  ✅ Created {key}")
                success_count += 1
            else:
                print(f"  ❌ Failed to create {key}: {create_response.status_code}")
    
    print(f"\nUpdated {success_count}/{len(ENV_VARS)} environment variables")
    return success_count == len(ENV_VARS)

def trigger_deployment(service_id, service_name):
    """Trigger a deployment for a service"""
    print(f"\nTriggering deployment for {service_name}...")
    
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f'{RENDER_API_URL}/services/{service_id}/deploys',
        headers=headers,
        json={'clearCache': 'clear'}
    )
    
    if response.status_code in [200, 201, 202]:
        deploy = response.json()
        print(f"✅ Deployment triggered: {deploy.get('id', 'unknown')}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False

def main():
    print("=" * 80)
    print("UPDATING ALL HOISTSCOUT ENVIRONMENT VARIABLES")
    print("=" * 80)
    print("\nEnvironment variables to set:")
    for key, value in ENV_VARS.items():
        if 'KEY' in key or 'PASSWORD' in value:
            display_value = value[:10] + '...'
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value
        print(f"  {key}: {display_value}")
    
    all_success = True
    
    for service_id, service_name in SERVICES:
        if not update_service_env_vars(service_id, service_name):
            all_success = False
        else:
            # Trigger deployment if env vars updated successfully
            trigger_deployment(service_id, service_name)
    
    print("\n" + "=" * 80)
    if all_success:
        print("✅ All services updated successfully!")
        print("\nNEXT STEPS:")
        print("1. Wait 3-5 minutes for deployments to complete")
        print("2. Monitor deployment progress at https://dashboard.render.com/")
        print("3. Run: python backend/verify_deployment.py")
        print("4. Check job processing: python scripts/monitor_jobs_simple.py --api-url https://hoistscout-api.onrender.com")
    else:
        print("⚠️  Some updates failed. Check the Render dashboard for details.")

if __name__ == "__main__":
    main()