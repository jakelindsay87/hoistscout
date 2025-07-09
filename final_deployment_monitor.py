#!/usr/bin/env python3
"""Final deployment monitor after Docker fix"""
import requests
import time
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"
API_URL = "https://hoistscout-api.onrender.com"

print("Final Deployment Monitor")
print("=" * 60)

# Monitor deployment
headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

print("Monitoring deployment...")
deployment_complete = False
start_time = time.time()

while not deployment_complete and (time.time() - start_time) < 600:  # 10 minute timeout
    deploys_response = requests.get(
        f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1",
        headers=headers
    )
    
    if deploys_response.status_code == 200:
        deploys = deploys_response.json()
        if deploys:
            latest = deploys[0]
            status = latest.get("deploy", {}).get("status")
            created = latest.get("deploy", {}).get("createdAt", "")
            
            # Check if this is our latest deployment
            if "Force Docker rebuild" in latest.get("deploy", {}).get("commit", {}).get("message", ""):
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Status: {status}", end="", flush=True)
                
                if status == "live":
                    deployment_complete = True
                    print(f"\n✅ Deployment successful!")
                elif status in ["build_failed", "update_failed"]:
                    print(f"\n❌ Deployment failed: {status}")
                    break
    
    time.sleep(10)

if deployment_complete:
    print("\nWaiting 30 seconds for worker initialization...")
    time.sleep(30)
    
    # Check job status
    print("\nChecking existing jobs...")
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "demo", "password": "demo123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get recent jobs
        jobs_response = requests.get(
            f"{API_URL}/api/scraping/jobs?limit=5",
            headers=headers
        )
        
        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            print(f"Found {len(jobs)} recent jobs:")
            
            # Monitor for status changes
            print("\nMonitoring for job processing...")
            checks = 0
            job_processed = False
            
            while checks < 30 and not job_processed:  # 5 minutes
                jobs_response = requests.get(
                    f"{API_URL}/api/scraping/jobs?limit=5",
                    headers=headers
                )
                
                if jobs_response.status_code == 200:
                    jobs = jobs_response.json()
                    
                    for job in jobs:
                        if job['status'] in ['running', 'completed']:
                            job_processed = True
                            print(f"\n🎉 Job {job['id']} is {job['status']}!")
                            
                            if job['status'] == 'completed':
                                print("✅ SUCCESSFULLY PROCESSED A JOB!")
                                print(f"Job details: {job}")
                            break
                    
                    if not job_processed:
                        # Show current status
                        statuses = [f"{j['id']}:{j['status']}" for j in jobs[:3]]
                        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Jobs: {', '.join(statuses)}", end="", flush=True)
                
                time.sleep(10)
                checks += 1
            
            if not job_processed:
                print("\n⚠️ No jobs processed after 5 minutes")
                print("Dashboard: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")