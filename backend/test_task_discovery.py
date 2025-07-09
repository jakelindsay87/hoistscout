#!/usr/bin/env python3
"""Test Celery task discovery and registration"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("CELERY TASK DISCOVERY TEST")
print("=" * 80)

# Set environment variables if not set
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')

try:
    # Import worker module
    print("\n1. Importing worker module...")
    from app.worker import celery_app
    print("✓ Worker module imported successfully")
    
    # List all registered tasks
    print("\n2. Registered tasks:")
    tasks = celery_app.tasks
    if tasks:
        for task_name in sorted(tasks.keys()):
            if not task_name.startswith('celery.'):  # Skip built-in tasks
                print(f"  - {task_name}")
    else:
        print("  ❌ No tasks registered!")
    
    # Check specific expected tasks
    print("\n3. Checking expected tasks:")
    expected_tasks = [
        'app.worker.scrape_website_task',
        'app.worker.process_scraped_data',
        'app.worker.scrape_all_active_websites'
    ]
    
    for task_name in expected_tasks:
        if task_name in tasks:
            print(f"  ✓ {task_name} - Found")
        else:
            print(f"  ❌ {task_name} - NOT FOUND")
    
    # Test task instance
    print("\n4. Testing task instance:")
    if 'app.worker.scrape_website_task' in tasks:
        task = tasks['app.worker.scrape_website_task']
        print(f"  Task name: {task.name}")
        print(f"  Task module: {task.__module__}")
        print(f"  Max retries: {getattr(task, 'max_retries', 'Not set')}")
        print("  ✓ Task instance is valid")
    else:
        print("  ❌ Cannot test - scrape_website_task not found")
    
    # Check Celery configuration
    print("\n5. Celery configuration:")
    print(f"  Broker: {celery_app.conf.broker_url}")
    print(f"  Result backend: {celery_app.conf.result_backend}")
    print(f"  Task serializer: {celery_app.conf.task_serializer}")
    print(f"  Result serializer: {celery_app.conf.result_serializer}")
    print(f"  Task default queue: {celery_app.conf.task_default_queue}")
    
    # Test Redis connection
    print("\n6. Testing Redis connection:")
    try:
        from celery import current_app
        conn = current_app.connection_or_acquire()
        conn.default_channel.queue_declare(queue='celery', passive=True)
        print("  ✓ Redis connection successful")
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    if 'app.worker.scrape_website_task' in tasks:
        print("✓ Task discovery is working correctly!")
    else:
        print("❌ Task discovery is NOT working - tasks are not being registered")
        print("\nPossible fixes:")
        print("1. Ensure tasks are defined with @celery_app.task decorator")
        print("2. Check for import errors in the worker module")
        print("3. Verify autodiscover_tasks is configured correctly")
    
except Exception as e:
    print(f"\n❌ Error during test: {e}")
    import traceback
    traceback.print_exc()