#!/usr/bin/env python3
"""Debug authentication headers issue"""
import requests
import json

API_BASE = "https://hoistscout-api.onrender.com"

print("Testing HoistScout Authentication...")

# Step 1: Login
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
    data = response.json()
    token = data.get("access_token")
    print(f"✓ Login successful, token: {token[:30]}...")
    
    # Test different header formats
    headers_to_test = [
        {"Authorization": f"Bearer {token}"},
        {"Authorization": f"bearer {token}"},
        {"Authorization": token},
        {"X-Token": token},
        {"Access-Token": token}
    ]
    
    for i, headers in enumerate(headers_to_test):
        print(f"\nTest {i+1}: Headers = {list(headers.keys())[0]}: {list(headers.values())[0][:30]}...")
        
        # Test /api/auth/me
        resp = requests.get(f"{API_BASE}/api/auth/me", headers=headers, timeout=5)
        print(f"  /api/auth/me: {resp.status_code}")
        
        # Test /api/websites
        resp = requests.get(f"{API_BASE}/api/websites", headers=headers, timeout=5)
        print(f"  /api/websites: {resp.status_code}")
        
        if resp.status_code == 200:
            print("  ✓ This header format works!")
            break
else:
    print(f"✗ Login failed: {response.status_code}")
    print(response.text)