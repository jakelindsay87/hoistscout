#!/usr/bin/env python3
"""
Test production HoistScout with Ollama configuration
"""
import requests
import os
import time

API_BASE = os.getenv("HOISTSCOUT_API_URL", "https://hoistscout-api.onrender.com")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def check_services():
    """Check if all services are available"""
    print("🔍 Checking Services...")
    print("-" * 50)
    
    # Check API
    try:
        resp = requests.get(f"{API_BASE}/api/health", timeout=5)
        print(f"✅ API: {API_BASE} - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ API: {API_BASE} - Error: {e}")
        return False
    
    # Check Ollama (if local)
    if "localhost" in OLLAMA_URL:
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            print(f"✅ Ollama: {OLLAMA_URL} - Status: {resp.status_code}")
            models = [m['name'] for m in resp.json().get('models', [])]
            if models:
                print(f"   Models: {', '.join(models)}")
        except Exception as e:
            print(f"⚠️  Ollama: {OLLAMA_URL} - Not available (worker will use fallback)")
    
    return True

def login():
    """Login and return token"""
    login_data = {
        "username": "demo",
        "password": "demo123",
        "grant_type": "password"
    }
    
    resp = requests.post(
        f"{API_BASE}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if resp.status_code == 200:
        return resp.json().get("access_token")
    else:
        raise Exception(f"Login failed: {resp.status_code}")

def get_or_create_tenders_website(token):
    """Get or create tenders.gov.au website"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Check existing
    resp = requests.get(f"{API_BASE}/api/websites/", headers=headers)
    websites = resp.json()
    
    for site in websites:
        if "tenders.gov.au" in site.get("url", ""):
            print(f"✅ Found existing website: {site['name']} (ID: {site['id']})")
            return site['id']
    
    # Create new
    website_data = {
        "name": "Australian Government Tenders",
        "url": "https://www.tenders.gov.au/atm",
        "category": "government",
        "scraping_config": {
            "search_patterns": ["tender", "contract", "procurement", "opportunity"],
            "max_depth": 2,
            "extract_pdfs": True
        },
        "is_active": True
    }
    
    resp = requests.post(
        f"{API_BASE}/api/websites/",
        headers=headers,
        json=website_data
    )
    
    if resp.status_code in [200, 201]:
        site = resp.json()
        print(f"✅ Created website: {site['name']} (ID: {site['id']})")
        return site['id']
    else:
        raise Exception(f"Failed to create website: {resp.text}")

def trigger_scraping(token, website_id):
    """Trigger scraping job"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    job_data = {
        "website_id": website_id,
        "job_type": "full",
        "priority": 10
    }
    
    resp = requests.post(
        f"{API_BASE}/api/scraping/jobs/",
        headers=headers,
        json=job_data
    )
    
    if resp.status_code in [200, 201]:
        job = resp.json()
        print(f"✅ Created scraping job: {job['id']}")
        return job['id']
    else:
        raise Exception(f"Failed to create job: {resp.text}")

def monitor_and_show_results(token, job_id, website_id):
    """Monitor job and show extracted data"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n⏳ Monitoring job {job_id}...")
    print("-" * 50)
    
    # Monitor job
    start_time = time.time()
    last_status = None
    
    while True:
        try:
            resp = requests.get(f"{API_BASE}/api/scraping/jobs/{job_id}", headers=headers)
            if resp.status_code == 200:
                job = resp.json()
                status = job.get('status', 'unknown')
                
                if status != last_status:
                    print(f"\nStatus: {status}")
                    if job.get('started_at'):
                        print(f"Started: {job['started_at']}")
                    last_status = status
                
                if status == 'completed':
                    print("\n✅ Scraping completed!")
                    if job.get('stats'):
                        print("\nStats:", job['stats'])
                    break
                elif status == 'failed':
                    print(f"\n❌ Job failed: {job.get('error_message')}")
                    break
                elif status == 'running':
                    print(".", end="", flush=True)
            
            if time.time() - start_time > 300:  # 5 min timeout
                print("\n⏱️ Timeout")
                break
                
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            break
        
        time.sleep(5)
    
    # Get opportunities
    print("\n\n📊 Fetching Extracted Opportunities...")
    print("=" * 80)
    
    resp = requests.get(
        f"{API_BASE}/api/opportunities/?website_id={website_id}",
        headers=headers
    )
    
    if resp.status_code == 200:
        opportunities = resp.json()
        
        if not opportunities:
            # Try without filter
            resp = requests.get(f"{API_BASE}/api/opportunities/", headers=headers)
            all_opps = resp.json()
            print(f"\nTotal opportunities in system: {len(all_opps)}")
            opportunities = [o for o in all_opps if o.get('website_id') == website_id]
        
        if opportunities:
            print(f"\n🎯 Found {len(opportunities)} opportunities from tenders.gov.au:\n")
            
            for i, opp in enumerate(opportunities[:5], 1):  # Show first 5
                print(f"\n{'='*80}")
                print(f"[{i}] {opp.get('title', 'No Title')}")
                print(f"{'='*80}")
                
                print(f"📌 Reference: {opp.get('reference_number', 'N/A')}")
                print(f"💰 Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
                print(f"📅 Deadline: {opp.get('deadline', 'N/A')}")
                print(f"📍 Location: {opp.get('location', 'N/A')}")
                print(f"🏷️  Categories: {', '.join(opp.get('categories', []))}")
                print(f"🔗 Source: {opp.get('source_url', 'N/A')}")
                print(f"📊 Confidence: {opp.get('confidence_score', 0):.1%}")
                
                desc = opp.get('description', '')
                if desc:
                    print(f"\n📄 Description:")
                    print(f"{desc[:300]}{'...' if len(desc) > 300 else ''}")
                
                # Show AI-extracted details
                extracted = opp.get('extracted_data', {})
                if extracted:
                    print(f"\n🤖 AI-Extracted Details:")
                    for key, value in extracted.items():
                        if key not in ['raw_text', 'extracted_at', 'title', 'description'] and value:
                            print(f"   • {key}: {value}")
                
                # Check extraction method
                if 'extraction_method' in extracted:
                    method = extracted['extraction_method']
                    if method == 'ollama_llm':
                        print("\n✅ Extracted using Ollama AI")
                    elif method == 'demo_scraper':
                        print("\n⚠️  Using demo data (Ollama not configured)")
                    else:
                        print(f"\n📝 Extraction method: {method}")
        else:
            print("\n⚠️  No opportunities found yet")
            print("This could mean:")
            print("- The worker is still processing")
            print("- Ollama is not configured (set OLLAMA_BASE_URL)")
            print("- The website structure has changed")
    else:
        print(f"\n❌ Failed to get opportunities: {resp.status_code}")

def main():
    print("=" * 80)
    print("🚀 HoistScout Production Test with AI Extraction")
    print("=" * 80)
    print(f"\nAPI: {API_BASE}")
    print(f"Ollama: {OLLAMA_URL}")
    print()
    
    try:
        # Check services
        if not check_services():
            return
        
        # Login
        print("\n🔐 Logging in...")
        token = login()
        print("✅ Login successful")
        
        # Get/create website
        print("\n🌐 Setting up tenders.gov.au...")
        website_id = get_or_create_tenders_website(token)
        
        # Trigger scraping
        print("\n🔄 Triggering AI-powered scraping...")
        job_id = trigger_scraping(token, website_id)
        
        # Monitor and show results
        monitor_and_show_results(token, job_id, website_id)
        
        print("\n\n✅ Test completed!")
        print("\nℹ️  Notes:")
        print("- If using Ollama: Opportunities show AI-extracted details")
        print("- If no Ollama: Falls back to demo data")
        print("- Check worker logs for detailed extraction info")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()