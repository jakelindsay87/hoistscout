#!/usr/bin/env python3
"""Final JWT debugging - decode actual tokens from API"""
import httpx
import jwt
import asyncio
import json

API_BASE = "https://hoistscout-api.onrender.com"

async def decode_actual_token():
    """Get a fresh token and decode it"""
    print("=== Decoding Actual JWT Tokens ===\n")
    
    async with httpx.AsyncClient() as client:
        # Login to get fresh token
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            data={"username": "test@hoistscout.com", "password": "testpass123"}
        )
        
        if resp.status_code != 200:
            print("Login failed, trying demo user...")
            resp = await client.post(
                f"{API_BASE}/api/auth/login",
                data={"username": "demo@hoistscout.com", "password": "demo123"}
            )
        
        if resp.status_code == 200:
            tokens = resp.json()
            access_token = tokens["access_token"]
            
            print("Token obtained successfully")
            print(f"Token (first 50 chars): {access_token[:50]}...")
            
            # Decode without verification to see exact payload
            try:
                header = jwt.get_unverified_header(access_token)
                payload = jwt.decode(access_token, options={"verify_signature": False})
                
                print(f"\nToken Header:")
                print(json.dumps(header, indent=2))
                
                print(f"\nToken Payload:")
                print(json.dumps(payload, indent=2))
                
                # Check specific fields
                print(f"\nField Analysis:")
                print(f"- 'sub' field: {payload.get('sub')} (type: {type(payload.get('sub'))})")
                print(f"- 'type' field: {payload.get('type')} (expected: 'access')")
                print(f"- 'email' field: {payload.get('email')}")
                print(f"- 'role' field: {payload.get('role')}")
                
                # Check if 'type' field is missing
                if 'type' not in payload:
                    print("\n⚠️  WARNING: 'type' field is missing from token!")
                    print("This is likely the issue - the verify_token function expects it")
                
            except Exception as e:
                print(f"Error decoding token: {e}")

async def main():
    await decode_actual_token()
    
    print("\n=== Solution ===")
    print("If 'type' field is missing from the token, the issue is in create_access_token()")
    print("The function needs to add 'type': 'access' to the token payload")

if __name__ == "__main__":
    asyncio.run(main())