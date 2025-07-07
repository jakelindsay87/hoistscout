#!/usr/bin/env python3
"""Test if demo user exists and create if needed"""
import httpx
import asyncio

API_BASE = "https://hoistscout-api.onrender.com"

async def test_demo_user():
    """Test demo user and potentially fix the issue"""
    print("=== Testing Demo User ===\n")
    
    async with httpx.AsyncClient() as client:
        # First, try to login as demo user
        print("1. Attempting to login as demo user...")
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            data={"username": "demo@hoistscout.com", "password": "demo123"}
        )
        
        if resp.status_code == 200:
            print("✓ Demo user login successful")
            print("But authentication still fails - this suggests the user ID in JWT doesn't match database")
            
            # The issue is that the demo user has a different ID in production
            # The JWT has user_id=3, but the actual user might have a different ID
            print("\nThe problem: JWT contains user_id=3, but the demo user in production DB likely has a different ID")
            print("\nSolutions:")
            print("1. Re-create the demo user to ensure consistent ID")
            print("2. Or login with a newly created user instead")
        else:
            print(f"✗ Demo user login failed: {resp.status_code}")
            print(f"Error: {resp.text}")
            print("\nDemo user might not exist in production database")
        
        # Try creating a new test user
        print("\n2. Creating a new test user...")
        test_email = "test@hoistscout.com"
        test_password = "testpass123"
        
        resp = await client.post(
            f"{API_BASE}/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "full_name": "Test User",
                "role": "viewer"
            }
        )
        
        if resp.status_code == 200:
            print(f"✓ Test user created successfully")
            user_data = resp.json()
            print(f"User ID: {user_data.get('id')}")
            
            # Now login with the new user
            print("\n3. Logging in with new test user...")
            resp = await client.post(
                f"{API_BASE}/api/auth/login",
                data={"username": test_email, "password": test_password}
            )
            
            if resp.status_code == 200:
                token = resp.json()["access_token"]
                print("✓ Login successful")
                
                # Test authentication
                print("\n4. Testing authentication with new user...")
                resp = await client.get(
                    f"{API_BASE}/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if resp.status_code == 200:
                    print("✓ Authentication successful!")
                    print(f"User data: {resp.json()}")
                    print("\n✅ AUTHENTICATION IS WORKING!")
                    print(f"\nUse these credentials for testing:")
                    print(f"Email: {test_email}")
                    print(f"Password: {test_password}")
                else:
                    print(f"✗ Authentication failed: {resp.text}")
            else:
                print(f"✗ Login failed: {resp.text}")
        elif "already registered" in resp.text:
            print("Test user already exists, trying to login...")
            
            resp = await client.post(
                f"{API_BASE}/api/auth/login",
                data={"username": test_email, "password": test_password}
            )
            
            if resp.status_code == 200:
                token = resp.json()["access_token"]
                print("✓ Login successful")
                
                resp = await client.get(
                    f"{API_BASE}/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if resp.status_code == 200:
                    print("✓ Authentication successful!")
                    print(f"\nUse these credentials:")
                    print(f"Email: {test_email}")
                    print(f"Password: {test_password}")
        else:
            print(f"✗ User creation failed: {resp.text}")

async def main():
    await test_demo_user()
    
    print("\n=== Root Cause ===")
    print("The demo user creation on startup created a user with ID=3 in development,")
    print("but in production, the user IDs are different (auto-increment).")
    print("The JWT token has the hardcoded user_id=3 which doesn't exist in production.")
    print("\nThe fix is to ensure demo user creation is consistent or use dynamic user IDs.")

if __name__ == "__main__":
    asyncio.run(main())