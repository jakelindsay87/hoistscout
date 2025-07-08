#!/usr/bin/env python3
"""Test Celery connection and task registration"""
import os
os.environ['DATABASE_URL'] = 'postgresql://demo:demo123@hoistscout-db.onrender.com/hoistscout'
os.environ['REDIS_URL'] = 'redis://red-d1eo8ertq21c73a72vbg:6379'
os.environ['USE_GEMINI'] = 'true'
os.environ['GEMINI_API_KEY'] = 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA'

from app.worker import celery_app, scrape_website_task

print("Testing Celery connection...")
print(f"Broker URL: {celery_app.conf.broker_url}")
print(f"Result backend: {celery_app.conf.result_backend}")

# List registered tasks
print("\nRegistered tasks:")
for task in celery_app.tasks:
    if not task.startswith('celery.'):
        print(f"  - {task}")

# Test connection
try:
    # Send a ping to see if any workers are active
    i = celery_app.control.inspect()
    stats = i.stats()
    
    if stats:
        print(f"\n✅ Found {len(stats)} active worker(s)!")
        for worker_name, worker_stats in stats.items():
            print(f"  Worker: {worker_name}")
            print(f"  Total tasks: {worker_stats.get('total', {})}")
    else:
        print("\n❌ No active workers found!")
        
    # Check active tasks
    active = i.active()
    if active:
        print("\nActive tasks:")
        for worker, tasks in active.items():
            print(f"  {worker}: {len(tasks)} tasks")
    
    # Check reserved tasks
    reserved = i.reserved()
    if reserved:
        print("\nReserved tasks:")
        for worker, tasks in reserved.items():
            print(f"  {worker}: {len(tasks)} tasks")
            
except Exception as e:
    print(f"\n❌ Error connecting to Celery: {e}")

print("\nTrying to send a test task...")
try:
    # Send a test task
    result = scrape_website_task.apply_async(args=[1], expires=60)
    print(f"✅ Task sent! ID: {result.id}")
    print(f"Task state: {result.state}")
except Exception as e:
    print(f"❌ Failed to send task: {e}")