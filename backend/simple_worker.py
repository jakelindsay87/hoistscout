#!/usr/bin/env python3
"""Simplest possible worker - no validation, just start Celery"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting simple worker...")
print(f"REDIS_URL: {os.environ.get('REDIS_URL')}")

# Import and start worker directly
try:
    from app.worker import celery_app
    print("Celery app imported successfully")
    print(f"Broker: {celery_app.conf.broker_url}")
    
    # Start worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=solo',
        '--queues=celery'
    ])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()