#\!/usr/bin/env python3
"""Verify HoistScout deployment and job processing"""
import os
import sys
import time
import requests
import json

API_URL = "https://hoistscout-api.onrender.com"

def login():
    """Login and get auth token"""
    print("1. Logging in...")
    response = requests.post(
        f"{API_URL}/api/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"username": "demo", "password": "demo123"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def check_health(token):
    """Check API health"""
    print("\n2. Checking API health...")
    response = requests.get(f"{API_URL}/api/health")
    if response.status_code == 200:
        print(f"✓ API is healthy: {response.json()}")
    else:
        print(f"✗ API health check failed: {response.status_code}")

def list_websites(token):
    """List websites"""
    print("\n3. Listing websites...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/websites/", headers=headers)
    if response.status_code == 200:
        websites = response.json()
        print(f"✓ Found {len(websites)} websites")
        for w in websites[:3]:
            print(f"  - ID: {w['id']}, Name: {w['name']}, URL: {w['url']}")
        return websites
    else:
        print(f"✗ Failed to list websites: {response.status_code}")
        return []

def create_job(token, website_id):
    """Create a scraping job"""
    print(f"\n4. Creating scraping job for website {website_id}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "website_id": website_id,
        "job_type": "test",
        "priority": 10
    }
    response = requests.post(
        f"{API_URL}/api/scraping/jobs/",
        headers=headers,
        json=data
    )
    if response.status_code == 200 or response.status_code == 201:
        job = response.json()
        print(f"✓ Job created: ID={job['id']}, Status={job['status']}")
        return job['id']
    else:
        print(f"✗ Failed to create job: {response.status_code} - {response.text}")
        return None

def check_job_status(token, job_id, max_wait=60):
    """Check job status"""
    print(f"\n5. Monitoring job {job_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(max_wait // 5):
        response = requests.get(
            f"{API_URL}/api/scraping/jobs/{job_id}",
            headers=headers
        )
        if response.status_code == 200:
            job = response.json()
            print(f"  [{i*5}s] Status: {job['status']}", end="")
            
            if job['started_at']:
                print(f" (started at {job['started_at']})", end="")
            if job['completed_at']:
                print(f" (completed at {job['completed_at']})", end="")
            if job['error_message']:
                print(f" ERROR: {job['error_message']}", end="")
            print()
            
            if job['status'] in ['completed', 'failed']:
                return job
        else:
            print(f"✗ Failed to check job: {response.status_code}")
            return None
        
        time.sleep(5)
    
    print("✗ Job did not complete within timeout")
    return None

def check_opportunities(token):
    """Check if any opportunities were created"""
    print("\n6. Checking opportunities...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/opportunities/", headers=headers)
    
    if response.status_code == 200:
        opportunities = response.json()
        print(f"✓ Found {len(opportunities)} opportunities")
        for opp in opportunities[:3]:
            print(f"  - {opp.get('title', 'No title')}")
    else:
        print(f"✗ Failed to check opportunities: {response.status_code}")

def main():
    print("=" * 80)
    print("HOISTSCOUT DEPLOYMENT VERIFICATION")
    print("=" * 80)
    
    # Login
    token = login()
    if not token:
        print("\nFailed at login stage. API might not be deployed correctly.")
        return
    
    # Check health
    check_health(token)
    
    # List websites
    websites = list_websites(token)
    if not websites:
        print("\nNo websites found. Cannot proceed with job creation.")
        return
    
    # Create job for first website
    website_id = websites[0]['id']
    job_id = create_job(token, website_id)
    if not job_id:
        print("\nFailed to create job. Check API logs for Celery connection issues.")
        return
    
    # Monitor job
    final_job = check_job_status(token, job_id)
    if final_job and final_job['status'] == 'completed':
        print("\n✅ SUCCESS\! Job was processed by the worker\!")
        check_opportunities(token)
    elif final_job and final_job['status'] == 'failed':
        print(f"\n❌ Job failed with error: {final_job.get('error_message', 'Unknown error')}")
    else:
        print("\n❌ Job is still pending. Worker might not be processing tasks.")
        print("\nPossible issues:")
        print("1. Worker not running or crashed")
        print("2. Redis connection issues")
        print("3. Task not being sent to Celery queue")
        print("4. Worker not listening to correct queue")

if __name__ == "__main__":
    main()
