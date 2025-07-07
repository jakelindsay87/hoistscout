#!/usr/bin/env python3
"""Debug JWT token verification issue"""
import httpx
import asyncio
from jose import jwt, JWTError
import json

API_BASE = "https://hoistscout-api.onrender.com"

async def debug_jwt_verification():
    """Debug JWT token creation and verification"""
    print("=== JWT Token Verification Debug ===\n")
    
    # Step 1: Get a token from the API
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_BASE}/api/auth/login", 
                                data={"username": "demo@hoistscout.com", "password": "demo123"})
        
        if resp.status_code != 200:
            print(f"Failed to get token: {resp.status_code}")
            return
        
        tokens = resp.json()
        access_token = tokens["access_token"]
        print(f"Token obtained successfully\n")
        
        # Step 2: Try to decode the token with different secret keys
        test_secrets = [
            "hoistscout-dev-secret-key-change-in-production-make-it-long-and-random",  # Default in config
            "your-secret-key-here",  # Common placeholder
            "secret",  # Simple default
            "hoistscout-secret-key",  # Possible production value
        ]
        
        print("Testing different secret keys:")
        for secret in test_secrets:
            try:
                payload = jwt.decode(access_token, secret, algorithms=["HS256"])
                print(f"✅ SUCCESS with secret: '{secret[:20]}...'")
                print(f"   Payload: {payload}")
                break
            except JWTError as e:
                print(f"❌ Failed with secret: '{secret[:20]}...' - {type(e).__name__}")
        
        # Step 3: Test the token with the API
        print("\nTesting token with API endpoints:")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Try different endpoints
        endpoints = ["/api/auth/me", "/api/auth/profile"]
        for endpoint in endpoints:
            resp = await client.get(f"{API_BASE}{endpoint}", headers=headers)
            print(f"{endpoint}: {resp.status_code} - {resp.text[:100] if resp.status_code != 200 else 'OK'}")

if __name__ == "__main__":
    asyncio.run(debug_jwt_verification())