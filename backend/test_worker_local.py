#!/usr/bin/env python3
"""Test worker functionality locally"""
import os
import sys

# Set minimal environment variables
os.environ['DATABASE_URL'] = 'postgresql://demo:demo123@hoistscout-db.onrender.com/hoistscout'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'  # Local Redis for testing
os.environ['USE_GEMINI'] = 'true'
os.environ['GEMINI_API_KEY'] = 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA'

print("Testing worker import and configuration...")

try:
    # Import worker
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app.worker import celery_app, scrape_website_task
    
    print("✅ Successfully imported worker")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Backend URL: {celery_app.conf.result_backend}")
    
    # List tasks
    print("\nRegistered tasks:")
    for task in sorted(celery_app.tasks):
        if not task.startswith('celery.'):
            print(f"  - {task}")
    
    # Check task registration
    print(f"\nscrape_website_task registered: {scrape_website_task.name in celery_app.tasks}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()