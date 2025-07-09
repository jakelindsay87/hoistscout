#!/usr/bin/env python3
"""Monitor deployment and job processing"""
import requests
import time
import json
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"
API_URL = "https://hoistscout-api.onrender.com"

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

def check_deployment():
    """Check worker deployment status"""
    deploys_response = requests.get(
        f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1",
        headers=headers
    )
    if deploys_response.status_code == 200:
        deploys = deploys_response.json()
        if deploys:
            latest = deploys[0]
            status = latest.get("deploy", {}).get("status")
            return status
    return None

def check_jobs():
    """Check job statuses via API"""
    # Login
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "demo", "password": "demo123"},
        timeout=10
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get jobs
        jobs_response = requests.get(
            f"{API_URL}/api/scraping/jobs?limit=5",
            headers=headers,
            timeout=10
        )
        
        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            return jobs
    return []

print("Monitoring deployment and job processing...")
print("=" * 70)

# Monitor deployment
deployment_complete = False
while not deployment_complete:
    status = check_deployment()
    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Deployment: {status}", end="", flush=True)
    
    if status == "live":
        deployment_complete = True
        print("\n✅ Deployment complete!")
    elif status == "build_failed":
        print("\n❌ Build failed!")
        break
    
    time.sleep(10)

if deployment_complete:
    print("\nWaiting 30 seconds for worker to initialize...")
    time.sleep(30)
    
    # Monitor jobs
    print("\nMonitoring job statuses:")
    print("-" * 70)
    
    job_processed = False
    checks = 0
    max_checks = 30  # 5 minutes
    
    while not job_processed and checks < max_checks:
        jobs = check_jobs()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Job Status Check #{checks + 1}:")
        
        for job in jobs[:3]:  # Show top 3 jobs
            status_emoji = {
                "pending": "⏳",
                "running": "🏃",
                "completed": "✅",
                "failed": "❌"
            }.get(job['status'], "❓")
            
            print(f"  Job {job['id']}: {status_emoji} {job['status']}")
            
            if job['status'] in ['running', 'completed']:
                job_processed = True
                print(f"\n🎉 Job {job['id']} is being processed!")
                
                if job['status'] == 'completed':
                    print("✅ Job completed successfully!")
                    if job.get('stats'):
                        print(f"   Stats: {json.dumps(job['stats'], indent=2)}")
        
        if not job_processed:
            time.sleep(10)
        
        checks += 1
    
    if not job_processed:
        print("\n⚠️ No jobs processed after 5 minutes")
        print("Check worker logs at: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")
else:
    print("\n❌ Deployment did not complete successfully")