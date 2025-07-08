#!/usr/bin/env python3
"""
Test real scraping of tenders.gov.au with LLM extraction
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

def add_tenders_website(token):
    """Add tenders.gov.au website"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First check if it already exists
    resp = requests.get(f"{API_BASE}/api/websites/", headers=headers)
    websites = resp.json()
    
    for site in websites:
        if "tenders.gov.au" in site.get("url", ""):
            print(f"✓ tenders.gov.au already exists with ID: {site['id']}")
            return site['id']
    
    # Create new website
    website_data = {
        "name": "Australian Government Tenders",
        "url": "https://www.tenders.gov.au/atm",
        "category": "government",
        "scraping_config": {
            "search_patterns": [
                "tender",
                "contract", 
                "procurement",
                "opportunity",
                "request for tender",
                "RFT",
                "EOI",
                "expression of interest"
            ],
            "max_depth": 3,
            "extract_pdfs": True,
            "follow_pagination": True
        },
        "is_active": True
    }
    
    resp = requests.post(
        f"{API_BASE}/api/websites/",
        headers=headers,
        json=website_data,
        timeout=10
    )
    
    if resp.status_code in [200, 201]:
        website = resp.json()
        print(f"✓ Created website: {website['name']} (ID: {website['id']})")
        return website['id']
    else:
        raise Exception(f"Failed to create website: {resp.status_code} - {resp.text}")

def trigger_scraping(token, website_id):
    """Trigger scraping job"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    job_data = {
        "website_id": website_id,
        "job_type": "full",
        "priority": 10  # High priority
    }
    
    resp = requests.post(
        f"{API_BASE}/api/scraping/jobs/",
        headers=headers,
        json=job_data,
        timeout=10
    )
    
    if resp.status_code in [200, 201]:
        job = resp.json()
        print(f"✓ Created scraping job: {job['id']}")
        return job['id']
    else:
        raise Exception(f"Failed to create job: {resp.status_code} - {resp.text}")

def monitor_job(token, job_id, max_wait=300):
    """Monitor job status"""
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    
    print(f"\nMonitoring job {job_id}...")
    print("-" * 50)
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"⏱️  Job monitoring timeout after {max_wait}s")
            break
        
        try:
            resp = requests.get(
                f"{API_BASE}/api/scraping/jobs/{job_id}",
                headers=headers,
                timeout=5
            )
            
            if resp.status_code == 200:
                job = resp.json()
                status = job.get('status', 'unknown')
                
                print(f"\r⏳ Status: {status} | Elapsed: {int(elapsed)}s", end="", flush=True)
                
                if status in ['completed', 'failed']:
                    print(f"\n{'✓' if status == 'completed' else '✗'} Job {status}")
                    
                    # Show job stats if available
                    if job.get('stats'):
                        print(f"\nJob Statistics:")
                        stats = job['stats']
                        for key, value in stats.items():
                            print(f"  - {key}: {value}")
                    
                    return status == 'completed'
            else:
                print(f"\n⚠️  Failed to get job status: {resp.status_code}")
        
        except Exception as e:
            print(f"\n⚠️  Error monitoring job: {e}")
        
        time.sleep(5)
    
    return False

def get_opportunities(token, website_id=None):
    """Get extracted opportunities"""
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"{API_BASE}/api/opportunities/"
    if website_id:
        url += f"?website_id={website_id}"
    
    resp = requests.get(url, headers=headers, timeout=10)
    
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"Failed to get opportunities: {resp.status_code}")

def display_opportunities(opportunities):
    """Display extracted opportunities"""
    if not opportunities:
        print("\n❌ No opportunities found")
        return
    
    print(f"\n✅ Found {len(opportunities)} opportunities:")
    print("=" * 80)
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n[{i}] {opp.get('title', 'No Title')}")
        print("-" * 80)
        
        # Display key fields
        fields = [
            ('Reference', 'reference_number'),
            ('Deadline', 'deadline'),
            ('Value', 'value'),
            ('Currency', 'currency'),
            ('Location', 'location'),
            ('Categories', 'categories'),
            ('Source URL', 'source_url'),
            ('Confidence', 'confidence_score')
        ]
        
        for label, field in fields:
            value = opp.get(field)
            if value:
                if field == 'categories' and isinstance(value, list):
                    value = ', '.join(value)
                elif field == 'deadline':
                    try:
                        # Format deadline nicely
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        value = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                elif field == 'value' and opp.get('currency'):
                    value = f"{value:,.2f} {opp.get('currency')}"
                elif field == 'confidence_score':
                    value = f"{value:.2%}"
                
                print(f"  {label}: {value}")
        
        # Show description excerpt
        desc = opp.get('description', '')
        if desc:
            # Limit to first 200 chars
            if len(desc) > 200:
                desc = desc[:197] + "..."
            print(f"\n  Description: {desc}")
        
        # Show extracted data if available
        extracted = opp.get('extracted_data', {})
        if extracted and isinstance(extracted, dict):
            print(f"\n  LLM Extracted Fields:")
            for key, value in extracted.items():
                if value and key not in ['title', 'description']:
                    print(f"    - {key}: {value}")

def main():
    print("=" * 80)
    print("HoistScout - Real Scraping Test for tenders.gov.au")
    print("=" * 80)
    
    try:
        # Login
        print("\n1. Logging in...")
        token = login()
        print("✓ Login successful")
        
        # Add website
        print("\n2. Adding tenders.gov.au...")
        website_id = add_tenders_website(token)
        
        # Trigger scraping
        print("\n3. Triggering scraping job...")
        job_id = trigger_scraping(token, website_id)
        
        # Monitor job
        print("\n4. Monitoring job execution...")
        success = monitor_job(token, job_id)
        
        if success:
            # Wait a bit for data to be processed
            print("\n5. Fetching extracted opportunities...")
            time.sleep(5)
            
            opportunities = get_opportunities(token, website_id)
            display_opportunities(opportunities)
            
            # Also show all opportunities (not filtered by website)
            print("\n\n6. All opportunities in system:")
            all_opps = get_opportunities(token)
            print(f"Total opportunities: {len(all_opps)}")
            
        else:
            print("\n❌ Job did not complete successfully")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()