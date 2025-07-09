#!/usr/bin/env python3
"""Test worker startup locally with minimal setup"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://demo:demo123@hoistscout-db.onrender.com/hoistscout'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'  # Local Redis
os.environ['USE_GEMINI'] = 'true'
os.environ['GEMINI_API_KEY'] = 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA'

print("Testing Worker Startup...")
print("=" * 60)

try:
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import Celery app
    from app.worker import celery_app
    
    print("✅ Celery app imported successfully")
    print(f"Broker: {celery_app.conf.broker_url}")
    print(f"Backend: {celery_app.conf.result_backend}")
    
    # Show task configuration
    print("\nTask Configuration:")
    print(f"  Default queue: {celery_app.conf.task_default_queue}")
    print(f"  Create missing queues: {celery_app.conf.task_create_missing_queues}")
    print(f"  Serializer: {celery_app.conf.task_serializer}")
    
    # List tasks
    print("\nRegistered Tasks:")
    for task_name in sorted(celery_app.tasks):
        if not task_name.startswith('celery.'):
            task = celery_app.tasks[task_name]
            print(f"  - {task_name}")
            print(f"    Queue: {getattr(task, 'queue', 'default')}")
            print(f"    Name: {task.name}")
    
    print("\n✅ Worker configuration looks good!")
    print("\nTo start the worker, run:")
    print("  celery -A app.worker worker --loglevel=info")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()