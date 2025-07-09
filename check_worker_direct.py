#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import time

print("Checking HoistScout Worker Status...")
print("=" * 80)

# First check if API is accessible
print("\n1. Checking API accessibility...")
try:
    api_resp = requests.get("https://hoistscout-api.onrender.com/api/health", timeout=10)
    print(f"   API Health Check: {api_resp.status_code}")
    if api_resp.status_code == 200:
        print(f"   Response: {api_resp.json()}")
except Exception as e:
    print(f"   ❌ API not accessible: {e}")

# Login and check job queue
print("\n2. Checking job queue...")
try:
    login_resp = requests.post(
        "https://hoistscout-api.onrender.com/api/auth/login",
        data={"username": "demo", "password": "demo123"},
        timeout=10
    )
    
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get recent jobs
        jobs_resp = requests.get(
            "https://hoistscout-api.onrender.com/api/scraping/jobs?limit=20",
            headers=headers,
            timeout=10
        )
        
        if jobs_resp.status_code == 200:
            jobs = jobs_resp.json()
            
            # Count by status
            status_counts = {}
            for job in jobs:
                status = job.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("\n   Job Status Summary:")
            for status, count in sorted(status_counts.items()):
                print(f"     {status}: {count}")
            
            # Show details of recent jobs
            print("\n   Recent Jobs (last 10):")
            for job in jobs[:10]:
                created = job.get('created_at', 'unknown')[:19]
                status = job.get('status', 'unknown')
                job_id = str(job.get('id', 'unknown'))
                error = job.get('error', '')
                
                status_emoji = {
                    'pending': '⏳',
                    'running': '🔄',
                    'completed': '✅',
                    'failed': '❌'
                }.get(status, '❓')
                
                print(f"     {status_emoji} {created} [{job_id[:8]}] {status}")
                if error:
                    print(f"        Error: {error[:100]}")
            
            # Try to submit a test job
            print("\n3. Submitting test job...")
            test_job_resp = requests.post(
                "https://hoistscout-api.onrender.com/api/scraping/jobs",
                headers=headers,
                json={
                    "url": "https://example.com",
                    "scraper_type": "generic"
                },
                timeout=10
            )
            
            if test_job_resp.status_code == 201:
                test_job = test_job_resp.json()
                test_job_id = test_job.get('id', 'unknown')
                print(f"   ✅ Test job created: {test_job_id}")
                
                # Wait and check if it gets picked up
                print("   Waiting 5 seconds to see if worker picks it up...")
                time.sleep(5)
                
                # Check test job status
                job_status_resp = requests.get(
                    f"https://hoistscout-api.onrender.com/api/scraping/jobs/{test_job_id}",
                    headers=headers,
                    timeout=10
                )
                
                if job_status_resp.status_code == 200:
                    job_status = job_status_resp.json()
                    status = job_status.get('status', 'unknown')
                    print(f"   Test job status after 5s: {status}")
                    
                    if status == 'pending':
                        print("   ⚠️  Worker is NOT processing jobs - still pending after 5 seconds")
                    elif status == 'running':
                        print("   ✅ Worker is processing! Job picked up and running")
                    elif status == 'completed':
                        print("   ✅ Worker processed job successfully!")
                    elif status == 'failed':
                        error = job_status.get('error', 'No error message')
                        print(f"   ❌ Job failed: {error}")
            else:
                print(f"   ❌ Failed to create test job: {test_job_resp.status_code}")
                print(f"      {test_job_resp.text}")
                
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("Summary:")
print("- API is accessible" if 'api_resp' in locals() and api_resp.status_code == 200 else "- API is NOT accessible")
print("- Worker is " + ("processing jobs" if 'status' in locals() and status in ['running', 'completed'] else "NOT processing jobs"))
print("- All pending jobs indicate worker is not running or can't connect to Redis/DB")