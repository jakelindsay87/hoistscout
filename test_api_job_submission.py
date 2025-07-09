#!/usr/bin/env python3
"""Test job submission through the API"""
import requests
import json
from datetime import datetime

# API configuration
API_URL = "https://hoistscout-api.onrender.com"
# We need to get an auth token first

print("Testing HoistScout API Job Submission...")
print("=" * 60)

# First, let's check if the API is healthy
health_response = requests.get(f"{API_URL}/api/health", timeout=10)
print(f"API Health Check: {health_response.status_code}")
if health_response.status_code == 200:
    print(f"Response: {health_response.json()}")
else:
    print(f"Error: {health_response.text}")

# Try to login with demo credentials
print("\nAttempting login...")
# OAuth2PasswordRequestForm expects 'username' and 'password' fields
login_data = {
    "username": "demo",  # Special case in the API that maps to demo@hoistscout.com
    "password": "demo123"
}

try:
    # Use form data instead of JSON
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        data=login_data,  # Using data instead of json for form-encoded
        timeout=10
    )
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        print("✅ Login successful!")
        
        # Create headers with token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get websites
        print("\nFetching websites...")
        websites_response = requests.get(
            f"{API_URL}/api/websites",
            headers=headers,
            timeout=10
        )
        
        if websites_response.status_code == 200:
            websites = websites_response.json()
            print(f"Found {len(websites)} websites")
            
            if websites:
                # Create a job for the first website
                website = websites[0]
                print(f"\nCreating job for: {website['name']} (ID: {website['id']})")
                
                job_data = {
                    "website_id": website['id'],
                    "job_type": "test",  # Must be 'full', 'incremental', or 'test'
                    "priority": 5
                }
                
                job_response = requests.post(
                    f"{API_URL}/api/scraping/jobs",
                    json=job_data,
                    headers=headers,
                    timeout=10
                )
                
                if job_response.status_code == 200:
                    job = job_response.json()
                    print(f"✅ Job created successfully!")
                    print(f"   Job ID: {job['id']}")
                    print(f"   Status: {job['status']}")
                    print(f"   Created at: {job['created_at']}")
                else:
                    print(f"❌ Failed to create job: {job_response.status_code}")
                    print(f"   Error: {job_response.text}")
            else:
                print("❌ No websites found to create jobs for")
        else:
            print(f"❌ Failed to fetch websites: {websites_response.status_code}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"   Error: {login_response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request error: {e}")

print("\n" + "=" * 60)
print("Check worker logs at:")
print("https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")