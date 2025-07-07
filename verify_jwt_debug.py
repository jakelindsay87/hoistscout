#!/usr/bin/env python3
"""Debug JWT verification with the new SECRET_KEY"""
import httpx
import jwt
import asyncio
import json
from datetime import datetime

# Update this with your new SECRET_KEY
SECRET_KEY = "ldV%0YU9gZ(!Iq()Mcs=obbqgzLVlA4GQM&-%-U*%LDoL5x_X=qu)o@RaWohIrK&"
API_BASE = "https://hoistscout-api.onrender.com"

async def test_jwt_verification():
    """Test the complete authentication flow"""
    print("=== Testing HoistScout Authentication ===\n")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Test login
        print("1. Testing login endpoint...")
        login_data = {
            "username": "demo@hoistscout.com",
            "password": "demo123"
        }
        
        try:
            resp = await client.post(
                f"{API_BASE}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"   Status: {resp.status_code}")
            print(f"   Headers: {dict(resp.headers)}")
            
            if resp.status_code != 200:
                print(f"   Error: {resp.text}")
                return
            
            tokens = resp.json()
            access_token = tokens.get("access_token")
            print(f"   ✓ Login successful, token received")
            
            # Step 2: Decode and verify token locally
            print("\n2. Decoding JWT token...")
            try:
                # Try decoding with the new secret
                payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])
                print(f"   ✓ Token decoded successfully!")
                print(f"   User ID: {payload.get('sub')}")
                print(f"   Email: {payload.get('email')}")
                print(f"   Role: {payload.get('role')}")
                exp = datetime.fromtimestamp(payload.get('exp', 0))
                print(f"   Expires: {exp} (in {(exp - datetime.now()).seconds // 60} minutes)")
            except jwt.InvalidTokenError as e:
                print(f"   ✗ Token decode failed: {type(e).__name__}: {e}")
                print(f"   This means the API is using a different SECRET_KEY!")
                
                # Try to decode without verification to see payload
                try:
                    unverified = jwt.decode(access_token, options={"verify_signature": False})
                    print(f"\n   Token payload (unverified):")
                    print(f"   {json.dumps(unverified, indent=2)}")
                except Exception as e2:
                    print(f"   Could not decode token at all: {e2}")
            
            # Step 3: Test authenticated endpoint
            print("\n3. Testing authenticated endpoint /api/auth/me...")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            me_resp = await client.get(
                f"{API_BASE}/api/auth/me",
                headers=headers
            )
            
            print(f"   Status: {me_resp.status_code}")
            print(f"   Headers: {dict(me_resp.headers)}")
            
            if me_resp.status_code == 200:
                user_data = me_resp.json()
                print(f"   ✓ Authentication successful!")
                print(f"   User data: {json.dumps(user_data, indent=2)}")
            else:
                print(f"   ✗ Authentication failed: {me_resp.text}")
                
                # Additional debugging
                print("\n4. Additional checks...")
                
                # Check if it's a CORS issue
                print("   - Testing CORS preflight...")
                options_resp = await client.options(
                    f"{API_BASE}/api/auth/me",
                    headers={
                        "Origin": "https://hoistscout-frontend.onrender.com",
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "authorization"
                    }
                )
                print(f"     CORS Status: {options_resp.status_code}")
                print(f"     CORS Headers: {dict(options_resp.headers)}")
                
        except Exception as e:
            print(f"   Error: {type(e).__name__}: {e}")

async def test_direct_api_info():
    """Get API information"""
    print("\n=== API Information ===")
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        resp = await client.get(f"{API_BASE}/")
        if resp.status_code == 200:
            print(f"API Version: {resp.json()}")
        
        # Test docs endpoint
        resp = await client.get(f"{API_BASE}/docs")
        print(f"API Docs available: {resp.status_code == 200}")

async def main():
    await test_direct_api_info()
    await test_jwt_verification()
    
    print("\n=== Diagnosis ===")
    print("If the token decode fails, it means:")
    print("1. The API hasn't redeployed with the new SECRET_KEY yet")
    print("2. Or there's a mismatch in the SECRET_KEY value")
    print("\nCheck Render dashboard to ensure:")
    print("- Both API and Worker services have redeployed")
    print("- The SECRET_KEY is exactly the same (no quotes or spaces)")
    print("- The services show as 'Live' after deploy")

if __name__ == "__main__":
    asyncio.run(main())