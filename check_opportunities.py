#!/usr/bin/env python3
"""
Check existing opportunities in HoistScout
"""
import httpx
import asyncio
import json

API_URL = "https://hoistscout-api.onrender.com"

async def check_opportunities():
    async with httpx.AsyncClient() as client:
        # Login
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
        
        # Get all opportunities
        print("\n📊 Fetching all opportunities...")
        response = await client.get(
            f"{API_URL}/api/opportunities/",
            headers=headers
        )
        opportunities = response.json()
        
        print(f"\n✅ Found {len(opportunities)} total opportunities")
        
        if opportunities:
            # Group by website
            by_website = {}
            for opp in opportunities:
                website_id = opp.get('website_id', 'unknown')
                if website_id not in by_website:
                    by_website[website_id] = []
                by_website[website_id].append(opp)
            
            print(f"\n📈 Opportunities by website:")
            for website_id, opps in by_website.items():
                print(f"   Website {website_id}: {len(opps)} opportunities")
            
            # Show sample opportunities
            print("\n🔍 Sample opportunities:")
            for i, opp in enumerate(opportunities[:3]):
                print(f"\n--- Opportunity {i+1} ---")
                print(f"Title: {opp.get('title', 'N/A')}")
                print(f"Reference: {opp.get('reference_number', 'N/A')}")
                print(f"Deadline: {opp.get('deadline', 'N/A')}")
                print(f"Value: ${opp.get('value', 'N/A')} {opp.get('currency', '')}")
                print(f"Source URL: {opp.get('source_url', 'N/A')}")
                print(f"Created: {opp.get('created_at', 'N/A')}")
                
                # Check if this is real data or mock data
                if "Demo Grant" in str(opp.get('title', '')) or "Test Grant" in str(opp.get('title', '')):
                    print("⚠️  This appears to be DEMO/MOCK data")
                else:
                    print("✅  This appears to be REAL extracted data")

if __name__ == "__main__":
    asyncio.run(check_opportunities())