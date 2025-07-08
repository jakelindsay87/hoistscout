#!/usr/bin/env python3
"""Worker startup script with comprehensive debugging"""
import os
import sys
import time
import asyncio
from datetime import datetime

# Set environment variables if not already set
if 'REDIS_URL' not in os.environ:
    os.environ['REDIS_URL'] = 'redis://redis:6379/0'

print("="*60)
print(f"HoistScout Worker Starting at {datetime.utcnow()}")
print("="*60)

# Display environment
print("\n🔧 Environment Variables:")
print(f"  REDIS_URL: {os.environ.get('REDIS_URL')}")
print(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
print(f"  USE_GEMINI: {os.environ.get('USE_GEMINI', 'Not set')}")
print(f"  GEMINI_API_KEY: {'✓ Set' if os.environ.get('GEMINI_API_KEY') else '✗ Not set'}")
print(f"  GEMINI_MODEL: {os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')}")

# Test Redis connection
print("\n🔌 Testing Redis Connection...")
try:
    import redis
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url)
    r.ping()
    print("  ✅ Redis connection successful!")
    
    # Check for existing keys
    keys = r.keys('celery*')
    print(f"  📊 Found {len(keys)} Celery-related keys in Redis")
except Exception as e:
    print(f"  ❌ Redis connection failed: {e}")

# Test Database connection
print("\n🗄️ Testing Database Connection...")
try:
    from app.database import engine
    from sqlalchemy import text
    
    async def test_db():
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar()
    
    result = asyncio.run(test_db())
    print("  ✅ Database connection successful!")
except Exception as e:
    print(f"  ❌ Database connection failed: {e}")

# Import and configure Celery
print("\n🎯 Importing Celery App...")
try:
    from app.worker import celery_app, scrape_website_task
    print("  ✅ Successfully imported Celery app")
    
    # Display configuration
    print("\n📋 Celery Configuration:")
    print(f"  Broker: {celery_app.conf.broker_url}")
    print(f"  Backend: {celery_app.conf.result_backend}")
    print(f"  Task serializer: {celery_app.conf.task_serializer}")
    print(f"  Result serializer: {celery_app.conf.result_serializer}")
    
    # List registered tasks
    print("\n📝 Registered Tasks:")
    task_count = 0
    for task_name in sorted(celery_app.tasks):
        if not task_name.startswith('celery.'):
            print(f"    - {task_name}")
            task_count += 1
    print(f"  Total custom tasks: {task_count}")
    
    # Check for pending tasks
    print("\n📬 Checking for pending tasks...")
    try:
        i = celery_app.control.inspect()
        # This will be None if no workers are running
        reserved = i.reserved() if i else None
        active = i.active() if i else None
        
        if reserved or active:
            print("  Found existing tasks in queue")
        else:
            print("  No active workers or tasks found (this is normal on startup)")
    except Exception as e:
        print(f"  Could not inspect tasks: {e}")
    
    # Start worker with detailed logging
    print("\n🚀 Starting Celery Worker...")
    print("  Configuration:")
    print("    - Concurrency: 1")
    print("    - Log level: INFO")
    print("    - Task events: Enabled")
    print("\n" + "="*60)
    print("WORKER LOGS:")
    print("="*60 + "\n")
    
    # Start the worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=1',
        '-E',  # Enable task events
        '--without-gossip',  # Disable gossip for cleaner logs
        '--without-mingle',  # Disable synchronization on startup
        '--without-heartbeat',  # Disable heartbeat for cleaner logs
        '-n', 'hoistscout-worker@%h'
    ])
    
except Exception as e:
    print(f"\n❌ Fatal Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Keep container running for debugging
    print("\n⚠️ Keeping container alive for debugging...")
    while True:
        time.sleep(60)
        print(f"Still alive at {datetime.utcnow()}")