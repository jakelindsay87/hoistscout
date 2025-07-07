#!/usr/bin/env python3
"""
Comprehensive end-to-end test for HoistScout
Tests the complete workflow: login → add website → trigger scrape → view results
"""
import requests
import time
import json
import sys
from datetime import datetime

API_BASE = "https://hoistscout-api.onrender.com"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_success(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")
    
    def add_failure(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"✗ {test_name}: {error}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*50}\n")
        return self.failed == 0

def test_auth_endpoints(token, results):
    """Test authentication endpoints"""
    print("\n1. Testing Authentication Endpoints")
    print("-" * 30)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /api/auth/me
    try:
        resp = requests.get(f"{API_BASE}/api/auth/me", headers=headers, timeout=5)
        if resp.status_code == 200:
            user = resp.json()
            results.add_success(f"/api/auth/me - User: {user['email']}, Role: {user['role']}")
        else:
            results.add_failure("/api/auth/me", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/auth/me", str(e))
    
    # Test /api/auth/profile
    try:
        resp = requests.get(f"{API_BASE}/api/auth/profile", headers=headers, timeout=5)
        if resp.status_code == 200:
            results.add_success("/api/auth/profile")
        else:
            results.add_failure("/api/auth/profile", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/auth/profile", str(e))

def test_crud_endpoints(token, results):
    """Test CRUD endpoints"""
    print("\n2. Testing CRUD Endpoints")
    print("-" * 30)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test websites endpoint
    try:
        resp = requests.get(f"{API_BASE}/api/websites/", headers=headers, timeout=5)
        if resp.status_code == 200:
            websites = resp.json()
            results.add_success(f"/api/websites/ - Found {len(websites)} websites")
        else:
            results.add_failure("/api/websites/", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/websites/", str(e))
    
    # Test opportunities endpoint
    try:
        resp = requests.get(f"{API_BASE}/api/opportunities/", headers=headers, timeout=5)
        if resp.status_code == 200:
            opps = resp.json()
            results.add_success(f"/api/opportunities/ - Found {len(opps)} opportunities")
        else:
            results.add_failure("/api/opportunities/", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/opportunities/", str(e))
    
    # Test jobs endpoint
    try:
        resp = requests.get(f"{API_BASE}/api/scraping/jobs/", headers=headers, timeout=5)
        if resp.status_code == 200:
            jobs = resp.json()
            results.add_success(f"/api/scraping/jobs/ - Found {len(jobs)} jobs")
        else:
            results.add_failure("/api/scraping/jobs/", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/scraping/jobs/", str(e))

def test_website_workflow(token, results):
    """Test complete website workflow"""
    print("\n3. Testing Website Workflow")
    print("-" * 30)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a test website
    test_website = {
        "name": f"Test Site {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "url": f"https://test-{datetime.now().strftime('%Y%m%d%H%M%S')}.example.com",
        "category": "test",
        "scraping_config": {
            "search_patterns": ["grant", "funding", "opportunity"],
            "max_depth": 2
        },
        "is_active": True
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/websites/", 
            headers=headers, 
            json=test_website,
            timeout=10
        )
        if resp.status_code in [200, 201]:
            website = resp.json()
            website_id = website['id']
            results.add_success(f"Created website: {website['name']} (ID: {website_id})")
            
            # Test getting the specific website
            resp = requests.get(
                f"{API_BASE}/api/websites/{website_id}", 
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                results.add_success(f"Retrieved website {website_id}")
            else:
                results.add_failure(f"GET /api/websites/{website_id}", f"Status {resp.status_code}")
            
            return website_id
        else:
            results.add_failure("POST /api/websites/", f"Status {resp.status_code}: {resp.text[:100]}")
            return None
    except Exception as e:
        results.add_failure("POST /api/websites/", str(e))
        return None

def test_scraping_workflow(token, website_id, results):
    """Test scraping job workflow"""
    print("\n4. Testing Scraping Workflow")
    print("-" * 30)
    
    if not website_id:
        results.add_failure("Scraping workflow", "No website ID available")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a scraping job
    job_data = {
        "website_id": website_id,
        "job_type": "test",
        "priority": 5
    }
    
    try:
        resp = requests.post(
            f"{API_BASE}/api/scraping/jobs/",
            headers=headers,
            json=job_data,
            timeout=10
        )
        if resp.status_code in [200, 201]:
            job = resp.json()
            job_id = job['id']
            results.add_success(f"Created scraping job: {job_id}")
            
            # Check job status
            time.sleep(2)  # Give it a moment to process
            resp = requests.get(
                f"{API_BASE}/api/scraping/jobs/{job_id}",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                job_status = resp.json()
                results.add_success(f"Job status: {job_status.get('status', 'unknown')}")
            else:
                results.add_failure(f"GET /api/scraping/jobs/{job_id}", f"Status {resp.status_code}")
        else:
            results.add_failure("POST /api/scraping/jobs/", f"Status {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        results.add_failure("POST /api/scraping/jobs/", str(e))

def test_health_endpoints(results):
    """Test health check endpoints"""
    print("\n5. Testing Health Endpoints")
    print("-" * 30)
    
    # Test basic health
    try:
        resp = requests.get(f"{API_BASE}/api/health", timeout=5)
        if resp.status_code == 200:
            results.add_success("/api/health")
        else:
            results.add_failure("/api/health", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/health", str(e))
    
    # Test ready endpoint
    try:
        resp = requests.get(f"{API_BASE}/api/health/ready", timeout=5)
        if resp.status_code == 200:
            results.add_success("/api/health/ready")
        else:
            results.add_failure("/api/health/ready", f"Status {resp.status_code}")
    except Exception as e:
        results.add_failure("/api/health/ready", str(e))

def main():
    print("=" * 50)
    print("HoistScout End-to-End Test Suite")
    print("=" * 50)
    
    results = TestResult()
    
    # First, test health endpoints (no auth required)
    test_health_endpoints(results)
    
    # Login
    print("\nLogging in...")
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
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✓ Login successful")
            
            # Run all tests
            test_auth_endpoints(token, results)
            test_crud_endpoints(token, results)
            website_id = test_website_workflow(token, results)
            test_scraping_workflow(token, website_id, results)
            
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False
    
    # Print summary
    return results.print_summary()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)