#!/usr/bin/env python3
import requests
import json

# Login
login_resp = requests.post(
    "https://hoistscout-api.onrender.com/api/auth/login",
    data={"username": "demo", "password": "demo123"}
)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get jobs
jobs_resp = requests.get(
    "https://hoistscout-api.onrender.com/api/scraping/jobs?limit=5",
    headers=headers
)
jobs = jobs_resp.json()

print(f"Total jobs: {len(jobs)}")
print("\nJob statuses:")
status_counts = {}
for job in jobs:
    status = job.get("status", "unknown")
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in status_counts.items():
    print(f"  {status}: {count}")

# Show first few jobs
print("\nRecent jobs:")
for job in jobs[:3]:
    print(f"  ID: {job['id']}, Status: {job['status']}, Created: {job['created_at'][:19]}")

# Check for running jobs
running = [j for j in jobs if j.get("status") == "running"]
if running:
    print(f"\n✅ Worker is processing! {len(running)} jobs running")
else:
    print("\n❌ No jobs currently running - worker may need attention")