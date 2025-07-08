#!/usr/bin/env python3
"""Check worker and job status"""
import requests
import json

API_BASE = "https://hoistscout-api.onrender.com"

# Login
login_data = {
    "username": "demo",
    "password": "demo123",
    "grant_type": "password"
}

response = requests.post(
    f"{API_BASE}/api/auth/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10
)

token = response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Get all jobs
print("=== All Scraping Jobs ===")
resp = requests.get(f"{API_BASE}/api/scraping/jobs/", headers=headers)
jobs = resp.json()

for job in jobs[:10]:  # Show last 10
    print(f"\nJob ID: {job['id']}")
    print(f"  Website ID: {job.get('website_id')}")
    print(f"  Status: {job.get('status')}")
    print(f"  Type: {job.get('job_type')}")
    print(f"  Created: {job.get('created_at')}")
    print(f"  Started: {job.get('started_at')}")
    print(f"  Completed: {job.get('completed_at')}")
    if job.get('error_message'):
        print(f"  Error: {job.get('error_message')}")
    if job.get('stats'):
        print(f"  Stats: {json.dumps(job.get('stats'), indent=4)}")

# Check websites
print("\n\n=== Websites ===")
resp = requests.get(f"{API_BASE}/api/websites/", headers=headers)
websites = resp.json()

for site in websites:
    if "tenders" in site.get("url", "").lower():
        print(f"\nWebsite: {site['name']} (ID: {site['id']})")
        print(f"  URL: {site['url']}")
        print(f"  Active: {site.get('is_active')}")
        print(f"  Config: {json.dumps(site.get('scraping_config'), indent=4)}")

# Check if there are any opportunities
print("\n\n=== Opportunities Count ===")
resp = requests.get(f"{API_BASE}/api/opportunities/", headers=headers)
opps = resp.json()
print(f"Total opportunities in system: {len(opps)}")

if opps:
    print("\nFirst opportunity:")
    print(json.dumps(opps[0], indent=2))