#!/usr/bin/env python3
"""Enhanced worker with comprehensive debugging and task discovery"""
import os
import sys
import logging
import signal
import time

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

logger.info("=" * 80)
logger.info("ENHANCED HOISTSCOUT WORKER STARTING")
logger.info("=" * 80)

# Environment check
logger.info("Environment variables:")
logger.info(f"  REDIS_URL: {os.environ.get('REDIS_URL', 'Not set')}")
logger.info(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
logger.info(f"  GEMINI_API_KEY: {'Set' if os.environ.get('GEMINI_API_KEY') else 'Not set'}")

try:
    # Import Celery app
    logger.info("\nImporting Celery app...")
    from app.worker import celery_app
    logger.info("✓ Celery app imported successfully")
    
    # Force task discovery
    logger.info("\nForcing task discovery...")
    celery_app.autodiscover_tasks(['app'], force=True)
    
    # List all tasks
    logger.info("\nRegistered tasks:")
    tasks = celery_app.tasks
    app_tasks = [name for name in tasks.keys() if not name.startswith('celery.')]
    for task_name in sorted(app_tasks):
        logger.info(f"  - {task_name}")
    
    if not app_tasks:
        logger.error("❌ No application tasks registered!")
        logger.error("Worker will not be able to process any jobs")
        sys.exit(1)
    
    # Test Redis connection
    logger.info("\nTesting Redis connection...")
    try:
        # Use Celery's connection
        with celery_app.connection_or_acquire() as conn:
            conn.ensure_connection(max_retries=3)
            logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        sys.exit(1)
    
    # Configure worker
    logger.info("\nConfiguring worker...")
    celery_app.conf.update(
        worker_prefetch_multiplier=1,
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        worker_hijack_root_logger=False,
        worker_redirect_stdouts_level='INFO',
    )
    
    # Start worker
    logger.info("\nStarting Celery worker...")
    logger.info("Queue: celery")
    logger.info("Pool: solo (single process)")
    logger.info("Press Ctrl+C to stop")
    logger.info("-" * 80)
    
    # Start with explicit configuration
    celery_app.worker_main([
        'worker',
        '--loglevel=INFO',
        '--pool=solo',
        '--queues=celery',
        '--concurrency=1',
        '--without-heartbeat',  # Disable heartbeat for debugging
        '--without-gossip',     # Disable gossip for debugging
        '--without-mingle',     # Disable mingle for debugging
    ])
    
except KeyboardInterrupt:
    logger.info("\nShutdown requested by user")
except Exception as e:
    logger.error(f"\n❌ Worker failed to start: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)