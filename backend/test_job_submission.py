#!/usr/bin/env python3
"""Test job submission directly to Redis"""
import os
import asyncio
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://demo:demo123@hoistscout-db.onrender.com/hoistscout'
os.environ['REDIS_URL'] = 'redis://red-d1eo8ertq21c73a72vbg:6379'
os.environ['USE_GEMINI'] = 'true'
os.environ['GEMINI_API_KEY'] = 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA'

async def test_job_submission():
    print("Testing job submission...")
    
    # Import after env vars are set
    from app.worker import scrape_website_task
    from app.database import get_db, engine
    from app.models.website import Website
    from sqlalchemy import select
    
    # Get a website to test with
    async with engine.begin() as conn:
        async_session = get_db()
        async with async_session() as session:
            result = await session.execute(select(Website).limit(1))
            website = result.scalar_one_or_none()
            
            if not website:
                print("❌ No websites found in database!")
                return
            
            print(f"✅ Found website: {website.name} (ID: {website.id})")
    
    # Submit job
    print(f"\n📤 Submitting scraping job for website ID {website.id}...")
    try:
        result = scrape_website_task.apply_async(
            args=[website.id],
            expires=300,  # 5 minute expiry
            retry=False
        )
        print(f"✅ Job submitted! Task ID: {result.id}")
        print(f"   Initial state: {result.state}")
        
        # Check status
        print("\n⏳ Waiting 5 seconds...")
        await asyncio.sleep(5)
        
        print(f"   Current state: {result.state}")
        if result.ready():
            print(f"   Result: {result.result}")
        else:
            print("   Job still pending/running")
            
        # Check backend
        backend_result = result.backend.get(result.backend.get_key_for_task(result.id))
        print(f"   Backend data: {backend_result}")
        
    except Exception as e:
        print(f"❌ Error submitting job: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_job_submission())