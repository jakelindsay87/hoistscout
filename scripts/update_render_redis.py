#!/usr/bin/env python3
"""
Update Render services with Redis URL
"""
import os
import sys
import requests
import json
from datetime import datetime

# Render API configuration
RENDER_API_KEY = os.getenv('RENDER_API_KEY', 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow')
RENDER_API_URL = 'https://api.render.com/v1'

def get_headers():
    """Get API headers"""
    return {
        'Authorization': f'Bearer {RENDER_API_KEY}',
        'Content-Type': 'application/json'
    }

def list_services():
    """List all services"""
    print("\nFetching services from Render...")
    response = requests.get(f'{RENDER_API_URL}/services', headers=get_headers())
    
    if response.status_code == 200:
        services = response.json()
        print(f"Found {len(services)} services")
        return services
    else:
        print(f"Failed to list services: {response.status_code}")
        return []

def update_env_vars(service_id, service_name, redis_url):
    """Update environment variables for a service"""
    print(f"\nUpdating {service_name} (ID: {service_id})...")
    
    # Get current env vars
    response = requests.get(
        f'{RENDER_API_URL}/services/{service_id}/env-vars',
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print(f"  ❌ Failed to get current env vars: {response.status_code}")
        return False
    
    current_vars = response.json()
    
    # Check if REDIS_URL already exists
    redis_var_exists = any(var.get('key') == 'REDIS_URL' for var in current_vars)
    
    if redis_var_exists:
        # Update existing variable
        for var in current_vars:
            if var.get('key') == 'REDIS_URL':
                var_id = var.get('id')
                update_response = requests.patch(
                    f'{RENDER_API_URL}/services/{service_id}/env-vars/{var_id}',
                    headers=get_headers(),
                    json={'value': redis_url}
                )
                if update_response.status_code == 200:
                    print(f"  ✅ Updated REDIS_URL")
                    return True
                else:
                    print(f"  ❌ Failed to update REDIS_URL: {update_response.status_code}")
                    return False
    else:
        # Create new variable
        create_response = requests.post(
            f'{RENDER_API_URL}/services/{service_id}/env-vars',
            headers=get_headers(),
            json={'key': 'REDIS_URL', 'value': redis_url}
        )
        if create_response.status_code in [200, 201]:
            print(f"  ✅ Created REDIS_URL")
            return True
        else:
            print(f"  ❌ Failed to create REDIS_URL: {create_response.status_code}")
            return False
    
    return False

def restart_service(service_id, service_name):
    """Restart a service to pick up new env vars"""
    print(f"  Restarting {service_name}...")
    
    response = requests.post(
        f'{RENDER_API_URL}/services/{service_id}/deploys',
        headers=get_headers(),
        json={'clearCache': False}
    )
    
    if response.status_code in [200, 201]:
        deploy = response.json()
        print(f"  ✅ Deployment triggered: {deploy.get('id')}")
        return True
    else:
        print(f"  ❌ Failed to restart service: {response.status_code}")
        return False

def main():
    """Main function"""
    # Get Redis URL from command line or environment
    redis_url = None
    if len(sys.argv) > 1:
        redis_url = sys.argv[1]
    else:
        redis_url = os.getenv('REDIS_URL')
    
    if not redis_url:
        print("Error: Please provide Redis URL as argument or set REDIS_URL environment variable")
        print("\nUsage:")
        print("  python update_render_redis.py redis://default:password@host:port")
        print("  REDIS_URL=redis://... python update_render_redis.py")
        sys.exit(1)
    
    print("=" * 80)
    print("RENDER REDIS CONFIGURATION UPDATE")
    print("=" * 80)
    print(f"Redis URL: {redis_url[:30]}...")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # List services
    services = list_services()
    if not services:
        print("\nNo services found!")
        return
    
    # Find HoistScout services
    hoistscout_services = []
    for service in services:
        service_data = service.get('service', {})
        name = service_data.get('name', '').lower()
        if 'hoistscout' in name and name.endswith(('-api', '-worker')):
            hoistscout_services.append({
                'id': service_data.get('id'),
                'name': service_data.get('name'),
                'type': service_data.get('type'),
                'status': service_data.get('suspended') and 'suspended' or 'active'
            })
    
    print(f"\nFound {len(hoistscout_services)} HoistScout services to update:")
    for svc in hoistscout_services:
        print(f"  - {svc['name']} ({svc['type']}) - {svc['status']}")
    
    if not hoistscout_services:
        print("\nNo HoistScout API or Worker services found!")
        return
    
    # Update each service
    print("\nUpdating services...")
    updated_count = 0
    for service in hoistscout_services:
        if update_env_vars(service['id'], service['name'], redis_url):
            updated_count += 1
            # Only restart if update was successful
            restart_service(service['id'], service['name'])
    
    print("\n" + "=" * 80)
    print(f"UPDATE COMPLETE: {updated_count}/{len(hoistscout_services)} services updated")
    print("=" * 80)
    
    if updated_count == len(hoistscout_services):
        print("\n✅ All services updated successfully!")
        print("\nNext steps:")
        print("1. Wait 2-3 minutes for services to restart")
        print("2. Check health endpoints:")
        print("   - https://hoistscout-api.onrender.com/api/health")
        print("   - https://hoistscout-api.onrender.com/api/health/redis")
        print("3. Run verification script:")
        print("   python backend/verify_deployment.py")
    else:
        print("\n⚠️  Some services failed to update. Check logs for details.")

if __name__ == "__main__":
    main()