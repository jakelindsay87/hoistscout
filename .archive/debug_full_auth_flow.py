#!/usr/bin/env python3
"""Debug the complete authentication flow including database lookup"""
import httpx
import asyncio
import json

API_BASE = "https://hoistscout-api.onrender.com"

async def debug_auth_flow():
    """Test authentication with detailed debugging"""
    print("=== Debugging Full Authentication Flow ===\n")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Login
        print("1. Logging in...")
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            data={"username": "demo@hoistscout.com", "password": "demo123"}
        )
        
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
            
        token = resp.json()["access_token"]
        print("✓ Login successful\n")
        
        # Step 2: Test different endpoints
        endpoints = [
            ("/api/auth/me", "GET"),
            ("/api/auth/profile", "GET"),
            ("/api/websites", "GET"),  # Test a different protected endpoint
            ("/", "GET"),  # Test unprotected endpoint
        ]
        
        for endpoint, method in endpoints:
            print(f"Testing {method} {endpoint}...")
            
            headers = {}
            if endpoint != "/":
                headers["Authorization"] = f"Bearer {token}"
            
            if method == "GET":
                resp = await client.get(f"{API_BASE}{endpoint}", headers=headers)
            
            print(f"  Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"  Error: {resp.text}")
            else:
                print(f"  Success: {resp.json() if resp.headers.get('content-type', '').startswith('application/json') else 'OK'}")
            print()
        
        # Step 3: Test with wrong token format
        print("3. Testing with malformed tokens...")
        
        bad_tokens = [
            ("No Bearer prefix", token),
            ("Wrong prefix", f"Token {token}"),
            ("Extra space", f"Bearer  {token}"),
            ("Lowercase bearer", f"bearer {token}"),
            ("Invalid token", "Bearer invalid.token.here"),
        ]
        
        for desc, bad_token in bad_tokens:
            print(f"  {desc}: ", end="")
            resp = await client.get(
                f"{API_BASE}/api/auth/me",
                headers={"Authorization": bad_token}
            )
            print(f"{resp.status_code} - {resp.json().get('detail', 'Unknown error')}")

async def test_database_connection():
    """Test if the issue is database-related"""
    print("\n=== Testing Database Connection ===")
    
    async with httpx.AsyncClient() as client:
        # Try to access public endpoints that might reveal DB issues
        resp = await client.get(f"{API_BASE}/docs")
        print(f"API Docs accessible: {resp.status_code == 200}")
        
        # Check if we can create a new user (might reveal DB issues)
        print("\nTesting user registration (to check DB write)...")
        test_user = {
            "email": f"test{int(asyncio.get_event_loop().time())}@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        resp = await client.post(
            f"{API_BASE}/api/auth/register",
            json=test_user
        )
        
        print(f"Registration status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Registration error: {resp.text}")
            if "connection" in resp.text.lower() or "database" in resp.text.lower():
                print("⚠️  Database connection issue detected!")

async def main():
    await debug_auth_flow()
    await test_database_connection()
    
    print("\n=== Diagnosis ===")
    print("Common causes of 401 after successful login:")
    print("1. Database connection issues (can't lookup user)")
    print("2. User ID mismatch (JWT has ID that doesn't exist)")
    print("3. OAuth2PasswordBearer tokenUrl mismatch")
    print("4. Middleware interfering with Authorization header")
    print("5. Async database session issues")

if __name__ == "__main__":
    asyncio.run(main())