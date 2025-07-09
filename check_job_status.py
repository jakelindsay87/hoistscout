#!/usr/bin/env python3
"""Check job status through the API"""
import requests
import time
import json

# API configuration
API_URL = "https://hoistscout-api.onrender.com"

print("Checking Job Status...")
print("=" * 60)

# Login first
login_data = {
    "username": "demo",
    "password": "demo123"
}

login_response = requests.post(
    f"{API_URL}/api/auth/login",
    data=login_data,
    timeout=10
)

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data.get("access_token")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get recent jobs
    jobs_response = requests.get(
        f"{API_URL}/api/scraping/jobs?limit=10",
        headers=headers,
        timeout=10
    )
    
    if jobs_response.status_code == 200:
        jobs = jobs_response.json()
        print(f"Found {len(jobs)} recent jobs:\n")
        
        for job in jobs:
            status_emoji = {
                "pending": "⏳",
                "running": "🏃",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(job['status'], "❓")
            
            print(f"Job ID: {job['id']} - {status_emoji} {job['status']}")
            print(f"  Website ID: {job['website_id']}")
            print(f"  Type: {job['job_type']}")
            print(f"  Created: {job['created_at']}")
            if job.get('started_at'):
                print(f"  Started: {job['started_at']}")
            if job.get('completed_at'):
                print(f"  Completed: {job['completed_at']}")
            if job.get('error_message'):
                print(f"  Error: {job['error_message']}")
            print()
    else:
        print(f"Failed to fetch jobs: {jobs_response.status_code}")
else:
    print(f"Login failed: {login_response.status_code}")

print("=" * 60)
print("Worker Dashboard: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")