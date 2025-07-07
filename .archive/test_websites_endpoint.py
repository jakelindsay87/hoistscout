#!/usr/bin/env python3
"""Test websites endpoint"""
import httpx
import asyncio

API_BASE = "https://hoistscout-api.onrender.com"

async def test_websites_endpoint():
    print("=== Testing Websites Endpoint ===\n")
    
    async with httpx.AsyncClient() as client:
        # Login first
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            data={"username": "demo@hoistscout.com", "password": "demo123"}
        )
        
        if resp.status_code != 200:
            print("Login failed")
            return
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test different variations
        endpoints = [
            "/api/websites",
            "/api/websites/",
            "/api/websites?page=1&limit=10",
        ]
        
        for endpoint in endpoints:
            print(f"Testing GET {endpoint}")
            resp = await client.get(
                f"{API_BASE}{endpoint}",
                headers=headers,
                follow_redirects=False  # Don't follow redirects
            )
            
            print(f"  Status: {resp.status_code}")
            if resp.status_code in [301, 302, 307, 308]:
                print(f"  Redirect to: {resp.headers.get('location')}")
            elif resp.status_code == 200:
                print(f"  Success: {len(resp.json())} websites")
            else:
                print(f"  Error: {resp.text[:100]}")
            print()

if __name__ == "__main__":
    asyncio.run(test_websites_endpoint())