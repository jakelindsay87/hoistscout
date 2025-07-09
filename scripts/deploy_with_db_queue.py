#!/usr/bin/env python3
"""
Deploy HoistScout with database queue instead of Celery/Redis
"""
import os
import requests
import json
import time

RENDER_API_KEY = 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow'
RENDER_API_URL = 'https://api.render.com/v1'

# Environment variables to enable database queue
DB_QUEUE_ENV_VARS = {
    'USE_DB_QUEUE': 'true',
    'DATABASE_URL': 'postgresql://hoistscout:jN3k41MjJu7jABNnhItKwwEEOQoN3QGT@dpg-d1hlpcvnte5s73actmq0-a.oregon-postgres.render.com/hoistscout',
    'USE_GEMINI': 'true',
    'GEMINI_API_KEY': 'AIzaSyDsEGE0opuH5BhfQRGBzQ7mQ1UXJNdKMx0',
    'SECRET_KEY': 'hoistscout-prod-secret-key-2024',
    'ENABLE_DEMO_MODE': 'true',
    'ENVIRONMENT': 'production'
}

def update_service_env_var(service_id, key, value):
    """Update a single environment variable"""
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
        return False
    
    current_vars = response.json()
    var_exists = False
    var_id = None
    
    for var in current_vars:
        if var.get('key') == key:
            var_exists = True
            var_id = var.get('id')
            break
    
    if var_exists and var_id:
        # Update existing
        response = requests.patch(
            f'{RENDER_API_URL}/services/{service_id}/env-vars/{var_id}',
            headers=headers,
            json={'value': value}
        )
    else:
        # Create new
        response = requests.post(
            f'{RENDER_API_URL}/services/{service_id}/env-vars',
            headers=headers,
            json={'key': key, 'value': value}
        )
    
    return response.status_code in [200, 201]

def trigger_deployment(service_id):
    """Trigger a deployment"""
    headers = {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f'{RENDER_API_URL}/services/{service_id}/deploys',
        headers=headers,
        json={'clearCache': 'clear'}
    )
    
    return response.status_code in [200, 201, 202], response.json().get('id') if response.status_code in [200, 201, 202] else None

def main():
    print("=" * 80)
    print("DEPLOYING HOISTSCOUT WITH DATABASE QUEUE")
    print("=" * 80)
    print("\nThis will enable the database-based task queue instead of Celery/Redis")
    print("No Redis required - uses existing PostgreSQL database")
    
    # Service IDs
    api_service_id = 'srv-d1hltovfte5s73ad16tg'
    worker_service_id = 'srv-d1hlvanfte5s73ad476g'
    
    print("\n1. Updating API service environment variables...")
    api_success = 0
    for key, value in DB_QUEUE_ENV_VARS.items():
        if update_service_env_var(api_service_id, key, value):
            print(f"   ✅ {key}")
            api_success += 1
        else:
            print(f"   ❌ {key}")
    
    print(f"\n   Updated {api_success}/{len(DB_QUEUE_ENV_VARS)} variables")
    
    print("\n2. Updating Worker service environment variables...")
    worker_success = 0
    for key, value in DB_QUEUE_ENV_VARS.items():
        if update_service_env_var(worker_service_id, key, value):
            print(f"   ✅ {key}")
            worker_success += 1
        else:
            print(f"   ❌ {key}")
    
    print(f"\n   Updated {worker_success}/{len(DB_QUEUE_ENV_VARS)} variables")
    
    print("\n3. Triggering deployments...")
    api_deploy_success, api_deploy_id = trigger_deployment(api_service_id)
    if api_deploy_success:
        print(f"   ✅ API deployment triggered: {api_deploy_id}")
    else:
        print("   ❌ API deployment failed")
    
    worker_deploy_success, worker_deploy_id = trigger_deployment(worker_service_id)
    if worker_deploy_success:
        print(f"   ✅ Worker deployment triggered: {worker_deploy_id}")
    else:
        print("   ❌ Worker deployment failed")
    
    print("\n" + "=" * 80)
    if api_deploy_success and worker_deploy_success:
        print("✅ DEPLOYMENT INITIATED SUCCESSFULLY!")
        print("\nThe database queue will handle job processing without Redis")
        print("\nNext steps:")
        print("1. Wait 3-5 minutes for deployments to complete")
        print("2. Run: python backend/verify_deployment.py")
        print("3. Monitor jobs: python scripts/monitor_jobs_simple.py --api-url https://hoistscout-api.onrender.com")
        print("\nThe worker will poll the database for jobs every 5 seconds")
    else:
        print("⚠️  Some deployments failed. Check the Render dashboard.")

if __name__ == "__main__":
    main()