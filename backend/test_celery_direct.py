#!/usr/bin/env python3
"""Direct test of Celery functionality"""
import os
import sys
import time

# Set test environment
os.environ['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/hoistscout')
os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', 'AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("DIRECT CELERY TEST")
print("=" * 80)

# Import Celery app and task
from app.worker import celery_app, scrape_website_task

print(f"\nRedis URL: {celery_app.conf.broker_url}")
print(f"Registered tasks: {list(celery_app.tasks.keys())}")

# Send a test task
print("\nSending test task...")
result = scrape_website_task.delay(1)
print(f"Task ID: {result.id}")
print(f"Initial state: {result.state}")

# Wait briefly
time.sleep(2)
print(f"State after 2s: {result.state}")

# Check Redis directly
import redis
r = redis.from_url(os.environ.get('REDIS_URL'))
print(f"\nRedis queue length: {r.llen('celery')}")