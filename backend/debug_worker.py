#!/usr/bin/env python3
"""Debug worker connectivity and configuration"""
import os
import sys
from celery import Celery
from app.config import get_settings

# Get settings
settings = get_settings()
print(f"Redis URL: {settings.redis_url}")
print(f"Database URL: {settings.database_url[:50]}...")
print(f"GEMINI_API_KEY: {'Set' if settings.gemini_api_key else 'NOT SET!'}")
print(f"USE_GEMINI: {settings.use_gemini}")

# Test Redis connection
import redis
try:
    r = redis.from_url(settings.redis_url)
    r.ping()
    print("\n✅ Redis connection: OK")
except Exception as e:
    print(f"\n❌ Redis connection failed: {e}")
    sys.exit(1)

# Check Celery
try:
    from app.worker import celery_app
    print(f"\n✅ Celery app loaded: {celery_app.main}")
    
    # List registered tasks
    print("\nRegistered tasks:")
    for task in celery_app.tasks:
        if not task.startswith('celery.'):
            print(f"  - {task}")
    
    # Check if worker is running
    i = celery_app.control.inspect()
    stats = i.stats()
    if stats:
        print(f"\n✅ Worker is running! Stats: {list(stats.keys())}")
    else:
        print("\n❌ No workers detected running")
        
except Exception as e:
    print(f"\n❌ Celery error: {e}")

print("\nDiagnosis complete!")