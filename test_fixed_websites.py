#!/usr/bin/env python3
"""Test that the fixed websites endpoint works correctly"""
import httpx
import asyncio

API_BASE = "https://hoistscout-api.onrender.com"

async def test_fixed_endpoint():
    print("=== Testing Fixed Websites Endpoint ===\n")
    
    async with httpx.AsyncClient() as client:
        # Login first
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            data={"username": "demo@hoistscout.com", "password": "demo123"}
        )
        
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code}")
            print(resp.text)
            return
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the fixed endpoint with trailing slash
        print("Testing GET /api/websites/ (with trailing slash)")
        resp = await client.get(
            f"{API_BASE}/api/websites/",
            headers=headers
        )
        
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Success! Retrieved {len(data)} websites")
            if data:
                print("\nFirst website:")
                print(f"  ID: {data[0]['id']}")
                print(f"  Name: {data[0]['name']}")
                print(f"  URL: {data[0]['url']}")
        else:
            print(f"Error: {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_fixed_endpoint())