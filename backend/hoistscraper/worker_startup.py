#!/usr/bin/env python
"""Worker startup script with improved connection handling and health checks."""
import os
import sys
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_connection() -> bool:
    """Check if database is accessible."""
    try:
        from sqlmodel import Session, select
        from hoistscraper.db import engine
        from hoistscraper.models import Website
        
        with Session(engine) as session:
            # Try a simple query
            session.exec(select(Website).limit(1)).first()
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        from hoistscraper.queue import redis_conn
        
        # Test basic operations
        redis_conn.ping()
        redis_conn.set("worker:startup:check", "ok", ex=10)
        value = redis_conn.get("worker:startup:check")
        
        if value == "ok":
            logger.info("Redis connection successful")
            return True
        else:
            logger.error("Redis read/write test failed")
            return False
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False


def check_playwright_installation() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Try to launch browser
            browser = p.chromium.launch(headless=True)
            browser.close()
            logger.info("Playwright browsers installed successfully")
            return True
    except Exception as e:
        logger.error(f"Playwright check failed: {e}")
        logger.info("Attempting to install Playwright browsers...")
        
        try:
            import subprocess
            subprocess.run(["playwright", "install", "chromium", "--with-deps"], check=True)
            logger.info("Playwright browsers installed")
            return True
        except Exception as install_error:
            logger.error(f"Failed to install Playwright browsers: {install_error}")
            return False


def wait_for_dependencies(max_wait: int = 300) -> bool:
    """Wait for all dependencies to be ready.
    
    Args:
        max_wait: Maximum time to wait in seconds (default: 5 minutes)
        
    Returns:
        True if all dependencies are ready, False otherwise
    """
    start_time = time.time()
    checks = {
        "Database": check_database_connection,
        "Redis": check_redis_connection,
        "Playwright": check_playwright_installation
    }
    
    while time.time() - start_time < max_wait:
        all_ready = True
        
        for service, check_func in checks.items():
            if not check_func():
                all_ready = False
                logger.warning(f"{service} not ready yet...")
        
        if all_ready:
            logger.info("All dependencies are ready!")
            return True
        
        # Wait before retrying
        wait_time = min(10, max_wait - (time.time() - start_time))
        if wait_time > 0:
            logger.info(f"Waiting {wait_time:.0f} seconds before retrying...")
            time.sleep(wait_time)
    
    logger.error(f"Dependencies not ready after {max_wait} seconds")
    return False


def start_worker(worker_type: str = "v1") -> None:
    """Start the RQ worker.
    
    Args:
        worker_type: Which worker to start ("v1" or "v2")
    """
    from rq import Worker, Queue, Connection
    from hoistscraper.queue import redis_conn
    
    logger.info(f"Starting RQ worker (type: {worker_type})")
    
    # Configure worker settings
    worker_config = {
        'name': f'hoistscraper-worker-{os.getpid()}',
        'log_level': 'INFO',
        'connection': redis_conn,
        'exception_handlers': [],
        'disable_default_exception_handler': False,
        'job_monitoring_interval': 5,
        'max_jobs': 100,  # Process 100 jobs before restarting
        'max_idle_time': 300,  # Restart after 5 minutes idle
    }
    
    try:
        with Connection(redis_conn):
            # Create queues
            queues = [Queue('scraper'), Queue('default')]
            
            # Create and configure worker
            worker = Worker(queues, **worker_config)
            
            # Log worker info
            logger.info(f"Worker {worker.name} starting...")
            logger.info(f"Listening on queues: {[q.name for q in queues]}")
            
            # Start working
            worker.work(with_scheduler=True)
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
        sys.exit(1)


def main():
    """Main entry point for worker startup."""
    logger.info("HoistScraper Worker Starting...")
    
    # Check environment
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
        "REDIS_URL": os.getenv("REDIS_URL", "Not set"),
        "DATA_DIR": os.getenv("DATA_DIR", "/data"),
    }
    
    logger.info("Environment configuration:")
    for key, value in env_vars.items():
        logger.info(f"  {key}: {value}")
    
    # Create data directory if needed
    data_dir = env_vars["DATA_DIR"]
    if data_dir != "Not set":
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Data directory ensured at: {data_dir}")
    
    # Wait for dependencies
    if not wait_for_dependencies():
        logger.error("Failed to connect to required services")
        sys.exit(1)
    
    # Determine which worker to use
    worker_type = os.getenv("WORKER_TYPE", "v2")
    
    if worker_type == "v2":
        # Import v2 worker to ensure it's loaded
        try:
            from hoistscraper.worker_v2 import scrape_website_job_v2
            logger.info("Using enhanced worker v2 with Ollama integration")
        except ImportError as e:
            logger.warning(f"Could not import worker_v2: {e}")
            logger.info("Falling back to v1 worker")
            worker_type = "v1"
    
    # Start the worker
    start_worker(worker_type)


if __name__ == '__main__':
    main()