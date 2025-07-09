#!/usr/bin/env python3
"""
Minimal worker script for debugging Celery startup issues.
This script bypasses all validation and focuses on raw Celery initialization.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging with maximum verbosity
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))
logger.info(f"Python path: {sys.path}")

# Print environment info
logger.info("=" * 80)
logger.info("ENVIRONMENT INFORMATION")
logger.info("=" * 80)
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Backend directory: {backend_dir}")

# Print relevant environment variables
env_vars = ['DATABASE_URL', 'REDIS_URL', 'CELERY_BROKER_URL', 'CELERY_RESULT_BACKEND']
for var in env_vars:
    value = os.environ.get(var, 'NOT SET')
    if 'redis' in var.lower() and value != 'NOT SET':
        # Mask password in Redis URLs
        import re
        value = re.sub(r':([^:@]+)@', ':****@', value)
    logger.info(f"{var}: {value}")

logger.info("=" * 80)

try:
    # Try to import Celery
    logger.info("Attempting to import Celery...")
    from celery import Celery
    logger.info(f"✓ Celery imported successfully. Version: {Celery.__version__ if hasattr(Celery, '__version__') else 'unknown'}")
except ImportError as e:
    logger.error(f"✗ Failed to import Celery: {e}")
    sys.exit(1)

try:
    # Try to get Redis URL from environment or use default
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    logger.info(f"Using Redis URL: {redis_url}")
    
    # Create minimal Celery app
    logger.info("Creating minimal Celery app...")
    app = Celery(
        'minimal_debug',
        broker=redis_url,
        backend=redis_url
    )
    logger.info("✓ Celery app created successfully")
    
    # Print Celery configuration
    logger.info("=" * 80)
    logger.info("CELERY CONFIGURATION")
    logger.info("=" * 80)
    logger.info(f"App name: {app.main}")
    logger.info(f"Broker URL: {app.conf.broker_url}")
    logger.info(f"Result backend: {app.conf.result_backend}")
    
    # Try to connect to broker
    logger.info("=" * 80)
    logger.info("TESTING BROKER CONNECTION")
    logger.info("=" * 80)
    
    try:
        # Test connection
        logger.info("Attempting to connect to broker...")
        conn = app.connection()
        conn.ensure_connection(max_retries=3)
        logger.info("✓ Successfully connected to broker")
        conn.release()
    except Exception as e:
        logger.error(f"✗ Failed to connect to broker: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # Define a simple test task
    @app.task
    def test_task():
        return "Hello from minimal debug worker!"
    
    logger.info("✓ Test task defined")
    
    # Try to import the actual worker module
    logger.info("=" * 80)
    logger.info("TESTING ACTUAL WORKER IMPORT")
    logger.info("=" * 80)
    
    try:
        logger.info("Attempting to import app.worker...")
        from app import worker
        logger.info("✓ Successfully imported app.worker")
        logger.info(f"Worker celery app: {worker.celery_app}")
        logger.info(f"Worker tasks: {list(worker.celery_app.tasks.keys())}")
    except Exception as e:
        logger.error(f"✗ Failed to import app.worker: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # Try to start worker with debug settings
    logger.info("=" * 80)
    logger.info("STARTING MINIMAL WORKER")
    logger.info("=" * 80)
    
    logger.info("Starting worker with following settings:")
    logger.info("  - Loglevel: DEBUG")
    logger.info("  - Concurrency: 1")
    logger.info("  - Pool: solo (single-threaded)")
    logger.info("  - Events: Enabled")
    
    # Start the worker
    app.worker_main([
        'worker',
        '--loglevel=DEBUG',
        '--concurrency=1',
        '--pool=solo',
        '--events',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ])
    
except Exception as e:
    logger.error(f"Fatal error: {e}")
    import traceback
    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    sys.exit(1)