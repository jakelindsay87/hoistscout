#!/usr/bin/env python3
"""Debug Redis connection and Celery queues"""
import os
import redis
import json
from celery import Celery

# External Redis URL for debugging
EXTERNAL_REDIS_URL = "rediss://red-d1hljoruibrs73fe7vkg:GVMeswpIbCXw0hrpegTULbgosBs53wSL@oregon-keyvalue.render.com:6379"

print("Debugging Redis Connection and Celery Queues...")
print("=" * 60)

# Test Redis connection
print("\n1. Testing Redis Connection...")
try:
    # Connect with SSL
    r = redis.from_url(EXTERNAL_REDIS_URL, ssl_cert_reqs=None)
    r.ping()
    print("✅ Redis connection successful!")
    
    # Get Redis info
    info = r.info()
    print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
    print(f"   Connected clients: {info.get('connected_clients', 0)}")
    
    # Check for Celery-related keys
    print("\n2. Checking Celery Keys...")
    celery_keys = r.keys('celery*')
    print(f"   Found {len(celery_keys)} Celery-related keys")
    
    # Check specific queues
    print("\n3. Checking Queue Contents...")
    queue_key = "celery"  # Default queue name
    queue_length = r.llen(queue_key)
    print(f"   Queue '{queue_key}': {queue_length} tasks")
    
    if queue_length > 0:
        # Show first few tasks
        print("   First 3 tasks in queue:")
        for i in range(min(3, queue_length)):
            task_data = r.lindex(queue_key, i)
            if task_data:
                try:
                    task = json.loads(task_data)
                    print(f"     - Task ID: {task.get('headers', {}).get('id', 'Unknown')}")
                    print(f"       Task: {task.get('headers', {}).get('task', 'Unknown')}")
                except:
                    print(f"     - Raw: {task_data[:100]}...")
    
    # Check for unacked tasks
    unacked_key = "unacked"
    unacked_tasks = r.hlen(unacked_key)
    print(f"\n   Unacknowledged tasks: {unacked_tasks}")
    
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    import traceback
    traceback.print_exc()

# Test Celery setup
print("\n4. Testing Celery Configuration...")
try:
    # Set environment for Celery
    os.environ['REDIS_URL'] = EXTERNAL_REDIS_URL
    os.environ['DATABASE_URL'] = 'postgresql://demo:demo123@hoistscout-db.onrender.com/hoistscout'
    os.environ['USE_GEMINI'] = 'true'
    os.environ['GEMINI_API_KEY'] = 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA'
    
    # Create test Celery app
    test_app = Celery('test', broker=EXTERNAL_REDIS_URL, backend=EXTERNAL_REDIS_URL)
    test_app.conf.update(
        broker_use_ssl={
            'ssl_cert_reqs': None
        }
    )
    
    # Inspect workers
    i = test_app.control.inspect()
    active_workers = i.active()
    
    if active_workers:
        print("✅ Found active workers:")
        for worker, tasks in active_workers.items():
            print(f"   Worker: {worker}")
            print(f"   Active tasks: {len(tasks)}")
    else:
        print("❌ No active workers found")
        
    # Check registered tasks
    registered = i.registered()
    if registered:
        print("\n   Registered tasks on workers:")
        for worker, tasks in registered.items():
            print(f"   Worker {worker}: {len(tasks)} tasks")
            for task in tasks[:5]:  # Show first 5
                if not task.startswith('celery.'):
                    print(f"     - {task}")
    
except Exception as e:
    print(f"❌ Celery inspection failed: {e}")

print("\n" + "=" * 60)
print("Dashboard: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g")