#!/usr/bin/env python3
"""
Test script to scrape tenders.gov.au using HoistScout
"""
import asyncio
import json
from datetime import datetime
import httpx

API_URL = "https://hoistscout-api.onrender.com"

async def test_tenders_scraping():
    """Test scraping tenders.gov.au page 4"""
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("🔐 Logging in...")
        login_response = await client.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": "demo@hoistscout.com",
                "password": "demo123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check if tenders.gov.au website exists
        print("\n🔍 Checking for existing website...")
        websites_response = await client.get(
            f"{API_URL}/api/websites/",
            headers=headers
        )
        websites = websites_response.json()
        
        tenders_website = None
        for website in websites:
            if "tenders.gov.au" in website["url"]:
                tenders_website = website
                break
        
        # 3. Create website if it doesn't exist
        if not tenders_website:
            print("📝 Creating tenders.gov.au website...")
            create_response = await client.post(
                f"{API_URL}/api/websites/",
                headers=headers,
                json={
                    "name": "Australian Government Tenders",
                    "url": "https://www.tenders.gov.au/atm",
                    "scrape_frequency": "daily",
                    "is_active": True,
                    "selectors": {}
                }
            )
            tenders_website = create_response.json()
            print(f"✅ Created website with ID: {tenders_website['id']}")
        else:
            print(f"✅ Found existing website with ID: {tenders_website['id']}")
        
        # 4. Create scraping job
        print("\n🚀 Creating scraping job...")
        job_response = await client.post(
            f"{API_URL}/api/scraping/jobs/",
            headers=headers,
            json={
                "website_id": tenders_website["id"],
                "job_type": "full"
            }
        )
        job = job_response.json()
        print(f"✅ Created job with ID: {job['id']}")
        print(f"   Status: {job['status']}")
        
        # 5. Poll job status
        print("\n⏳ Waiting for job to complete...")
        print("   (This may take 1-2 minutes while Gemini AI extracts tender data)")
        
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            job_status_response = await client.get(
                f"{API_URL}/api/scraping/jobs/{job['id']}/",
                headers=headers
            )
            job_status = job_status_response.json()
            
            print(f"   Status: {job_status['status']} (attempt {attempt + 1}/{max_attempts})")
            
            if job_status["status"] == "completed":
                print("\n✅ Job completed successfully!")
                break
            elif job_status["status"] == "failed":
                print(f"\n❌ Job failed: {job_status.get('error_message', 'Unknown error')}")
                return
            
            attempt += 1
        
        if attempt >= max_attempts:
            print("\n⏱️ Job timed out - checking current status...")
        
        # 6. Get extracted opportunities
        print("\n📊 Fetching extracted opportunities...")
        opportunities_response = await client.get(
            f"{API_URL}/api/opportunities/",
            headers=headers,
            params={"website_id": tenders_website["id"]}
        )
        opportunities = opportunities_response.json()
        
        print(f"\n🎯 Found {len(opportunities)} opportunities")
        
        # 7. Display results
        if opportunities:
            print("\n" + "="*80)
            print("EXTRACTED TENDER DATA FROM TENDERS.GOV.AU")
            print("="*80)
            
            # Show first 5 opportunities
            for i, opp in enumerate(opportunities[:5]):
                print(f"\n--- Opportunity {i+1} ---")
                print(f"Title: {opp.get('title', 'N/A')}")
                print(f"Reference: {opp.get('reference_number', 'N/A')}")
                print(f"Deadline: {opp.get('deadline', 'N/A')}")
                print(f"Value: ${opp.get('value', 'N/A')} {opp.get('currency', '')}")
                print(f"Location: {opp.get('location', 'N/A')}")
                print(f"Categories: {', '.join(opp.get('categories', []))}")
                print(f"Source URL: {opp.get('source_url', 'N/A')}")
                
                desc = opp.get('description', 'N/A')
                if desc and desc != 'N/A':
                    print(f"Description: {desc[:200]}{'...' if len(desc) > 200 else ''}")
                
            if len(opportunities) > 5:
                print(f"\n... and {len(opportunities) - 5} more opportunities")
        else:
            print("\n⚠️ No opportunities extracted. Checking job stats...")
            print(f"Job stats: {json.dumps(job_status.get('stats', {}), indent=2)}")
        
        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)
        print("\n💡 To verify accuracy:")
        print("1. Visit https://www.tenders.gov.au/atm")
        print("2. Navigate to page 4")
        print("3. Compare the first tender with the extracted data above")
        print("\n🔍 Look for:")
        print("- Matching titles and reference numbers")
        print("- Correct deadline dates")
        print("- Accurate descriptions")
        print("- Proper categorization")

if __name__ == "__main__":
    asyncio.run(test_tenders_scraping())