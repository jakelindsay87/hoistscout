#!/usr/bin/env python3
"""Monitor the FINAL worker fix - removed broken DB test"""
import requests
import time
from datetime import datetime

RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
WORKER_ID = "srv-d1hlvanfte5s73ad476g"
API_URL = "https://hoistscout-api.onrender.com"

print("🚀 FINAL WORKER FIX DEPLOYMENT")
print("=" * 70)
print("Fix: Removed broken async database test that was causing:")
print("  'The asyncio extension requires an async driver to be used'")
print("=" * 70)

# Monitor deployment
headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
start = time.time()

while (time.time() - start) < 600:
    resp = requests.get(f"https://api.render.com/v1/services/{WORKER_ID}/deploys?limit=1", headers=headers)
    if resp.status_code == 200:
        deploy = resp.json()[0]["deploy"]
        status = deploy["status"]
        commit = deploy.get("commit", {}).get("message", "")
        
        if "Remove broken async database test" in commit:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Deploy: {status}", end="", flush=True)
            
            if status == "live":
                print("\n✅ DEPLOYMENT SUCCESSFUL!")
                print("\nWaiting 45 seconds for worker to start...")
                time.sleep(45)
                
                # Check jobs
                login = requests.post(f"{API_URL}/api/auth/login", data={"username": "demo", "password": "demo123"})
                if login.status_code == 200:
                    token = login.json()["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    print("\nChecking job status...")
                    for i in range(12):  # 2 minutes
                        jobs = requests.get(f"{API_URL}/api/scraping/jobs?limit=5", headers=headers).json()
                        
                        for job in jobs:
                            if job['status'] != 'pending':
                                print(f"\n\n🎉 SUCCESS! Job {job['id']} is {job['status']}!")
                                print("✅ WORKER IS FINALLY PROCESSING JOBS!")
                                
                                if job['status'] == 'completed':
                                    print(f"\nJob completed with stats:")
                                    print(f"{job.get('stats', {})}")
                                exit(0)
                        
                        statuses = [f"{j['id']}:{j['status']}" for j in jobs[:3]]
                        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {', '.join(statuses)}", end="", flush=True)
                        time.sleep(10)
                
                print("\n\n⚠️ Jobs still pending after 2 minutes")
                print("Check logs: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/logs")
                break
                
            elif status in ["build_failed", "update_failed"]:
                print(f"\n❌ Deploy failed: {status}")
                break
    
    time.sleep(10)