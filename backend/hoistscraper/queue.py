"""Queue management with RQ and Redis."""
import os
import logging
from typing import Optional
from redis import Redis
from rq import Queue
from rq.job import Job

logger = logging.getLogger(__name__)

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)

# Create default queue
default_queue = Queue(connection=redis_conn)
scraper_queue = Queue("scraper", connection=redis_conn)


def get_redis_connection() -> Redis:
    """Get Redis connection instance."""
    return redis_conn


def get_queue(name: str = "default") -> Queue:
    """Get queue by name."""
    if name == "scraper":
        return scraper_queue
    return default_queue


def enqueue_job(func, *args, queue_name: str = "scraper", **kwargs) -> Job:
    """Enqueue a job to the specified queue."""
    queue = get_queue(queue_name)
    job = queue.enqueue(func, *args, **kwargs)
    logger.info(f"Enqueued job {job.id} to queue '{queue_name}'")
    return job


def get_job_status(job_id: str) -> Optional[dict]:
    """Get job status by ID."""
    job = Job.fetch(job_id, connection=redis_conn)
    if not job:
        return None
    
    return {
        "id": job.id,
        "status": job.get_status(),
        "created_at": job.created_at,
        "started_at": job.started_at,
        "ended_at": job.ended_at,
        "result": job.result,
        "exc_info": job.exc_info,
        "meta": job.meta
    }


def cancel_job(job_id: str) -> bool:
    """Cancel a job by ID."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        logger.info(f"Cancelled job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        return False