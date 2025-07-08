#!/usr/bin/env python3
"""
Monitor HoistScout deployment and test scraping
"""
import asyncio
import httpx
import time
from datetime import datetime

API_URL = "https://hoistscout-api.onrender.com"
RENDER_API_KEY = "rnd_QIzAkqWkpLRAu9w5ARGvwQtDTbx8"

async def check_deployment_status():
    """Check if services are deployed and healthy"""
    async with httpx.AsyncClient() as client:
        # Check API health
        try:
            response = await client.get(f"{API_URL}/api/health")
            if response.status_code == 200:
                print("✅ API is healthy")
                return True
        except:
            print("❌ API is not responding")
            return False

async def check_worker_processing():
    """Check if worker is processing jobs"""
    async with httpx.AsyncClient() as client:
        # Login
        login_response = await client.post(
            f"{API_URL}/api/auth/login",
            data={
                "username": "demo@hoistscout.com",
                "password": "demo123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check jobs
        jobs_response = await client.get(
            f"{API_URL}/api/scraping/jobs/",
            headers=headers
        )
        jobs = jobs_response.json()
        
        # Count statuses
        statuses = {}
        for job in jobs:
            status = job["status"]
            statuses[status] = statuses.get(status, 0) + 1
        
        print(f"\n📊 Job Status Summary:")
        for status, count in statuses.items():
            print(f"   {status}: {count} jobs")
        
        # Check if any jobs are running or completed
        if statuses.get("running", 0) > 0 or statuses.get("completed", 0) > 0:
            print("\n✅ Worker is processing jobs!")
            return True
        else:
            print("\n⚠️ Worker is not processing jobs yet")
            return False

async def monitor_deployment():
    """Monitor deployment progress"""
    print("🚀 Monitoring HoistScout deployment...")
    print(f"Started at: {datetime.now()}")
    
    # Wait for deployment to complete (usually 2-5 minutes)
    print("\n⏳ Waiting for deployment to complete...")
    await asyncio.sleep(60)  # Initial wait
    
    # Check deployment
    max_attempts = 10
    for attempt in range(max_attempts):
        print(f"\n--- Check {attempt + 1}/{max_attempts} ---")
        
        # Check API
        api_healthy = await check_deployment_status()
        
        if api_healthy:
            # Check worker
            worker_processing = await check_worker_processing()
            
            if worker_processing:
                print("\n🎉 Deployment successful! Worker is processing jobs!")
                break
        
        if attempt < max_attempts - 1:
            print(f"\n⏳ Waiting 30 seconds before next check...")
            await asyncio.sleep(30)
    
    print(f"\n🏁 Monitoring completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(monitor_deployment())