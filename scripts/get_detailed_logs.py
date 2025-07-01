#!/usr/bin/env python3
import requests
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

# Latest deploy IDs
LATEST_DEPLOYS = {
    "hoistscout-api": {
        "service_id": "srv-d1hltovfte5s73ad16tg",
        "deploy_id": "dep-d1hns4ripnbc73fbkn4g"
    },
    "hoistscout-frontend": {
        "service_id": "srv-d1hlum6r433s73avdn6g",
        "deploy_id": "dep-d1hns6buibrs73fil2f0"
    },
    "hoistscout-worker": {
        "service_id": "srv-d1hlvanfte5s73ad476g",
        "deploy_id": "dep-d1hns7er433s73b33bdg"
    }
}

def get_full_deploy_logs(service_id, deploy_id, service_name):
    """Get complete deployment logs"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}/logs"
    
    print(f"\n{'='*80}")
    print(f"{service_name.upper()} - Deploy Logs")
    print(f"Deploy ID: {deploy_id}")
    print(f"{'='*80}")
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        all_lines = []
        error_lines = []
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                all_lines.append(decoded)
                
                # Identify key error messages
                lower_line = decoded.lower()
                if any(keyword in lower_line for keyword in ['error:', 'failed', 'fatal', 'cannot find', 'no such', 'unable', 'exception']):
                    error_lines.append(decoded)
        
        # Show key errors first
        if error_lines:
            print("\n🚨 KEY ERRORS:")
            print("-" * 60)
            for error in error_lines:
                print(error)
        
        # Show build context (first 30 and last 30 lines)
        print("\n📜 BUILD CONTEXT (First 30 lines):")
        print("-" * 60)
        for line in all_lines[:30]:
            print(line)
        
        print("\n📜 BUILD CONTEXT (Last 30 lines):")
        print("-" * 60)
        for line in all_lines[-30:]:
            print(line)
        
        # Analyze the issue
        print("\n🔍 ISSUE ANALYSIS:")
        print("-" * 60)
        
        # Check for common issues
        full_log = '\n'.join(all_lines).lower()
        
        if 'repository not found' in full_log or 'could not read from remote' in full_log:
            print("❌ REPOSITORY ISSUE: Cannot clone from GitHub")
            print("   - The repository might still be pointing to 'hoistscraper'")
            print("   - Or the repository might be private and needs authentication")
            
        elif 'no such file or directory' in full_log and 'dockerfile' in full_log:
            print("❌ DOCKERFILE ISSUE: Cannot find Dockerfile at specified path")
            print("   - Check that Dockerfile exists at the path specified in render.yaml")
            
        elif 'requirements.txt' in full_log and 'no such file' in full_log:
            print("❌ REQUIREMENTS ISSUE: Cannot find requirements.txt")
            print("   - Ensure requirements.txt exists in the correct location")
            
        elif 'modulenotfounderror' in full_log or 'importerror' in full_log:
            print("❌ DEPENDENCY ISSUE: Python module import failed")
            print("   - Check that all required packages are in requirements.txt")
            
        elif 'permission denied' in full_log:
            print("❌ PERMISSION ISSUE: Cannot access required resources")
            print("   - Check file permissions in the repository")
            
        else:
            print("❓ UNKNOWN ISSUE: Review the error messages above")
    else:
        print(f"❌ Failed to get logs: {response.status_code}")

def main():
    print(f"Detailed Deployment Logs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    for service_name, deploy_info in LATEST_DEPLOYS.items():
        get_full_deploy_logs(
            deploy_info['service_id'],
            deploy_info['deploy_id'],
            service_name
        )
    
    print("\n\n" + "=" * 100)
    print("📌 RECOMMENDED ACTIONS:")
    print("=" * 100)
    print("\n1. Check repository settings in Render dashboard")
    print("2. Ensure GitHub repository is public or Render has access")
    print("3. Verify all required files are pushed to GitHub")
    print("4. Check that Dockerfile paths match render.yaml configuration")

if __name__ == "__main__":
    main()