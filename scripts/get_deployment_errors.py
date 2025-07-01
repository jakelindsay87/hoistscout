#!/usr/bin/env python3
import requests
from datetime import datetime

RENDER_API_KEY = "rnd_b0JTXMVuKeIwUfFrwXBzm0NzlzXh"
RENDER_API_BASE = "https://api.render.com/v1"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

SERVICES = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g",
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g"
}

def get_recent_deploys(service_id, service_name):
    """Get recent deployment logs with errors"""
    url = f"{RENDER_API_BASE}/services/{service_id}/deploys"
    params = {"limit": 1}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        deploys = response.json()
        if deploys:
            deploy = deploys[0]
            deploy_id = deploy.get('id')
            status = deploy.get('status')
            
            print(f"\n{'='*80}")
            print(f"{service_name.upper()} - Deploy: {deploy_id}")
            print(f"Status: {status}")
            print(f"{'='*80}")
            
            # Get deploy logs
            log_url = f"{RENDER_API_BASE}/services/{service_id}/deploys/{deploy_id}/logs"
            log_response = requests.get(log_url, headers=headers, stream=True)
            
            if log_response.status_code == 200:
                print("\nDeploy logs (showing errors and last 50 lines):")
                print("-" * 60)
                
                all_lines = []
                error_lines = []
                
                for line in log_response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        all_lines.append(decoded)
                        
                        # Capture error lines
                        lower_line = decoded.lower()
                        if any(keyword in lower_line for keyword in ['error', 'fail', 'fatal', 'could not', 'unable']):
                            error_lines.append(decoded)
                
                # Show errors first
                if error_lines:
                    print("\n🚨 ERRORS FOUND:")
                    print("-" * 40)
                    for error in error_lines[-20:]:  # Last 20 errors
                        print(error)
                
                # Show last 50 lines
                print("\n📜 LAST 50 LINES:")
                print("-" * 40)
                for line in all_lines[-50:]:
                    print(line)

def main():
    print(f"Deployment Error Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    for service_name, service_id in SERVICES.items():
        get_recent_deploys(service_id, service_name)
    
    print("\n\n" + "=" * 100)
    print("🔍 COMMON ISSUES DETECTED:")
    print("=" * 100)
    print("\n1. Repository mismatch - Services trying to clone from 'hoistscraper' which doesn't exist")
    print("2. Missing Dockerfile or incorrect paths")
    print("3. Environment variable configuration issues")
    print("\n📌 SOLUTION: You need to manually update the repository URL in Render dashboard")
    print("   Go to each service settings and change repo from 'hoistscraper' to 'hoistscout'")

if __name__ == "__main__":
    main()