"""Simple database-based job queue to replace Redis/RQ."""
import os
import logging
import threading
import time
from datetime import datetime, UTC
from typing import Optional, Callable, Dict, Any
from sqlmodel import Session, select
from concurrent.futures import ThreadPoolExecutor, Future

from .db import engine
from .models import ScrapeJob, JobStatus

logger = logging.getLogger(__name__)


class SimpleJobQueue:
    """Simple job queue using database and thread pool."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.worker_thread = None
        self.job_futures: Dict[int, Future] = {}
    
    def start(self):
        """Start the job queue worker."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Simple job queue started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the job queue worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Simple job queue stopped")
    
    def enqueue(self, func: Callable, *args, **kwargs) -> Optional[int]:
        """Enqueue a job for processing.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Job ID if enqueued successfully, None otherwise
        """
        # Extract job_id from kwargs if present
        job_id = kwargs.get('job_id')
        if not job_id:
            logger.error("job_id is required in kwargs")
            return None
        
        try:
            # Submit job to executor
            future = self.executor.submit(self._execute_job, func, job_id, *args, **kwargs)
            self.job_futures[job_id] = future
            logger.info(f"Enqueued job {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to enqueue job {job_id}: {e}")
            return None
    
    def _execute_job(self, func: Callable, job_id: int, *args, **kwargs):
        """Execute a job and update its status."""
        with Session(engine) as session:
            # Update job status to running
            job = session.get(ScrapeJob, job_id)
            if job:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(UTC)
                session.commit()
                logger.info(f"Starting job {job_id}")
        
        try:
            # Execute the job
            result = func(*args, **kwargs)
            logger.info(f"Job {job_id} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            # Update job status to failed
            with Session(engine) as session:
                job = session.get(ScrapeJob, job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(UTC)
                    job.error_message = str(e)
                    session.commit()
            raise
        finally:
            # Clean up future
            self.job_futures.pop(job_id, None)
    
    def _worker_loop(self):
        """Worker loop to process pending jobs from database."""
        while self.running:
            try:
                # Check for pending jobs in database
                with Session(engine) as session:
                    pending_jobs = session.exec(
                        select(ScrapeJob)
                        .where(ScrapeJob.status == JobStatus.PENDING)
                        .order_by(ScrapeJob.created_at)
                        .limit(10)
                    ).all()
                    
                    for job in pending_jobs:
                        # Skip if already being processed
                        if job.id in self.job_futures:
                            continue
                        
                        # Import worker function
                        try:
                            from .worker_v2 import scrape_website_job_v2
                            worker_func = scrape_website_job_v2
                        except ImportError:
                            from .worker import scrape_website_job
                            worker_func = scrape_website_job
                        
                        # Enqueue the job
                        self.enqueue(
                            worker_func,
                            website_id=job.website_id,
                            job_id=job.id
                        )
                
                # Sleep before checking again
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(10)


# Global job queue instance
job_queue = SimpleJobQueue(max_workers=int(os.getenv("WORKER_THREADS", "4")))


def enqueue_job(func: Callable, *args, **kwargs) -> Optional[int]:
    """Enqueue a job to the simple queue.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Job ID if enqueued successfully, None otherwise
    """
    # Ensure queue is started
    if not job_queue.running:
        job_queue.start()
    
    return job_queue.enqueue(func, *args, **kwargs)


def get_job_status(job_id: int) -> Optional[dict]:
    """Get job status by ID from database."""
    with Session(engine) as session:
        job = session.get(ScrapeJob, job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_message": job.error_message,
            "result_count": job.result_count
        }


def start_worker():
    """Start the job queue worker."""
    job_queue.start()
    logger.info("Simple job queue worker started")
    
    # Keep the worker running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping worker...")
        job_queue.stop()