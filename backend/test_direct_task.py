#!/usr/bin/env python3
"""Test running a Celery task directly"""
import os
import sys
import time

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('DATABASE_URL', 'postgresql://user:pass@localhost/hoistscout')
os.environ.setdefault('GEMINI_API_KEY', 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA')

print("=" * 80)
print("DIRECT CELERY TASK TEST")
print("=" * 80)

try:
    # Import and configure
    from app.worker import celery_app, scrape_website_task
    from app.core.config import get_settings
    
    settings = get_settings()
    print(f"\n1. Configuration:")
    print(f"   Redis URL: {settings.redis_url}")
    print(f"   Gemini API Key: {'Set' if settings.gemini_api_key else 'Not set'}")
    
    # Send a test task
    print("\n2. Sending test task...")
    result = scrape_website_task.delay(1)  # Test with website ID 1
    print(f"   Task ID: {result.id}")
    print(f"   Task state: {result.state}")
    
    # Wait for result
    print("\n3. Waiting for task result (max 10 seconds)...")
    for i in range(10):
        if result.ready():
            print(f"   Task completed!")
            if result.successful():
                print(f"   Result: {result.result}")
            else:
                print(f"   Error: {result.info}")
            break
        else:
            print(f"   Still waiting... ({i+1}/10) State: {result.state}")
            time.sleep(1)
    else:
        print("   Task did not complete within 10 seconds")
        print(f"   Final state: {result.state}")
    
    # Check if task is in queue
    print("\n4. Checking Redis queue...")
    import redis
    r = redis.from_url(settings.redis_url)
    queue_length = r.llen('celery')
    print(f"   Tasks in 'celery' queue: {queue_length}")
    
    if queue_length > 0:
        print("   ⚠️  Tasks are queued but not being processed!")
        print("   This means the worker is not running or not consuming from the queue")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()