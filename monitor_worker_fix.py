#!/usr/bin/env python3
"""Monitor worker deployment and job processing after queue fix"""
import requests
import time
import json
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"
API_URL = "https://hoistscout-api.onrender.com"

def wait_for_deployment():
    """Wait for deployment to complete"""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    
    print("Waiting for deployment to complete...")
    while True:
        deploys_response = requests.get(
            f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1",
            headers=headers
        )
        if deploys_response.status_code == 200:
            deploys = deploys_response.json()
            if deploys:
                latest = deploys[0]
                status = latest.get("deploy", {}).get("status")
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Deployment status: {status}", end="", flush=True)
                
                if status == "live":
                    print("\n✅ Deployment complete!")
                    return True
                elif status in ["build_failed", "deactivated"]:
                    print(f"\n❌ Deployment failed: {status}")
                    return False
        
        time.sleep(10)

def create_test_job():
    """Create a new test job"""
    # Login
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "demo", "password": "demo123"},
        timeout=10
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Get first website
        websites_response = requests.get(f"{API_URL}/api/websites?limit=1", headers=headers)
        if websites_response.status_code == 200:
            websites = websites_response.json()
            if websites:
                website = websites[0]
                
                # Create job
                job_data = {
                    "website_id": website['id'],
                    "job_type": "test",
                    "priority": 10  # High priority
                }
                
                job_response = requests.post(
                    f"{API_URL}/api/scraping/jobs",
                    json=job_data,
                    headers=headers
                )
                
                if job_response.status_code == 200:
                    job = job_response.json()
                    print(f"✅ Created test job ID: {job['id']}")
                    return job['id']
    
    return None

def monitor_job(job_id):
    """Monitor a specific job"""
    # Login
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data={"username": "demo", "password": "demo123"},
        timeout=10
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"\nMonitoring job {job_id}...")
        print("-" * 60)
        
        for i in range(60):  # Monitor for up to 10 minutes
            # Get job status
            job_response = requests.get(
                f"{API_URL}/api/scraping/jobs/{job_id}",
                headers=headers
            )
            
            if job_response.status_code == 200:
                job = job_response.json()
                status = job['status']
                
                status_emoji = {
                    "pending": "⏳",
                    "running": "🏃",
                    "completed": "✅",
                    "failed": "❌"
                }.get(status, "❓")
                
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Job {job_id}: {status_emoji} {status}", end="", flush=True)
                
                if status == "running":
                    print(f"\n🎉 Job is being processed!")
                    
                if status == "completed":
                    print(f"\n✅ Job completed successfully!")
                    print(f"Stats: {json.dumps(job.get('stats', {}), indent=2)}")
                    
                    # Check for opportunities
                    opps_response = requests.get(
                        f"{API_URL}/api/opportunities?website_id={job['website_id']}&limit=5",
                        headers=headers
                    )
                    if opps_response.status_code == 200:
                        opportunities = opps_response.json()
                        print(f"\n📊 Found {len(opportunities)} opportunities!")
                        for opp in opportunities[:3]:
                            print(f"  - {opp['title']}")
                            print(f"    Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
                    
                    return True
                
                elif status == "failed":
                    print(f"\n❌ Job failed!")
                    print(f"Error: {job.get('error_message', 'Unknown error')}")
                    return False
            
            time.sleep(10)
        
        print(f"\n⚠️ Job still pending after 10 minutes")
        return False

# Main execution
print("HoistScout Worker Queue Fix Monitor")
print("=" * 60)

if wait_for_deployment():
    print("\nWaiting 30 seconds for worker to initialize...")
    time.sleep(30)
    
    # Create a new test job
    job_id = create_test_job()
    if job_id:
        # Monitor the job
        success = monitor_job(job_id)
        
        if not success:
            print("\n⚠️ Worker may still not be processing jobs correctly")
            print("Check logs at: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")
    else:
        print("❌ Failed to create test job")