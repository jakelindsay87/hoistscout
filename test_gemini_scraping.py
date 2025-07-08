#!/usr/bin/env python3
"""Test script to create a new scraping job and monitor it"""
import requests
import time

# Login first
login_resp = requests.post(
    "https://hoistscout-api.onrender.com/api/auth/login",
    data={"username": "demo", "password": "demo123"}
)

if login_resp.status_code != 200:
    print("Login failed!")
    exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create a new scraping job for tenders.gov.au
print("Creating new scraping job for tenders.gov.au...")
job_resp = requests.post(
    "https://hoistscout-api.onrender.com/api/scraping/jobs/",
    headers=headers,
    json={
        "website_id": 1,  # Assuming tenders.gov.au is ID 1
        "force": True
    }
)

if job_resp.status_code in [200, 201]:
    job = job_resp.json()
    job_id = job.get("id", "unknown")
    print(f"✅ Created job {job_id}")
else:
    print(f"❌ Failed to create job: {job_resp.status_code}")
    print(job_resp.text)
    exit(1)

# Monitor the job
print("\nMonitoring job status...")
for i in range(30):  # Monitor for up to 5 minutes
    time.sleep(10)
    
    # Get job status
    status_resp = requests.get(
        f"https://hoistscout-api.onrender.com/api/scraping/jobs/{job_id}",
        headers=headers
    )
    
    if status_resp.status_code == 200:
        job = status_resp.json()
        status = job.get("status", "unknown")
        created = job.get("created_at", "")[:19]
        started = job.get("started_at", "")[:19] if job.get("started_at") else "Not started"
        
        print(f"  Status: {status} | Created: {created} | Started: {started}")
        
        if status == "completed":
            print("\n✅ Job completed successfully!")
            
            # Check if opportunities were found
            opp_count = job.get("stats", {}).get("opportunities_found", 0)
            print(f"Opportunities found: {opp_count}")
            
            if opp_count > 0:
                # Get opportunities
                opp_resp = requests.get(
                    "https://hoistscout-api.onrender.com/api/opportunities/?limit=5",
                    headers=headers
                )
                
                if opp_resp.status_code == 200:
                    opps = opp_resp.json()
                    print(f"\nLatest opportunities:")
                    for opp in opps[:3]:
                        print(f"  - {opp['title'][:80]}...")
                        print(f"    Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
                        print(f"    Deadline: {opp.get('deadline', 'N/A')}")
            break
            
        elif status == "failed":
            print(f"\n❌ Job failed!")
            print(f"Error: {job.get('error_message', 'Unknown error')}")
            break
        
        elif status == "running":
            print("  🔄 Job is running...")
    else:
        print(f"  ❌ Failed to get job status: {status_resp.status_code}")

print("\nDone!")