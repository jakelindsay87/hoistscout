#!/usr/bin/env python3
"""
Wait for deployment and test scraping with real data extraction
"""
import requests
import time
import json
from datetime import datetime

API_BASE = "https://hoistscout-api.onrender.com"

def login():
    """Login and return auth token"""
    login_data = {
        "username": "demo",
        "password": "demo123",
        "grant_type": "password"
    }
    
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Login failed: {response.status_code}")

def check_deployment_status(token):
    """Check if new code is deployed by looking at job results"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check health endpoint
    resp = requests.get(f"{API_BASE}/api/health", timeout=5)
    print(f"Health check: {resp.status_code}")
    
    return resp.status_code == 200

def trigger_new_job(token):
    """Trigger a new scraping job for tenders.gov.au"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get website ID for tenders.gov.au
    resp = requests.get(f"{API_BASE}/api/websites/", headers=headers)
    websites = resp.json()
    
    website_id = None
    for site in websites:
        if "tenders.gov.au" in site.get("url", ""):
            website_id = site['id']
            break
    
    if not website_id:
        raise Exception("tenders.gov.au not found in websites")
    
    # Create new job
    job_data = {
        "website_id": website_id,
        "job_type": "full",
        "priority": 10
    }
    
    resp = requests.post(
        f"{API_BASE}/api/scraping/jobs/",
        headers=headers,
        json=job_data,
        timeout=10
    )
    
    if resp.status_code in [200, 201]:
        job = resp.json()
        print(f"✓ Created new scraping job: {job['id']}")
        return job['id']
    else:
        raise Exception(f"Failed to create job: {resp.status_code}")

def monitor_job_detailed(token, job_id):
    """Monitor job with detailed status updates"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    last_status = None
    
    print(f"\nMonitoring job {job_id}...")
    print("-" * 50)
    
    while True:
        elapsed = time.time() - start_time
        
        try:
            resp = requests.get(
                f"{API_BASE}/api/scraping/jobs/{job_id}",
                headers=headers,
                timeout=5
            )
            
            if resp.status_code == 200:
                job = resp.json()
                status = job.get('status', 'unknown')
                
                if status != last_status:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status changed: {last_status} → {status}")
                    last_status = status
                    
                    if job.get('started_at'):
                        print(f"  Started at: {job['started_at']}")
                    if job.get('error_message'):
                        print(f"  Error: {job['error_message']}")
                
                if status == 'completed':
                    print(f"\n✅ Job completed successfully!")
                    if job.get('stats'):
                        print(f"\nJob Statistics:")
                        print(json.dumps(job['stats'], indent=2))
                    return True
                    
                elif status == 'failed':
                    print(f"\n❌ Job failed")
                    if job.get('error_message'):
                        print(f"Error: {job['error_message']}")
                    return False
                    
                elif status == 'running':
                    print(".", end="", flush=True)
                
                if elapsed > 300:  # 5 minute timeout
                    print(f"\n⏱️ Timeout after 5 minutes")
                    return False
                    
            else:
                print(f"\n⚠️ Failed to get job status: {resp.status_code}")
                
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
        
        time.sleep(3)

def get_opportunities(token):
    """Get all opportunities and display them"""
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.get(f"{API_BASE}/api/opportunities/", headers=headers)
    
    if resp.status_code == 200:
        opportunities = resp.json()
        
        print(f"\n{'='*80}")
        print(f"EXTRACTED OPPORTUNITIES: {len(opportunities)} found")
        print(f"{'='*80}")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n[Opportunity {i}]")
            print(f"Title: {opp.get('title', 'N/A')}")
            print(f"Reference: {opp.get('reference_number', 'N/A')}")
            print(f"Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
            print(f"Deadline: {opp.get('deadline', 'N/A')}")
            print(f"Location: {opp.get('location', 'N/A')}")
            print(f"Categories: {', '.join(opp.get('categories', []))}")
            print(f"Source: {opp.get('source_url', 'N/A')}")
            print(f"Confidence: {opp.get('confidence_score', 0):.2%}")
            
            desc = opp.get('description', '')
            if desc:
                print(f"\nDescription:")
                print(f"{desc[:300]}{'...' if len(desc) > 300 else ''}")
            
            # Show LLM extracted data
            extracted = opp.get('extracted_data', {})
            if extracted:
                print(f"\nExtracted Details:")
                for key, value in extracted.items():
                    if key not in ['raw_text', 'extracted_at'] and value:
                        print(f"  - {key}: {value}")
            
            print("-" * 80)
            
        return opportunities
    else:
        print(f"Failed to get opportunities: {resp.status_code}")
        return []

def main():
    print("=" * 80)
    print("HoistScout - Waiting for Deployment and Testing Real Extraction")
    print("=" * 80)
    
    try:
        # Login
        print("\n1. Logging in...")
        token = login()
        print("✓ Login successful")
        
        # Wait a bit for deployment
        print("\n2. Waiting for deployment to update (30 seconds)...")
        time.sleep(30)
        
        # Check deployment
        print("\n3. Checking deployment status...")
        if not check_deployment_status(token):
            print("⚠️ Deployment may not be ready yet")
        
        # Trigger new job
        print("\n4. Triggering new scraping job...")
        job_id = trigger_new_job(token)
        
        # Monitor job
        print("\n5. Monitoring job execution...")
        success = monitor_job_detailed(token, job_id)
        
        # Get opportunities regardless of job status
        print("\n6. Fetching opportunities...")
        time.sleep(5)  # Give it a moment to save data
        
        opportunities = get_opportunities(token)
        
        if not opportunities:
            print("\n⚠️ No opportunities found. The scraper may need more time or configuration.")
        else:
            print(f"\n✅ Successfully extracted {len(opportunities)} opportunities!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()