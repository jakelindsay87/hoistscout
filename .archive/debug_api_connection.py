#!/usr/bin/env python3
"""Comprehensive API connection debugger"""
import asyncio
import httpx
import json
import base64
from datetime import datetime

# API endpoints
API_BASE = "https://hoistscout-api.onrender.com"
FRONTEND_BASE = "https://hoistscout-frontend.onrender.com"

# Test credentials
DEMO_EMAIL = "demo@hoistscout.com"
DEMO_PASSWORD = "demo123"

async def test_basic_connectivity():
    """Test 1: Basic API connectivity"""
    print("\n=== TEST 1: Basic Connectivity ===")
    async with httpx.AsyncClient() as client:
        try:
            # Test root endpoint
            resp = await client.get(f"{API_BASE}/")
            print(f"Root endpoint: {resp.status_code} - {resp.json()}")
            
            # Test health endpoint
            resp = await client.get(f"{API_BASE}/health")
            print(f"Health endpoint: {resp.status_code} - {resp.json()}")
            
            # Test API docs
            resp = await client.get(f"{API_BASE}/docs")
            print(f"API docs: {resp.status_code} - {'OK' if resp.status_code == 200 else 'FAIL'}")
            
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

async def test_cors_headers():
    """Test 2: CORS configuration"""
    print("\n=== TEST 2: CORS Headers ===")
    async with httpx.AsyncClient() as client:
        # Test preflight OPTIONS request
        headers = {
            "Origin": FRONTEND_BASE,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization"
        }
        try:
            resp = await client.options(f"{API_BASE}/api/auth/login", headers=headers)
            print(f"Preflight request: {resp.status_code}")
            print(f"CORS headers: {dict(resp.headers)}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

async def test_login_flow():
    """Test 3: Complete login flow"""
    print("\n=== TEST 3: Login Flow ===")
    async with httpx.AsyncClient() as client:
        # Test login with different content types
        test_cases = [
            {
                "name": "FormData (OAuth2 standard)",
                "data": {"username": DEMO_EMAIL, "password": DEMO_PASSWORD},
                "content_type": "application/x-www-form-urlencoded"
            },
            {
                "name": "JSON body",
                "json": {"username": DEMO_EMAIL, "password": DEMO_PASSWORD},
                "content_type": "application/json"
            },
            {
                "name": "Multipart form",
                "files": {"username": (None, DEMO_EMAIL), "password": (None, DEMO_PASSWORD)},
                "content_type": None
            }
        ]
        
        for test in test_cases:
            print(f"\nTesting {test['name']}:")
            headers = {"Origin": FRONTEND_BASE}
            if test.get("content_type"):
                headers["Content-Type"] = test["content_type"]
            
            try:
                if "data" in test:
                    resp = await client.post(f"{API_BASE}/api/auth/login", data=test["data"], headers=headers)
                elif "json" in test:
                    resp = await client.post(f"{API_BASE}/api/auth/login", json=test["json"], headers=headers)
                else:
                    resp = await client.post(f"{API_BASE}/api/auth/login", files=test["files"], headers=headers)
                
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    tokens = resp.json()
                    print(f"  Access token: {tokens['access_token'][:50]}...")
                    return tokens
                else:
                    print(f"  Error: {resp.text}")
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")
    return None

async def test_auth_endpoints(access_token):
    """Test 4: All authentication endpoints"""
    print("\n=== TEST 4: Auth Endpoints ===")
    if not access_token:
        print("No access token available, skipping auth tests")
        return
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Origin": FRONTEND_BASE
        }
        
        endpoints = [
            "/api/auth/me",
            "/api/auth/profile",
            "/api/auth/user",
            "/api/user/me",
            "/api/users/me"
        ]
        
        for endpoint in endpoints:
            try:
                resp = await client.get(f"{API_BASE}{endpoint}", headers=headers)
                print(f"{endpoint}: {resp.status_code} - {'OK' if resp.status_code == 200 else resp.text[:100]}")
            except Exception as e:
                print(f"{endpoint}: ERROR - {type(e).__name__}: {e}")

async def test_token_validation():
    """Test 5: Token validation and parsing"""
    print("\n=== TEST 5: Token Validation ===")
    async with httpx.AsyncClient() as client:
        # First get a token
        data = {"username": DEMO_EMAIL, "password": DEMO_PASSWORD}
        resp = await client.post(f"{API_BASE}/api/auth/login", data=data)
        
        if resp.status_code != 200:
            print("Failed to get token")
            return
        
        tokens = resp.json()
        access_token = tokens["access_token"]
        
        # Decode JWT (without verification)
        try:
            parts = access_token.split(".")
            if len(parts) == 3:
                # Decode header
                header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
                print(f"JWT Header: {header}")
                
                # Decode payload
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
                print(f"JWT Payload: {payload}")
                
                # Check expiration
                if "exp" in payload:
                    exp_time = datetime.fromtimestamp(payload["exp"])
                    print(f"Token expires at: {exp_time}")
                    print(f"Token valid for: {(exp_time - datetime.now()).total_seconds() / 60:.1f} minutes")
        except Exception as e:
            print(f"Failed to decode JWT: {e}")

async def test_request_headers():
    """Test 6: Required headers analysis"""
    print("\n=== TEST 6: Request Headers Analysis ===")
    async with httpx.AsyncClient() as client:
        # Get token first
        resp = await client.post(f"{API_BASE}/api/auth/login", 
                                data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD})
        if resp.status_code != 200:
            print("Failed to get token")
            return
        
        access_token = resp.json()["access_token"]
        
        # Test different header combinations
        test_cases = [
            {"name": "Minimal", "headers": {"Authorization": f"Bearer {access_token}"}},
            {"name": "With Origin", "headers": {"Authorization": f"Bearer {access_token}", "Origin": FRONTEND_BASE}},
            {"name": "With Referer", "headers": {"Authorization": f"Bearer {access_token}", "Referer": FRONTEND_BASE}},
            {"name": "Full browser headers", "headers": {
                "Authorization": f"Bearer {access_token}",
                "Origin": FRONTEND_BASE,
                "Referer": f"{FRONTEND_BASE}/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache"
            }}
        ]
        
        for test in test_cases:
            try:
                resp = await client.get(f"{API_BASE}/api/auth/me", headers=test["headers"])
                print(f"{test['name']}: {resp.status_code} - {'OK' if resp.status_code == 200 else 'FAIL'}")
            except Exception as e:
                print(f"{test['name']}: ERROR - {e}")

async def main():
    """Run all tests"""
    print("=== HoistScout API Connection Debugger ===")
    print(f"API URL: {API_BASE}")
    print(f"Frontend URL: {FRONTEND_BASE}")
    print(f"Test credentials: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    
    await test_basic_connectivity()
    await test_cors_headers()
    tokens = await test_login_flow()
    
    if tokens:
        await test_auth_endpoints(tokens["access_token"])
        await test_token_validation()
        await test_request_headers()
    else:
        print("\nFailed to obtain access token - skipping authenticated tests")
    
    print("\n=== Summary of Issues Found ===")
    print("1. Check if API service is actually running on Render")
    print("2. Verify CORS is properly configured for frontend URL")
    print("3. Ensure OAuth2 form data format is accepted")
    print("4. Confirm /api/auth/me endpoint exists and works")
    print("5. Validate JWT token structure and expiration")

if __name__ == "__main__":
    asyncio.run(main())