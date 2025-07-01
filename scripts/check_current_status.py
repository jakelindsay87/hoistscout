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

HOISTSCOUT_SERVICES = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g", 
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g"
}

def get_service_details(service_id, service_name):
    """Get complete service details"""
    url = f"{RENDER_API_BASE}/services/{service_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        service = response.json()
        
        print(f"\n{'='*80}")
        print(f"{service_name}")
        print(f"{'='*80}")
        
        # Basic info
        print(f"ID: {service.get('id', 'N/A')}")
        print(f"Repository: {service.get('repo', 'N/A')}")
        print(f"Branch: {service.get('branch', 'N/A')}")
        print(f"Status: {service.get('suspended', 'unknown')}")
        print(f"Auto Deploy: {service.get('autoDeploy', 'N/A')}")
        
        # Service details
        if 'serviceDetails' in service:
            details = service['serviceDetails']
            print(f"\nService Details:")
            print(f"  Type: {service.get('type', 'N/A')}")
            print(f"  Runtime: {details.get('runtime', 'N/A')}")
            print(f"  Plan: {details.get('plan', 'N/A')}")
            print(f"  Region: {details.get('region', 'N/A')}")
            
            # Docker details
            if 'envSpecificDetails' in details:
                env_details = details['envSpecificDetails']
                print(f"  Dockerfile Path: {env_details.get('dockerfilePath', 'N/A')}")
                print(f"  Docker Command: {env_details.get('dockerCommand', 'N/A')}")
            
            # Environment variables
            env_vars = details.get('envVars', [])
            print(f"\nEnvironment Variables: {len(env_vars)} configured")
            if env_vars:
                for var in env_vars[:5]:  # Show first 5
                    print(f"  - {var.get('key', 'N/A')}")
                if len(env_vars) > 5:
                    print(f"  ... and {len(env_vars) - 5} more")
        
        # Get recent deploys
        get_recent_deploys(service_id, service_name)
        
        return service
    else:
        print(f"\n❌ Failed to get details for {service_name}: {response.status_code}")
    
    return None

def get_recent_deploys(service_id, service_name):
    """Get recent deployment history"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    params = {"limit": 5}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        deploys = response.json()
        
        print(f"\nRecent Deploys:")
        print("-" * 60)
        
        if deploys:
            for i, deploy in enumerate(deploys):
                status = deploy.get('status', 'unknown')
                created = deploy.get('createdAt', 'N/A')
                deploy_id = deploy.get('id', 'N/A')
                
                status_symbol = {
                    'live': '✅',
                    'build_in_progress': '🔨',
                    'update_in_progress': '🔄',
                    'build_failed': '❌',
                    'update_failed': '❌',
                    'canceled': '🚫',
                    'created': '📋'
                }.get(status, '❓')
                
                print(f"{i+1}. {status_symbol} {status} - {created}")
                print(f"   ID: {deploy_id}")
                
                # Try to get error message for failed deploys
                if status in ['build_failed', 'update_failed'] and i == 0:  # Only for most recent
                    get_deploy_error(service_id, deploy_id)
        else:
            print("  No deployment history found")

def get_deploy_error(service_id, deploy_id):
    """Try to get error message for failed deploy"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        deploy = response.json()
        if 'error' in deploy:
            print(f"   Error: {deploy['error']}")

def check_github_repo():
    """Check if GitHub repository is accessible"""
    print("\n\n📁 GitHub Repository Check")
    print("=" * 80)
    
    repo_url = "https://api.github.com/repos/jakelindsay87/hoistscout"
    
    response = requests.get(repo_url)
    
    if response.status_code == 200:
        repo = response.json()
        print(f"✅ Repository found: {repo['full_name']}")
        print(f"   Visibility: {repo['visibility']}")
        print(f"   Default branch: {repo['default_branch']}")
        print(f"   Created: {repo['created_at']}")
        print(f"   Last push: {repo['pushed_at']}")
        
        # Check for required files
        files_to_check = ['render.yaml', 'backend/Dockerfile', 'frontend/Dockerfile']
        
        print("\n📋 Checking required files:")
        for file_path in files_to_check:
            file_url = f"https://api.github.com/repos/jakelindsay87/hoistscout/contents/{file_path}"
            file_response = requests.get(file_url)
            
            if file_response.status_code == 200:
                print(f"  ✅ {file_path} - Found")
            else:
                print(f"  ❌ {file_path} - Not found")
    else:
        print(f"❌ Repository not accessible: {response.status_code}")
        if response.status_code == 404:
            print("   The repository might be private or doesn't exist")

def main():
    print(f"Current Service Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Check each service
    for service_name, service_id in HOISTSCOUT_SERVICES.items():
        get_service_details(service_id, service_name)
    
    # Check GitHub repository
    check_github_repo()
    
    # Summary and recommendations
    print("\n\n📌 ISSUE SUMMARY")
    print("=" * 80)
    print("\nBased on the analysis, the main issues appear to be:")
    print("\n1. ❌ Repository Configuration:")
    print("   - Services may still be pointing to old 'hoistscraper' repository")
    print("   - Or GitHub repository might not be accessible to Render")
    print("\n2. ❌ Missing Environment Variables:")
    print("   - No environment variables configured for services")
    print("\n3. ❌ Build Failures:")
    print("   - Deployments are failing during build phase")
    
    print("\n\n✅ REQUIRED ACTIONS:")
    print("=" * 80)
    print("\n1. Update Repository in Render Dashboard:")
    print("   - Go to each service settings")
    print("   - Change repository to: jakelindsay87/hoistscout")
    print("   - Ensure branch is set to 'master'")
    print("\n2. Configure Environment Variables:")
    print("   - Add DATABASE_URL, REDIS_URL, SECRET_KEY etc.")
    print("   - Use the values from render.yaml")
    print("\n3. Ensure GitHub Repository is Public:")
    print("   - Or add Render's deploy key to the repository")

if __name__ == "__main__":
    main()