import requests
import json
from datetime import datetime

API_KEY = "rnd_dBFj9wa2fqKqaeJX1RlR7owt83Q7"
headers = {"Authorization": f"Bearer {API_KEY}"}

services = {
    "hoistscout-api": "srv-d1hltovfte5s73ad16tg",
    "hoistscout-frontend": "srv-d1hlum6r433s73avdn6g", 
    "hoistscout-worker": "srv-d1hlvanfte5s73ad476g",
    "hoistscout-info": "srv-d1hlrhjuibrs73fen260"
}

print("=" * 80)
print("HOISTSCOUT DEPLOYMENT STATUS REPORT")
print("=" * 80)
print(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

for service_name, service_id in services.items():
    print(f"\n{'=' * 40}")
    print(f"SERVICE: {service_name}")
    print(f"{'=' * 40}")
    
    # Get service details
    service_url = f"https://api.render.com/v1/services/{service_id}"
    service_resp = requests.get(service_url, headers=headers)
    service_data = service_resp.json()
    
    print(f"Type: {service_data.get('type', 'N/A')}")
    print(f"Status: {service_data.get('suspended', 'N/A')}")
    
    if 'serviceDetails' in service_data:
        details = service_data['serviceDetails']
        print(f"URL: {details.get('url', 'N/A')}")
        print(f"Runtime: {details.get('runtime', 'N/A')}")
        print(f"Region: {details.get('region', 'N/A')}")
    
    # Get latest deployment
    deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=5"
    deploy_resp = requests.get(deploy_url, headers=headers)
    deploys = deploy_resp.json()
    
    if deploys:
        print(f"\nLATEST DEPLOYMENTS:")
        for i, deploy_data in enumerate(deploys[:3]):
            deploy = deploy_data.get('deploy', {})
            print(f"\n  Deployment #{i+1}:")
            print(f"  - Status: {deploy.get('status', 'N/A')}")
            print(f"  - Created: {deploy.get('createdAt', 'N/A')}")
            print(f"  - Finished: {deploy.get('finishedAt', 'N/A')}")
            
            commit = deploy.get('commit', {})
            if commit:
                msg = commit.get('message', 'N/A')
                print(f"  - Commit: {msg[:60]}..." if len(msg) > 60 else f"  - Commit: {msg}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
