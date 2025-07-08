#!/usr/bin/env python3
"""Test HoistScout deployment status"""

import requests
import json
import sys
import time

BASE_URL = "https://hoistscout-api.onrender.com"

def test_health():
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_login():
    """Test login with demo credentials"""
    print("\n2. Testing login endpoint...")
    login_data = {
        "username": "demo@hoistscout.com",
        "password": "demo123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   Access Token: {token_data.get('access_token', 'Not found')[:50]}...")
            return token_data.get('access_token')
        else:
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ERROR: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint"""
    print("\n3. Testing protected endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test websites endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/websites/", headers=headers)
        print(f"   Websites Endpoint - Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Websites: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

def test_scraping_endpoints(token):
    """Test scraping endpoints"""
    print("\n4. Testing scraping endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test opportunities endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/opportunities/", headers=headers)
        print(f"   Opportunities Endpoint - Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test scraping jobs endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/scraping/jobs/", headers=headers)
        print(f"   Scraping Jobs - Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")

def check_gemini_config(token):
    """Check if Gemini is properly configured"""
    print("\n5. Checking Gemini configuration...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create a test website to see if Gemini errors appear
    test_data = {
        "url": "https://example.com",
        "name": "Test Site",
        "industry": "Technology",
        "scrape_interval": 24
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/websites/",
            json=test_data,
            headers=headers
        )
        print(f"   Create Website Test - Status Code: {response.status_code}")
        if response.status_code == 201:
            print("   ✅ Website creation successful")
            website_id = response.json().get("id")
            # Try to delete the test website
            if website_id:
                del_response = requests.delete(
                    f"{BASE_URL}/api/websites/{website_id}",
                    headers=headers
                )
                print(f"   Cleanup - Status Code: {del_response.status_code}")
        elif response.status_code != 200:
            error_text = response.text
            if "GOOGLE_GEMINI_API_KEY" in error_text or "gemini" in error_text.lower():
                print("   ⚠️  GEMINI NOT CONFIGURED: API key environment variable missing")
            else:
                print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   ERROR: {e}")

def main():
    print("=== HoistScout Deployment Status Check ===\n")
    
    # Test health
    health_ok = test_health()
    if not health_ok:
        print("\n❌ Health check failed. API may not be running.")
        sys.exit(1)
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Login failed. Authentication system may have issues.")
        sys.exit(1)
    
    # Test protected endpoints
    test_protected_endpoint(token)
    
    # Test scraping endpoints
    test_scraping_endpoints(token)
    
    # Check Gemini configuration
    check_gemini_config(token)
    
    # Test creating a scraping job
    test_scraping_job(token)
    
    print("\n=== Summary ===")
    print("✅ API is running and healthy")
    print("✅ Authentication system is working")
    print("📋 Check the output above for any warnings about Gemini configuration")

def test_scraping_job(token):
    """Test creating a scraping job to check Gemini integration"""
    print("\n6. Testing scraping job creation (Gemini check)...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # First get a website ID
    try:
        response = requests.get(f"{BASE_URL}/api/websites/", headers=headers)
        if response.status_code == 200:
            websites = response.json()
            if websites:
                website_id = websites[0]["id"]
                
                # Create a scraping job
                job_data = {
                    "website_id": website_id,
                    "job_type": "full",
                    "priority": 1
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/scraping/jobs/",
                    json=job_data,
                    headers=headers
                )
                print(f"   Create Scraping Job - Status Code: {response.status_code}")
                
                if response.status_code == 201 or response.status_code == 200:
                    print("   ✅ Scraping job created successfully")
                    job_id = response.json().get("id")
                    
                    # Check job status
                    if job_id:
                        # Wait a moment for the job to start processing
                        time.sleep(2)
                        status_response = requests.get(
                            f"{BASE_URL}/api/scraping/jobs/{job_id}",
                            headers=headers
                        )
                        if status_response.status_code == 200:
                            job_status = status_response.json()
                            print(f"   Job Status: {job_status.get('status', 'Unknown')}")
                            if job_status.get('error'):
                                error_msg = job_status.get('error')
                                if "GOOGLE_GEMINI_API_KEY" in error_msg or "gemini" in error_msg.lower():
                                    print("   ⚠️  GEMINI NOT CONFIGURED: API key environment variable missing")
                                else:
                                    print(f"   Job Error: {error_msg}")
                else:
                    error_text = response.text
                    if "GOOGLE_GEMINI_API_KEY" in error_text or "gemini" in error_text.lower():
                        print("   ⚠️  GEMINI NOT CONFIGURED: API key environment variable missing")
                    else:
                        print(f"   Error: {error_text}")
            else:
                print("   No websites available to test")
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    main()