#!/usr/bin/env python3
"""
Ultra-minimal Celery worker for debugging.
This version doesn't import anything from the app.
"""

import os
import sys
import logging

# Maximum verbosity
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("=" * 80)
print("ULTRA MINIMAL CELERY WORKER DEBUG")
print("=" * 80)

# Step 1: Check if we can import Celery
try:
    import celery
    print(f"✓ Celery module imported: {celery.__file__}")
    print(f"✓ Celery version: {celery.__version__}")
except ImportError as e:
    print(f"✗ Cannot import Celery: {e}")
    sys.exit(1)

# Step 2: Create the simplest possible Celery app
try:
    from celery import Celery
    
    # Get Redis URL or use default
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    print(f"\nUsing Redis URL: {redis_url}")
    
    # Create app
    app = Celery('test', broker=redis_url, backend=redis_url)
    print("✓ Celery app created")
    
    # Define a test task
    @app.task
    def hello():
        return 'Hello World!'
    
    print("✓ Test task defined")
    
    # Configure for debugging
    app.conf.update(
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        worker_redirect_stdouts_level='DEBUG',
    )
    
    print("\nStarting worker with minimal configuration...")
    print("Press Ctrl+C to stop\n")
    
    # Start worker
    app.worker_main([
        'worker',
        '--loglevel=DEBUG',
        '--pool=solo',  # Single thread
        '--concurrency=1',
    ])
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)