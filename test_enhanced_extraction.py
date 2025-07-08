#!/usr/bin/env python3
"""
Test enhanced extraction with the new comprehensive prompt
"""
import requests
import json
import time
from datetime import datetime

API_BASE = "https://hoistscout-api.onrender.com"

def test_extraction():
    print("=" * 80)
    print("🚀 HoistScout Enhanced Extraction Test")
    print("=" * 80)
    
    # Login
    print("\n1. Logging in...")
    login_resp = requests.post(
        f"{API_BASE}/api/auth/login",
        data={"username": "demo", "password": "demo123", "grant_type": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        return
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Get tenders.gov.au website
    print("\n2. Getting website...")
    resp = requests.get(f"{API_BASE}/api/websites/", headers=headers)
    websites = resp.json()
    
    website_id = None
    for site in websites:
        if "tenders.gov.au" in site.get("url", ""):
            website_id = site["id"]
            print(f"✅ Found tenders.gov.au (ID: {website_id})")
            break
    
    if not website_id:
        print("❌ tenders.gov.au not found")
        return
    
    # Create scraping job
    print("\n3. Creating scraping job...")
    job_resp = requests.post(
        f"{API_BASE}/api/scraping/jobs/",
        headers={**headers, "Content-Type": "application/json"},
        json={"website_id": website_id, "job_type": "full", "priority": 10}
    )
    
    if job_resp.status_code not in [200, 201]:
        print(f"❌ Failed to create job: {job_resp.text}")
        return
    
    job = job_resp.json()
    job_id = job["id"]
    print(f"✅ Created job {job_id}")
    
    # Monitor job
    print("\n4. Monitoring job (this may take a few minutes)...")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < 300:  # 5 minute timeout
        resp = requests.get(f"{API_BASE}/api/scraping/jobs/{job_id}", headers=headers)
        if resp.status_code == 200:
            job = resp.json()
            status = job.get("status", "unknown")
            
            if status != last_status:
                print(f"\n   Status: {status}")
                last_status = status
            
            if status == "completed":
                print("\n✅ Job completed!")
                break
            elif status == "failed":
                print(f"\n❌ Job failed: {job.get('error_message')}")
                return
            elif status == "running":
                print(".", end="", flush=True)
        
        time.sleep(3)
    
    # Get opportunities
    print("\n\n5. Fetching extracted opportunities...")
    print("=" * 80)
    
    resp = requests.get(f"{API_BASE}/api/opportunities/", headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to get opportunities: {resp.status_code}")
        return
    
    all_opportunities = resp.json()
    opportunities = [o for o in all_opportunities if o.get("website_id") == website_id]
    
    if not opportunities:
        print("⚠️  No opportunities extracted yet")
        print("\nPossible reasons:")
        print("- Worker is not configured with Ollama URL")
        print("- Extraction is still processing")
        print("- Website structure has changed")
        return
    
    print(f"\n🎯 Extracted {len(opportunities)} opportunities with enhanced data:\n")
    
    # Display opportunities with enhanced fields
    for i, opp in enumerate(opportunities[:3], 1):  # Show first 3 in detail
        print(f"\n{'='*80}")
        print(f"OPPORTUNITY {i}")
        print(f"{'='*80}")
        
        # Core Information
        print(f"\n📋 CORE INFORMATION")
        print(f"   Title: {opp.get('title', 'N/A')}")
        print(f"   Type: {opp.get('extracted_data', {}).get('opportunity_type', 'N/A')}")
        print(f"   Reference: {opp.get('reference_number', 'N/A')}")
        print(f"   Funder: {opp.get('extracted_data', {}).get('funder_name', 'N/A')}")
        
        # Financial Information
        print(f"\n💰 FINANCIAL INFORMATION")
        print(f"   Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
        
        extracted = opp.get('extracted_data', {})
        if 'funding_value' in extracted:
            fv = extracted['funding_value']
            if isinstance(fv, dict):
                print(f"   Min: ${fv.get('minimum', 0):,.2f}")
                print(f"   Max: ${fv.get('maximum', 0):,.2f}")
        
        if 'co_funding_requirements' in extracted:
            print(f"   Co-funding: {extracted['co_funding_requirements']}")
        
        # Timeline
        print(f"\n📅 TIMELINE")
        print(f"   Deadline: {opp.get('deadline', 'N/A')}")
        if 'publication_date' in extracted:
            print(f"   Published: {extracted['publication_date']}")
        if 'duration' in extracted:
            print(f"   Duration: {extracted['duration']}")
        
        # Eligibility
        print(f"\n✅ ELIGIBILITY")
        if 'eligible_applicants' in extracted:
            applicants = extracted['eligible_applicants']
            if isinstance(applicants, list):
                print(f"   Applicants: {', '.join(applicants)}")
            else:
                print(f"   Applicants: {applicants}")
        
        if 'geographic_restrictions' in extracted:
            print(f"   Geography: {extracted['geographic_restrictions']}")
        
        if 'sector_focus' in extracted:
            sectors = extracted['sector_focus']
            if isinstance(sectors, list):
                print(f"   Sectors: {', '.join(sectors)}")
            else:
                print(f"   Sectors: {sectors}")
        
        # Description
        desc = opp.get('description', '')
        if desc:
            print(f"\n📄 DESCRIPTION")
            print(f"   {desc[:200]}{'...' if len(desc) > 200 else ''}")
        
        # Priority Areas
        if 'priority_areas' in extracted:
            print(f"\n🎯 PRIORITY AREAS")
            areas = extracted['priority_areas']
            if isinstance(areas, list):
                for area in areas:
                    print(f"   • {area}")
            else:
                print(f"   {areas}")
        
        # Contact Information
        if 'contact' in extracted or 'contact_email' in extracted:
            print(f"\n📞 CONTACT")
            contact = extracted.get('contact', {})
            if isinstance(contact, dict):
                if 'email' in contact:
                    print(f"   Email: {contact['email']}")
                if 'phone' in contact:
                    print(f"   Phone: {contact['phone']}")
                if 'website' in contact:
                    print(f"   Website: {contact['website']}")
            elif 'contact_email' in extracted:
                print(f"   Email: {extracted['contact_email']}")
        
        # Assessment Criteria
        if 'assessment_criteria' in extracted:
            print(f"\n📊 ASSESSMENT CRITERIA")
            criteria = extracted['assessment_criteria']
            if isinstance(criteria, list):
                for criterion in criteria:
                    print(f"   • {criterion}")
            else:
                print(f"   {criteria}")
        
        # Extraction Method
        print(f"\n🤖 EXTRACTION METHOD")
        method = extracted.get('extraction_method', 'unknown')
        confidence = opp.get('confidence_score', 0)
        print(f"   Method: {method}")
        print(f"   Confidence: {confidence:.1%}")
        
        if method == 'ollama_llm':
            print("   ✅ AI-powered extraction with enhanced prompt")
        elif method == 'demo_scraper' or method == 'demo_fallback':
            print("   ⚠️  Demo mode (configure Ollama for real extraction)")
    
    # Summary
    print(f"\n\n{'='*80}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Opportunities: {len(opportunities)}")
    
    # Check extraction quality
    high_quality = 0
    for opp in opportunities:
        extracted = opp.get('extracted_data', {})
        quality_fields = [
            'opportunity_type', 'funder_name', 'funding_value',
            'eligible_applicants', 'sector_focus', 'priority_areas',
            'assessment_criteria', 'duration'
        ]
        
        extracted_count = sum(1 for field in quality_fields if field in extracted)
        if extracted_count >= 5:
            high_quality += 1
    
    print(f"High Quality Extractions: {high_quality}/{len(opportunities)}")
    print(f"Quality Rate: {(high_quality/len(opportunities)*100):.1f}%")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    test_extraction()