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

def get_owner_id():
    """Get the owner ID (user/team) for creating services"""
    url = f"{RENDER_API_BASE}/owners"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        owners = response.json()
        if owners:
            # Use the first owner (typically the user)
            return owners[0].get('owner', {}).get('id')
    return None

def check_existing_services():
    """Check what services already exist"""
    url = f"{RENDER_API_BASE}/services"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        services = response.json()
        print("\n📋 Existing Services:")
        print("-" * 60)
        
        for service in services:
            name = service.get('name', 'Unknown')
            repo = service.get('repo', 'N/A')
            suspended = service.get('suspended', False)
            status = "SUSPENDED" if suspended == 'suspended' else "ACTIVE"
            
            print(f"- {name}: {status} ({repo})")
        
        return services
    return []

def delete_old_service(service_id, service_name):
    """Delete an old service"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    print(f"\n🗑️  Deleting old service: {service_name}")
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print(f"✅ Successfully deleted {service_name}")
        return True
    else:
        print(f"❌ Failed to delete {service_name}: {response.status_code}")
        return False

def main():
    print(f"Render Service Management - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Get owner ID
    owner_id = get_owner_id()
    if not owner_id:
        print("❌ Could not get owner ID")
        return
    
    print(f"\n✅ Owner ID: {owner_id}")
    
    # Check existing services
    existing_services = check_existing_services()
    
    # Find problematic hoistscout services
    old_services = [s for s in existing_services if 'hoistscout' in s.get('name', '').lower() and 'hoistscraper' in s.get('repo', '')]
    
    if old_services:
        print(f"\n\n🔍 Found {len(old_services)} services with wrong repository:")
        for service in old_services:
            print(f"  - {service.get('name')} (ID: {service.get('id')})")
        
        print("\n⚠️  These services are pointing to the deleted 'hoistscraper' repository")
        print("⚠️  They cannot be updated via API due to Render limitations")
        
        print("\n\n📌 REQUIRED MANUAL ACTIONS:")
        print("=" * 60)
        print("\n1. Go to https://dashboard.render.com")
        print("2. For each hoistscout service:")
        print("   a. Click on the service")
        print("   b. Go to Settings tab")
        print("   c. Find 'Source Code' section")
        print("   d. Click 'Edit' next to GitHub repository")
        print("   e. Change repository from 'hoistscraper' to 'hoistscout'")
        print("   f. Click 'Save Changes'")
        print("   g. Click 'Manual Deploy' > 'Deploy'")
        
        print("\n\n🔗 Direct Links to Services:")
        print("-" * 40)
        for service in old_services:
            service_id = service.get('id')
            name = service.get('name')
            print(f"{name}: https://dashboard.render.com/web/{service_id}/settings")
    else:
        print("\n✅ No services found with wrong repository")
    
    # Show current hoistscout repository status
    print("\n\n📁 Checking hoistscout repository...")
    print("-" * 60)
    
    # Check if render.yaml exists
    import os
    if os.path.exists('/root/hoistscout/render.yaml'):
        print("✅ render.yaml found in hoistscout repository")
        print("\n   Services defined in render.yaml:")
        with open('/root/hoistscout/render.yaml', 'r') as f:
            import yaml
            render_config = yaml.safe_load(f)
            
            if 'services' in render_config:
                for service in render_config['services']:
                    print(f"   - {service.get('name')} ({service.get('type')})")
    else:
        print("❌ render.yaml not found")

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pyyaml"])
        import yaml
    
    main()