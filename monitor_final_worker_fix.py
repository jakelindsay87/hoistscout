#!/usr/bin/env python3
"""Monitor the final worker fix deployment"""
import requests
import time
import json
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"
API_URL = "https://hoistscout-api.onrender.com"

def monitor_deployment():
    """Monitor deployment progress"""
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}", "Accept": "application/json"}
    
    print("🚀 Monitoring Worker Fix Deployment")
    print("=" * 70)
    print("Expected improvements:")
    print("  ✓ Fixed circular import issue")
    print("  ✓ Added comprehensive startup validation")
    print("  ✓ Proper Celery app discovery")
    print("  ✓ Detailed logging throughout startup")
    print("=" * 70)
    
    # Wait for deployment
    start_time = time.time()
    while (time.time() - start_time) < 600:  # 10 min timeout
        response = requests.get(f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1", headers=headers)
        if response.status_code == 200:
            deploys = response.json()
            if deploys:
                latest = deploys[0]["deploy"]
                status = latest["status"]
                commit_msg = latest.get("commit", {}).get("message", "")
                
                if "Complete worker overhaul" in commit_msg:
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Deploy status: {status}", end="", flush=True)
                    
                    if status == "live":
                        print("\n✅ Deployment successful!")
                        print("\n📋 Check worker logs at:")
                        print(f"   https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/logs")
                        print("\nExpected log output:")
                        print("  - Environment validation")
                        print("  - Redis connection test")
                        print("  - Database connection test")
                        print("  - Registered tasks list")
                        print("  - Worker startup confirmation")
                        return True
                    elif status in ["build_failed", "update_failed"]:
                        print(f"\n❌ Deployment failed: {status}")
                        return False
        
        time.sleep(10)
    
    print("\n⏱️ Timeout waiting for deployment")
    return False

def check_job_processing():
    """Check if jobs are being processed"""
    print("\n📊 Checking Job Processing")
    print("-" * 70)
    
    # Login
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "demo", "password": "demo123"}
    )
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test job
    websites_response = requests.get(f"{API_URL}/api/websites?limit=1", headers=headers)
    if websites_response.status_code == 200 and websites_response.json():
        website = websites_response.json()[0]
        
        job_data = {
            "website_id": website['id'],
            "job_type": "test",
            "priority": 10
        }
        
        job_response = requests.post(
            f"{API_URL}/api/scraping/jobs",
            json=job_data,
            headers={**headers, "Content-Type": "application/json"}
        )
        
        if job_response.status_code == 200:
            job = job_response.json()
            job_id = job['id']
            print(f"✅ Created test job ID: {job_id}")
            
            # Monitor job
            print("\nMonitoring job status...")
            for i in range(36):  # 6 minutes
                job_response = requests.get(f"{API_URL}/api/scraping/jobs/{job_id}", headers=headers)
                if job_response.status_code == 200:
                    job = job_response.json()
                    status = job['status']
                    
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Job {job_id}: {status}", end="", flush=True)
                    
                    if status == "running":
                        print("\n🎉 JOB IS BEING PROCESSED!")
                    elif status == "completed":
                        print("\n✅ JOB COMPLETED SUCCESSFULLY!")
                        print(f"\nJob details:")
                        print(json.dumps(job, indent=2))
                        
                        # Check for opportunities
                        opps_response = requests.get(
                            f"{API_URL}/api/opportunities?website_id={website['id']}&limit=5",
                            headers=headers
                        )
                        if opps_response.status_code == 200:
                            opps = opps_response.json()
                            print(f"\n📈 Found {len(opps)} opportunities!")
                            for opp in opps[:3]:
                                print(f"  - {opp['title'][:60]}...")
                        return True
                    elif status == "failed":
                        print(f"\n❌ Job failed: {job.get('error_message', 'Unknown error')}")
                        return False
                
                time.sleep(10)
            
            print(f"\n⚠️ Job still {status} after 6 minutes")
            
    print("\n🔍 Dashboard URLs:")
    print(f"   Worker Logs: https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/logs")
    print(f"   Worker Shell: https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/shell")

if __name__ == "__main__":
    if monitor_deployment():
        time.sleep(45)  # Wait for worker to fully initialize
        check_job_processing()