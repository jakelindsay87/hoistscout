#!/usr/bin/env python3
"""Test script to verify scraping functionality."""
import requests
import time
import json
from datetime import datetime

# API endpoints
API_BASE = "https://hoistscraper.onrender.com"

def test_api_health():
    """Test if API is accessible."""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print(f"✓ API is healthy: {response.json()}")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to API: {e}")
        return False

def get_websites():
    """Get list of websites."""
    print("\nFetching websites...")
    try:
        response = requests.get(f"{API_BASE}/api/websites", timeout=10)
        if response.status_code == 200:
            websites = response.json()
            print(f"✓ Found {len(websites)} websites")
            return websites
        else:
            print(f"✗ Failed to get websites: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error fetching websites: {e}")
        return []

def create_test_website():
    """Create a test website if none exist."""
    print("\nCreating test website...")
    test_site = {
        "name": "Test Grant Site",
        "url": "https://www.grants.gov",
        "crawl_enabled": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/websites",
            json=test_site,
            timeout=10
        )
        if response.status_code in [200, 201]:
            website = response.json()
            print(f"✓ Created test website: {website['name']} (ID: {website['id']})")
            return website
        else:
            print(f"✗ Failed to create website: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error creating website: {e}")
        return None

def trigger_scrape(website_id):
    """Trigger a scrape job for a website."""
    print(f"\nTriggering scrape for website ID {website_id}...")
    
    job_data = {
        "website_id": website_id
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/scrape-jobs",
            json=job_data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            job = response.json()
            print(f"✓ Created scrape job ID: {job['id']} with status: {job['status']}")
            return job
        else:
            print(f"✗ Failed to create job: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error creating job: {e}")
        return None

def check_job_status(job_id):
    """Check the status of a scrape job."""
    try:
        response = requests.get(f"{API_BASE}/api/scrape-jobs/{job_id}", timeout=10)
        if response.status_code == 200:
            job = response.json()
            return job
        else:
            print(f"✗ Failed to get job status: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error checking job: {e}")
        return None

def monitor_job(job_id, max_wait=120):
    """Monitor a job until completion."""
    print(f"\nMonitoring job {job_id}...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        job = check_job_status(job_id)
        if not job:
            break
            
        status = job.get('status', 'unknown')
        print(f"  Job status: {status}")
        
        if status in ['completed', 'failed']:
            if status == 'completed':
                print(f"✓ Job completed successfully!")
            else:
                error = job.get('error_message', 'Unknown error')
                print(f"✗ Job failed: {error}")
            return job
            
        time.sleep(5)
    
    print(f"✗ Job did not complete within {max_wait} seconds")
    return None

def main():
    """Main test function."""
    print("=== HoistScraper Functionality Test ===")
    print(f"Time: {datetime.now()}")
    print(f"API: {API_BASE}")
    print("=" * 40)
    
    # Test API health
    if not test_api_health():
        print("\n❌ API is not accessible. Exiting.")
        return
    
    # Get existing websites
    websites = get_websites()
    
    # Create a test website if none exist
    if not websites:
        website = create_test_website()
        if not website:
            print("\n❌ Could not create test website. Exiting.")
            return
    else:
        # Use the first website
        website = websites[0]
        print(f"\nUsing existing website: {website['name']} (ID: {website['id']})")
    
    # Trigger a scrape job
    job = trigger_scrape(website['id'])
    if not job:
        print("\n❌ Could not create scrape job. Exiting.")
        return
    
    # Monitor the job
    final_job = monitor_job(job['id'])
    
    # Summary
    print("\n=== Test Summary ===")
    if final_job and final_job.get('status') == 'completed':
        print("✅ Scraping functionality is working!")
        print(f"   - Website: {website['name']}")
        print(f"   - Job ID: {final_job['id']}")
        print(f"   - Status: {final_job['status']}")
    else:
        print("❌ Scraping functionality is not working properly")
        if final_job:
            print(f"   - Final status: {final_job.get('status', 'unknown')}")
            print(f"   - Error: {final_job.get('error_message', 'None')}")

if __name__ == "__main__":
    main()