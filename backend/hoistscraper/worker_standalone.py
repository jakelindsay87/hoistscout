#!/usr/bin/env python
"""Standalone worker that processes jobs from the database without Redis."""
import os
import sys
import time
import logging
from datetime import datetime, UTC
from sqlmodel import Session, select

from hoistscraper.db import engine, create_db_and_tables
from hoistscraper.models import ScrapeJob, JobStatus
from hoistscraper.worker_v2 import EnhancedScraperWorker
from hoistscraper.worker import ScraperWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_pending_jobs():
    """Process all pending jobs from the database."""
    # Ensure database is initialized
    create_db_and_tables()
    
    # Determine which worker to use
    worker_type = os.getenv("WORKER_TYPE", "v2")
    use_v2 = worker_type == "v2"
    
    if use_v2:
        try:
            import asyncio
            worker = EnhancedScraperWorker()
            logger.info("Using enhanced worker v2 with Ollama integration")
        except ImportError:
            logger.warning("Could not import worker_v2, falling back to v1")
            use_v2 = False
            worker = ScraperWorker()
    else:
        worker = ScraperWorker()
        logger.info("Using standard worker v1")
    
    try:
        while True:
            # Get pending jobs from database
            with Session(engine) as session:
                pending_jobs = session.exec(
                    select(ScrapeJob)
                    .where(ScrapeJob.status == JobStatus.PENDING)
                    .order_by(ScrapeJob.created_at)
                    .limit(1)  # Process one at a time
                ).all()
                
                if not pending_jobs:
                    logger.debug("No pending jobs, waiting...")
                    time.sleep(10)
                    continue
                
                for job in pending_jobs:
                    logger.info(f"Processing job {job.id} for website {job.website_id}")
                    
                    # Update job status to running
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.now(UTC)
                    session.commit()
                    
                    try:
                        # Execute the job
                        if use_v2 and isinstance(worker, EnhancedScraperWorker):
                            # Run async function
                            result = asyncio.run(
                                worker.scrape_website(job.website_id, job.id)
                            )
                        else:
                            # Run sync function
                            result = worker.scrape_website(job.website_id, job.id)
                        
                        logger.info(f"Job {job.id} completed successfully")
                        
                        # Job status is updated within the worker
                        
                    except Exception as e:
                        logger.error(f"Job {job.id} failed: {e}")
                        
                        # Update job status to failed
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.now(UTC)
                        job.error_message = str(e)
                        session.commit()
                    
                    # Small delay between jobs
                    time.sleep(2)
    
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        # Cleanup
        if use_v2 and isinstance(worker, EnhancedScraperWorker):
            import asyncio
            asyncio.run(worker.cleanup())
        else:
            worker.cleanup()


def main():
    """Main entry point."""
    logger.info("Starting standalone worker...")
    
    # Log configuration
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
        "DATA_DIR": os.getenv("DATA_DIR", "/data"),
        "WORKER_TYPE": os.getenv("WORKER_TYPE", "v2"),
        "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "Not set"),
    }
    
    logger.info("Environment configuration:")
    for key, value in env_vars.items():
        if "URL" in key and value != "Not set":
            # Mask sensitive data
            from urllib.parse import urlparse
            parsed = urlparse(value)
            if parsed.password:
                value = value.replace(parsed.password, "***")
        logger.info(f"  {key}: {value}")
    
    # Create data directory if needed
    data_dir = os.getenv("DATA_DIR", "/data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Start processing jobs
    process_pending_jobs()


if __name__ == '__main__':
    main()