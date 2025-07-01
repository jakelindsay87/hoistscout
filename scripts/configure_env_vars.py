#!/usr/bin/env python3
import requests
import json
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Environment variables based on render.yaml
ENV_CONFIGS = {
    "hoistscout-api": {
        "service_id": "srv-d1hltovfte5s73ad16tg",
        "env_vars": [
            {"key": "REDIS_URL", "value": "redis://red-d1hljoruibrs73fe7vkg:6379"},
            {"key": "SECRET_KEY", "value": "change-this-to-random-secret-key"},
            {"key": "ENVIRONMENT", "value": "production"},
            {"key": "PYTHONUNBUFFERED", "value": "1"},
            {"key": "DATABASE_URL", "value": "postgresql://user:pass@host:5432/db"}  # Placeholder
        ]
    },
    "hoistscout-frontend": {
        "service_id": "srv-d1hlum6r433s73avdn6g",
        "env_vars": [
            {"key": "NEXT_PUBLIC_API_URL", "value": "https://hoistscout-api.onrender.com"},
            {"key": "NODE_ENV", "value": "production"},
            {"key": "NEXT_TELEMETRY_DISABLED", "value": "1"},
            {"key": "NODE_OPTIONS", "value": "--max-old-space-size=512"}
        ]
    },
    "hoistscout-worker": {
        "service_id": "srv-d1hlvanfte5s73ad476g",
        "env_vars": [
            {"key": "REDIS_URL", "value": "redis://red-d1hljoruibrs73fe7vkg:6379"},
            {"key": "PYTHONUNBUFFERED", "value": "1"},
            {"key": "DATABASE_URL", "value": "postgresql://user:pass@host:5432/db"}  # Placeholder
        ]
    }
}

def update_env_vars(service_id, service_name, env_vars):
    """Update environment variables for a service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/env-vars"
    
    print(f"\n📝 Configuring environment variables for {service_name}...")
    
    # Format env vars for API
    env_data = []
    for var in env_vars:
        env_data.append({
            "key": var["key"],
            "value": var["value"]
        })
    
    # Try to update env vars
    response = requests.put(url, headers=headers, json=env_data)
    
    if response.status_code in [200, 201, 204]:
        print(f"✅ Successfully configured {len(env_vars)} environment variables")
        for var in env_vars:
            print(f"   - {var['key']}")
        return True
    else:
        print(f"❌ Failed to update env vars: {response.status_code}")
        print(f"   Error: {response.text}")
        
        # Try alternative method - updating service
        print("\n🔄 Trying alternative method...")
        return update_service_with_env_vars(service_id, service_name, env_vars)

def update_service_with_env_vars(service_id, service_name, env_vars):
    """Update service with environment variables"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    # Get current service config
    get_response = requests.get(url, headers=headers)
    if get_response.status_code != 200:
        print(f"❌ Failed to get service config")
        return False
    
    service = get_response.json()
    
    # Update env vars in service details
    if 'serviceDetails' not in service:
        service['serviceDetails'] = {}
    
    service['serviceDetails']['envVars'] = env_vars
    
    # Update service
    patch_response = requests.patch(url, headers=headers, json={"serviceDetails": {"envVars": env_vars}})
    
    if patch_response.status_code in [200, 201, 204]:
        print(f"✅ Successfully updated service with env vars")
        return True
    else:
        print(f"❌ Alternative method also failed: {patch_response.status_code}")
        return False

def main():
    print(f"Environment Variable Configuration - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    success_count = 0
    
    for service_name, config in ENV_CONFIGS.items():
        if update_env_vars(config['service_id'], service_name, config['env_vars']):
            success_count += 1
    
    print("\n\n📊 Configuration Summary")
    print("=" * 80)
    print(f"Successfully configured: {success_count}/{len(ENV_CONFIGS)} services")
    
    if success_count < len(ENV_CONFIGS):
        print("\n⚠️  Some services could not be configured automatically")
        print("\n📋 Manual Configuration Required:")
        print("-" * 60)
        
        for service_name, config in ENV_CONFIGS.items():
            print(f"\n{service_name}:")
            print(f"Go to: https://dashboard.render.com/web/{config['service_id']}/env")
            print("Add these environment variables:")
            for var in config['env_vars']:
                print(f"  - {var['key']} = {var['value']}")
    
    print("\n\n📌 Additional Required Actions:")
    print("=" * 80)
    print("\n1. Fix Dockerfile Paths in Render Dashboard:")
    print("   - hoistscout-api: Change from './Dockerfile.hoistscout-api' to './backend/Dockerfile'")
    print("   - hoistscout-frontend: Change from './Dockerfile.hoistscout-frontend' to './frontend/Dockerfile'")
    print("   - hoistscout-worker: Change from './Dockerfile.hoistscout-worker' to './backend/Dockerfile'")
    print("\n2. Configure Database:")
    print("   - Create PostgreSQL database in Render")
    print("   - Update DATABASE_URL in api and worker services")
    print("\n3. Ensure GitHub Repository is Public:")
    print("   - Or add Render deploy key to private repository")
    print("\n4. After fixing, trigger new deployments")

if __name__ == "__main__":
    main()