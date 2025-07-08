#!/usr/bin/env python3
"""
HoistScout Production Pipeline Test
Tests the complete scraping pipeline from job creation to opportunity extraction
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "https://hoistscout-api.onrender.com"
USERNAME = "demo"
PASSWORD = "demo123"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(message, status="info"):
    """Print colored status messages"""
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, BLUE)
    print(f"{color}[{status.upper()}]{RESET} {message}")

def login():
    """Authenticate and get access token"""
    print_status("Logging in as demo user...", "info")
    
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_status("Login successful!", "success")
        return token
    else:
        print_status(f"Login failed: {response.text}", "error")
        return None

def get_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def check_worker_health(token):
    """Check if worker is processing jobs"""
    print_status("\nChecking worker status...", "info")
    
    response = requests.get(
        f"{API_BASE_URL}/api/jobs?status=pending",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        pending_jobs = response.json()
        if len(pending_jobs) > 0:
            print_status(f"Found {len(pending_jobs)} pending jobs", "warning")
            print_status("Worker may not be processing jobs - check GEMINI_API_KEY!", "warning")
        else:
            print_status("No stuck pending jobs found", "success")
        return pending_jobs
    else:
        print_status(f"Failed to check jobs: {response.text}", "error")
        return []

def find_test_website(token):
    """Find a good website to test with"""
    print_status("\nFinding test website...", "info")
    
    response = requests.get(
        f"{API_BASE_URL}/api/websites",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        websites = response.json()
        # Look for tenders.gov.au or similar
        test_site = None
        for site in websites:
            if "tenders.gov.au" in site["url"] or "grants.gov.au" in site["url"]:
                test_site = site
                break
        
        if not test_site and websites:
            test_site = websites[0]  # Use first available
            
        if test_site:
            print_status(f"Using test site: {test_site['name']} ({test_site['url']})", "success")
            return test_site
        else:
            print_status("No websites found to test with!", "error")
            return None
    else:
        print_status(f"Failed to fetch websites: {response.text}", "error")
        return None

def create_scraping_job(token, website_id):
    """Create a new scraping job"""
    print_status(f"\nCreating scraping job for website ID {website_id}...", "info")
    
    response = requests.post(
        f"{API_BASE_URL}/api/scrape/{website_id}",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        job = response.json()
        print_status(f"Job created successfully! ID: {job['id']}", "success")
        return job
    else:
        print_status(f"Failed to create job: {response.text}", "error")
        return None

def monitor_job(token, job_id, timeout=300):
    """Monitor job progress"""
    print_status(f"\nMonitoring job {job_id}...", "info")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"{API_BASE_URL}/api/jobs/{job_id}",
            headers=get_headers(token)
        )
        
        if response.status_code == 200:
            job = response.json()
            status = job["status"]
            
            if status != last_status:
                print_status(f"Job status: {status}", "info")
                last_status = status
            
            if status == "completed":
                print_status("Job completed successfully!", "success")
                return job
            elif status == "failed":
                print_status(f"Job failed: {job.get('error', 'Unknown error')}", "error")
                return job
            elif status == "pending" and time.time() - start_time > 30:
                print_status("Job stuck in pending - worker not processing!", "error")
                print_status("ACTION REQUIRED: Set GEMINI_API_KEY in Render dashboard", "error")
                return job
        else:
            print_status(f"Failed to check job status: {response.text}", "error")
        
        time.sleep(5)
    
    print_status("Job monitoring timed out", "error")
    return None

def check_opportunities(token, job_id):
    """Check if opportunities were extracted"""
    print_status("\nChecking for extracted opportunities...", "info")
    
    # First check job results
    response = requests.get(
        f"{API_BASE_URL}/api/results/{job_id}",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print_status(f"Found {len(results)} results from job", "info")
    
    # Then check all opportunities
    response = requests.get(
        f"{API_BASE_URL}/api/opportunities",
        headers=get_headers(token)
    )
    
    if response.status_code == 200:
        opportunities = response.json()
        if opportunities:
            print_status(f"Total opportunities in database: {len(opportunities)}", "success")
            # Show first few opportunities
            for i, opp in enumerate(opportunities[:3]):
                print(f"\n  Opportunity {i+1}:")
                print(f"  - Title: {opp.get('title', 'N/A')}")
                print(f"  - Value: ${opp.get('value', 'N/A')}")
                print(f"  - Deadline: {opp.get('closing_date', 'N/A')}")
            return True
        else:
            print_status("No opportunities found in database!", "error")
            return False
    else:
        print_status(f"Failed to fetch opportunities: {response.text}", "error")
        return False

def main():
    """Run the complete pipeline test"""
    print(f"\n{BLUE}=== HoistScout Production Pipeline Test ==={RESET}\n")
    print(f"Testing against: {API_BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Login
    token = login()
    if not token:
        return
    
    # Step 2: Check worker health
    pending_jobs = check_worker_health(token)
    
    # Step 3: Find test website
    website = find_test_website(token)
    if not website:
        return
    
    # Step 4: Create scraping job
    job = create_scraping_job(token, website["id"])
    if not job:
        return
    
    # Step 5: Monitor job progress
    completed_job = monitor_job(token, job["id"])
    if not completed_job:
        return
    
    if completed_job["status"] == "pending":
        print_status("\n⚠️  CRITICAL ISSUE DETECTED!", "error")
        print_status("The worker is not processing jobs!", "error")
        print_status("This means NO opportunities are being extracted!", "error")
        print_status("\nACTION REQUIRED:", "error")
        print_status("1. Go to: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g", "error")
        print_status("2. Add GEMINI_API_KEY environment variable", "error")
        print_status("3. Get free key at: https://makersuite.google.com/app/apikey", "error")
        print_status("4. Save and let worker restart", "error")
        print_status("5. Run this test again", "error")
        return
    
    # Step 6: Check opportunities
    if completed_job["status"] == "completed":
        success = check_opportunities(token, job["id"])
        
        if success:
            print_status("\n✅ SUCCESS! Pipeline is working!", "success")
            print_status("HoistScout is now extracting funding opportunities!", "success")
        else:
            print_status("\n❌ Pipeline completed but no opportunities extracted", "error")
            print_status("Check worker logs for extraction errors", "error")
    
    print(f"\n{BLUE}=== Test Complete ==={RESET}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()