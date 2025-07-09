#!/usr/bin/env python3
"""
Monitor Render deployment progress
"""
import requests
import time
import sys
from datetime import datetime

RENDER_API_KEY = 'rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow'
RENDER_API_URL = 'https://api.render.com/v1'

deployments = [
    ('dep-d1n2ij3uibrs73e2guhg', 'hoistscout-api'),
    ('dep-d1n2ijruibrs73e2gvag', 'hoistscout-worker')
]

def get_deployment_status(deploy_id):
    """Get deployment status"""
    headers = {'Authorization': f'Bearer {RENDER_API_KEY}'}
    
    # Try to get deployment status
    response = requests.get(
        f'{RENDER_API_URL}/deploys/{deploy_id}',
        headers=headers
    )
    
    if response.status_code == 200:
        deploy = response.json()
        return {
            'status': deploy.get('status', 'unknown'),
            'created_at': deploy.get('createdAt', ''),
            'finished_at': deploy.get('finishedAt', '')
        }
    return None

def monitor_deployments():
    """Monitor deployment progress"""
    print("=" * 80)
    print("MONITORING HOISTSCOUT DEPLOYMENTS")
    print("=" * 80)
    
    completed = []
    start_time = time.time()
    
    while len(completed) < len(deployments):
        print(f"\n[{int(time.time() - start_time)}s] Checking deployment status...")
        
        for deploy_id, service_name in deployments:
            if deploy_id in completed:
                continue
                
            status = get_deployment_status(deploy_id)
            
            if status:
                status_text = status['status']
                if status_text == 'live':
                    print(f"✅ {service_name}: LIVE")
                    completed.append(deploy_id)
                elif status_text in ['build_failed', 'update_failed', 'canceled']:
                    print(f"❌ {service_name}: {status_text.upper()}")
                    completed.append(deploy_id)
                else:
                    print(f"⏳ {service_name}: {status_text}")
            else:
                print(f"❓ {service_name}: Unable to get status")
        
        if len(completed) < len(deployments):
            time.sleep(30)
    
    print("\n" + "=" * 80)
    if all(deploy_id in completed for deploy_id, _ in deployments):
        print("✅ All deployments completed!")
        print("\nNow running verification...")
        time.sleep(30)  # Wait a bit for services to stabilize
        
        # Run verification
        import subprocess
        result = subprocess.run(['python', 'backend/verify_deployment.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    else:
        print("⚠️  Some deployments may have issues")

if __name__ == "__main__":
    monitor_deployments()