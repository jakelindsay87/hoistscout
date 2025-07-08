#!/usr/bin/env python3
"""
Live monitoring script for HoistScout worker
Continuously checks if worker starts processing jobs
"""
import time
import httpx
from datetime import datetime
import sys

API_URL = "https://hoistscout-api.onrender.com"

def check_worker_status():
    """Check if worker is processing jobs"""
    try:
        # Login
        login_response = httpx.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": "demo@hoistscout.com",
                "password": "demo123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get jobs
        jobs_response = httpx.get(
            f"{API_URL}/api/scraping/jobs/",
            headers=headers
        )
        jobs = jobs_response.json()
        
        # Count statuses
        statuses = {}
        for job in jobs:
            status = job["status"]
            statuses[status] = statuses.get(status, 0) + 1
        
        # Check for processing
        is_processing = statuses.get("running", 0) > 0 or statuses.get("completed", 0) > 0
        
        return statuses, is_processing
        
    except Exception as e:
        print(f"Error checking status: {e}")
        return None, False

def main():
    print("🔍 Monitoring HoistScout Worker Status")
    print("=" * 50)
    print("Waiting for GEMINI_API_KEY to be set in Render...")
    print("Press Ctrl+C to stop monitoring\n")
    
    check_count = 0
    last_status = None
    
    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            statuses, is_processing = check_worker_status()
            
            if statuses:
                # Only print if status changed
                if statuses != last_status:
                    print(f"\n[{timestamp}] Check #{check_count}")
                    print("Job Status:")
                    for status, count in statuses.items():
                        emoji = "⏳" if status == "pending" else "🔄" if status == "running" else "✅" if status == "completed" else "❌"
                        print(f"  {emoji} {status}: {count} jobs")
                    
                    if is_processing:
                        print("\n🎉 WORKER IS PROCESSING JOBS!")
                        print("The GEMINI_API_KEY has been set successfully.")
                        print("\nNext steps:")
                        print("1. Run: python3 test_tenders_scraping.py")
                        print("2. Check opportunities at: https://hoistscout-frontend.onrender.com/opportunities")
                        break
                    else:
                        print("\n⏳ Worker not processing yet. Still waiting for API key...")
                    
                    last_status = statuses
                else:
                    # Just show we're still checking
                    sys.stdout.write(f"\r[{timestamp}] Still checking... (#{check_count})")
                    sys.stdout.flush()
            
            # Wait 10 seconds between checks
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    main()