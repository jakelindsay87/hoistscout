#!/usr/bin/env python3
"""Test API authentication flow"""
import requests

API_BASE = "https://hoistscout-api.onrender.com"

# Test 1: Health check
print("1. Testing API health...")
try:
    response = requests.get(f"{API_BASE}/health", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Login with demo user
print("\n2. Testing login...")
login_data = {
    "username": "demo",
    "password": "demo123",
    "grant_type": "password"
}

try:
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"   Token received: {'Yes' if token else 'No'}")
        
        # Test 3: Access authenticated endpoint
        if token:
            print("\n3. Testing authenticated endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test /api/auth/me
            response = requests.get(f"{API_BASE}/api/auth/me", headers=headers, timeout=10)
            print(f"   /api/auth/me status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Test /api/websites
            response = requests.get(f"{API_BASE}/api/websites", headers=headers, timeout=10)
            print(f"   /api/websites status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Try direct email login
print("\n4. Testing login with email...")
login_data = {
    "username": "demo@hoistscout.com",
    "password": "demo123",
    "grant_type": "password"
}

try:
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
except Exception as e:
    print(f"   Error: {e}")