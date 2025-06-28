"""Queue management with RQ and Redis."""
import os
import logging
import time
from typing import Optional
from redis import Redis, ConnectionError
from rq import Queue
from rq.job import Job

logger = logging.getLogger(__name__)


def create_redis_connection(max_retries: int = 10, initial_wait: int = 2) -> Redis:
    """Create Redis connection with improved retry logic using exponential backoff.
    
    Args:
        max_retries: Maximum number of connection attempts (default: 10)
        initial_wait: Initial wait time in seconds before first retry (default: 2)
        
    Returns:
        Redis connection instance
        
    Raises:
        ConnectionError: If all connection attempts fail
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    
    # Initial wait to allow services to start
    if initial_wait > 0:
        logger.info(f"Waiting {initial_wait} seconds before attempting Redis connection...")
        time.sleep(initial_wait)
    
    for attempt in range(max_retries):
        try:
            # Log connection attempt
            logger.info(f"Redis connection attempt {attempt + 1}/{max_retries}")
            
            # Try URL first, then host/port
            if redis_url != "redis://localhost:6379/0":
                redis_conn = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=10,  # Increased timeout
                    socket_timeout=10,
                    retry_on_timeout=True,
                    retry_on_error=[ConnectionError, TimeoutError],
                    health_check_interval=30
                )
            else:
                redis_conn = Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True,
                    socket_connect_timeout=10,  # Increased timeout
                    socket_timeout=10,
                    retry_on_timeout=True,
                    retry_on_error=[ConnectionError, TimeoutError],
                    health_check_interval=30
                )
            
            # Test connection with multiple pings
            for i in range(3):
                redis_conn.ping()
                if i > 0:
                    time.sleep(0.5)
            
            logger.info(f"Successfully connected to Redis at {redis_url or f'{redis_host}:{redis_port}'}")
            
            # Set a test key to ensure write capability
            redis_conn.set("worker:connection:test", "success", ex=60)
            
            return redis_conn
            
        except (ConnectionError, TimeoutError, Exception) as e:
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
            
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                base_sleep = min(2 ** attempt, 30)  # Cap at 30 seconds
                jitter = base_sleep * 0.1 * (0.5 - time.time() % 1)  # Add some randomness
                sleep_time = base_sleep + jitter
                
                logger.info(f"Retrying in {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"All {max_retries} Redis connection attempts failed")
                logger.error("Please ensure Redis is running and accessible")
                raise ConnectionError(f"Could not connect to Redis after {max_retries} attempts")


# Redis connection with retry logic
redis_conn = create_redis_connection()

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