#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import time

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Service IDs for hoistscout services
HOISTSCOUT_SERVICES = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g", 
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g"
}

def update_service_repo(service_id, service_name):
    """Update service repository to hoistscout"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    # First, get current service details
    get_response = requests.get(url, headers=headers)
    
    if get_response.status_code != 200:
        print(f"❌ Failed to get {service_name} details: {get_response.status_code}")
        return False
    
    current_data = get_response.json()
    
    # Update the repository URL
    update_data = {
        "repo": "https://github.com/jakelindsay87/hoistscout",
        "branch": "main",
        "autoDeploy": True
    }
    
    print(f"\n📝 Updating {service_name}...")
    print(f"   From: {current_data.get('repo', 'Unknown')}")
    print(f"   To: {update_data['repo']}")
    
    # Send update request
    patch_response = requests.patch(url, headers=headers, json=update_data)
    
    if patch_response.status_code == 200:
        print(f"✅ Successfully updated {service_name}")
        return True
    else:
        print(f"❌ Failed to update {service_name}: {patch_response.status_code}")
        print(f"   Error: {patch_response.text}")
        return False

def resume_service(service_id, service_name):
    """Resume a suspended service"""
    url = f"{RENDER_API_BASE}/services/{service_id}/resume"
    
    print(f"\n▶️  Resuming {service_name}...")
    
    response = requests.post(url, headers=headers)
    
    if response.status_code in [200, 201, 204]:
        print(f"✅ Successfully resumed {service_name}")
        return True
    else:
        print(f"❌ Failed to resume {service_name}: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def trigger_deploy(service_id, service_name):
    """Trigger a new deployment"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    
    print(f"\n🚀 Triggering deployment for {service_name}...")
    
    deploy_data = {
        "clearCache": "clear"
    }
    
    response = requests.post(url, headers=headers, json=deploy_data)
    
    if response.status_code in [200, 201]:
        deploy = response.json()
        deploy_id = deploy.get('id', 'Unknown')
        print(f"✅ Deployment triggered for {service_name}")
        print(f"   Deploy ID: {deploy_id}")
        return True
    else:
        print(f"❌ Failed to trigger deployment for {service_name}: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def get_service_status(service_id, service_name):
    """Check current service status"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        suspended = service.get('suspended', 'unknown')
        repo = service.get('repo', 'Unknown')
        
        return {
            'suspended': suspended,
            'repo': repo,
            'name': service_name
        }
    return None

def main():
    print(f"Render Service Update Script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # First, check current status
    print("\n📊 Current Service Status:")
    print("-" * 40)
    
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        status = get_service_status(service_id, service_name)
        if status:
            suspended_status = "SUSPENDED" if status['suspended'] == 'suspended' else "ACTIVE"
            print(f"{service_name}: {suspended_status} - Repo: {status['repo']}")
    
    # Update repositories
    print("\n\n🔄 Step 1: Updating Repositories")
    print("=" * 80)
    
    update_results = {}
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        update_results[service_name] = update_service_repo(service_id, service_name)
        time.sleep(1)  # Rate limiting
    
    # Resume services
    print("\n\n▶️  Step 2: Resuming Services")
    print("=" * 80)
    
    resume_results = {}
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        resume_results[service_name] = resume_service(service_id, service_name)
        time.sleep(1)  # Rate limiting
    
    # Wait a bit for services to resume
    print("\n⏳ Waiting 5 seconds for services to resume...")
    time.sleep(5)
    
    # Trigger deployments
    print("\n\n🚀 Step 3: Triggering Deployments")
    print("=" * 80)
    
    deploy_results = {}
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        deploy_results[service_name] = trigger_deploy(service_id, service_name)
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    
    print("\nRepository Updates:")
    for service, result in update_results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"  {service}: {status}")
    
    print("\nService Resumes:")
    for service, result in resume_results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"  {service}: {status}")
    
    print("\nDeployments:")
    for service, result in deploy_results.items():
        status = "✅ Success" if result else "❌ Failed"
        print(f"  {service}: {status}")
    
    print("\n\n📌 Next Steps:")
    print("1. Monitor deployments in Render dashboard")
    print("2. Check service logs after deployment completes")
    print("3. Verify services are accessible via their URLs")
    print("4. Run integration tests")

if __name__ == "__main__":
    main()