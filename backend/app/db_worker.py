#!/usr/bin/env python3
"""
Database Queue Worker - PostgreSQL-based task queue worker.
This replaces the Celery worker when Redis is not available.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db_queue import Worker, celery_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Database Queue Worker')
    parser.add_argument('--worker-id', help='Worker ID', default=None)
    parser.add_argument('--queues', help='Comma-separated list of queues', default='celery')
    parser.add_argument('--concurrency', type=int, help='Number of concurrent tasks', default=1)
    
    args = parser.parse_args()
    
    queues = [q.strip() for q in args.queues.split(',')]
    
    logger.info("Starting Database Queue Worker")
    logger.info(f"Worker ID: {args.worker_id or 'auto-generated'}")
    logger.info(f"Queues: {queues}")
    logger.info(f"Concurrency: {args.concurrency}")
    
    # Create and run worker
    worker = Worker(
        celery_app,
        worker_id=args.worker_id,
        queues=queues,
        concurrency=args.concurrency
    )
    
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()