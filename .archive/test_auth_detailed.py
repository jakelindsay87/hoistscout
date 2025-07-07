#!/usr/bin/env python3
"""Detailed authentication test to diagnose the issue"""
import requests
import json
import sys

API_BASE = "https://hoistscout-api.onrender.com"

def test_auth():
    print("=== HoistScout Authentication Detailed Test ===\n")
    
    # Step 1: Login
    print("1. Testing login...")
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
    
    if response.status_code != 200:
        print(f"✗ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
        
    data = response.json()
    token = data.get("access_token")
    print(f"✓ Login successful, token: {token[:30]}...")
    
    # Step 2: Test headers
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Test different endpoints
    endpoints = [
        "/api/auth/me",
        "/api/auth/profile",
        "/api/websites",
        "/api/opportunities",
        "/api/scraping/jobs"
    ]
    
    print("\n2. Testing endpoints with Bearer token...")
    for endpoint in endpoints:
        try:
            resp = requests.get(
                f"{API_BASE}{endpoint}", 
                headers=headers, 
                timeout=5
            )
            print(f"  {endpoint}: {resp.status_code}")
            
            # If unauthorized, check headers
            if resp.status_code == 401:
                print(f"    Response headers: {dict(resp.headers)}")
                print(f"    Response body: {resp.text[:200]}")
                
        except Exception as e:
            print(f"  {endpoint}: ERROR - {e}")
    
    # Step 4: Test raw request to see what's different
    print("\n3. Testing raw request to /api/websites...")
    import urllib.request
    import urllib.error
    
    req = urllib.request.Request(
        f"{API_BASE}/api/websites",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"  Status: {response.status}")
            print(f"  Headers: {dict(response.headers)}")
    except urllib.error.HTTPError as e:
        print(f"  Error: {e.code}")
        print(f"  Headers: {dict(e.headers)}")
        print(f"  Body: {e.read().decode()[:200]}")
    
    # Step 5: Check if there's a timing issue
    print("\n4. Testing with fresh login...")
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    
    if response.status_code == 200:
        fresh_token = response.json().get("access_token")
        
        # Immediately test websites endpoint
        resp = requests.get(
            f"{API_BASE}/api/websites",
            headers={"Authorization": f"Bearer {fresh_token}"},
            timeout=5
        )
        print(f"  Fresh token test: {resp.status_code}")
    
    return True

if __name__ == "__main__":
    try:
        test_auth()
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)