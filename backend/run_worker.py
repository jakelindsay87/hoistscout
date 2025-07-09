#!/usr/bin/env python3
"""
Robust Celery worker startup script with validation
"""
import os
import sys
import time
import logging

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables"""
    required_vars = {
        'REDIS_URL': os.environ.get('REDIS_URL'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
        'USE_GEMINI': os.environ.get('USE_GEMINI', 'true')
    }
    
    logger.info("Environment validation:")
    for var, value in required_vars.items():
        if value:
            logger.info(f"  ✓ {var}: {'Set' if var == 'GEMINI_API_KEY' else value[:50] + '...'}")
        else:
            logger.error(f"  ✗ {var}: Not set!")
            if var != 'USE_GEMINI':
                return False
    return True

def test_redis_connection():
    """Test Redis connection before starting worker"""
    try:
        import redis
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        logger.info(f"Testing Redis connection to: {redis_url}")
        
        # Parse URL to check if it's internal or external
        if redis_url.startswith('redis://red-'):
            # Internal Render URL
            r = redis.from_url(redis_url, socket_connect_timeout=5)
        else:
            # External URL might need SSL
            r = redis.from_url(redis_url, socket_connect_timeout=5, ssl_cert_reqs=None)
        
        r.ping()
        logger.info("  ✓ Redis connection successful")
        
        # Check queue status
        queue_length = r.llen('celery')
        logger.info(f"  ✓ Celery queue has {queue_length} pending tasks")
        return True
    except Exception as e:
        logger.error(f"  ✗ Redis connection failed: {e}")
        return False

# Database test removed - worker handles its own async connections

def import_celery_app():
    """Import and validate Celery app"""
    try:
        logger.info("Importing Celery app...")
        
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.worker import celery_app
        logger.info("  ✓ Celery app imported successfully")
        
        # List registered tasks
        logger.info("Registered tasks:")
        task_count = 0
        for task_name in sorted(celery_app.tasks):
            if not task_name.startswith('celery.'):
                logger.info(f"    - {task_name}")
                task_count += 1
        
        if task_count == 0:
            logger.error("  ✗ No custom tasks registered!")
            return None
        
        logger.info(f"  ✓ Total custom tasks: {task_count}")
        return celery_app
    except Exception as e:
        logger.error(f"  ✗ Failed to import Celery app: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("HoistScout Worker Starting")
    logger.info("=" * 60)
    
    # Step 1: Validate environment
    if not validate_environment():
        logger.error("Environment validation failed!")
        sys.exit(1)
    
    # Step 2: Test Redis connection
    if not test_redis_connection():
        logger.error("Redis connection test failed!")
        sys.exit(1)
    
    # Step 3: Skip database test - worker handles its own connections
    logger.info("Skipping database test - worker manages connections internally")
    
    # Step 4: Import Celery app
    celery_app = import_celery_app()
    if not celery_app:
        logger.error("Failed to import Celery app!")
        sys.exit(1)
    
    # Step 5: Start worker
    logger.info("=" * 60)
    logger.info("Starting Celery worker...")
    logger.info("Configuration:")
    logger.info(f"  - Broker: {celery_app.conf.broker_url}")
    logger.info(f"  - Backend: {celery_app.conf.result_backend}")
    logger.info(f"  - Default queue: {celery_app.conf.task_default_queue}")
    logger.info("=" * 60)
    
    # Start worker with explicit settings
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=1',
        '--pool=solo',  # Use solo pool for simplicity
        '--queues=celery',  # Listen to default queue
        '-n', 'hoistscout-worker@%h',
        '-E',  # Enable events
        '--time-limit=1800',  # 30 min hard limit
        '--soft-time-limit=1500'  # 25 min soft limit
    ])

if __name__ == '__main__':
    main()