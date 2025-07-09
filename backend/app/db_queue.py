"""
PostgreSQL-based task queue implementation as a drop-in replacement for Celery.
This module provides a simple task queue that uses PostgreSQL as the backend.
"""

import asyncio
import json
import logging
import traceback
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import inspect
import functools
import signal
import sys

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, Boolean, 
    create_engine, select, and_, or_, func, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from .config import get_settings

logger = logging.getLogger(__name__)

# Create base for our task queue models
TaskQueueBase = declarative_base()


class TaskStatus(str, Enum):
    """Task status enum matching Celery conventions."""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class TaskQueueModel(TaskQueueBase):
    """Database model for task queue."""
    __tablename__ = "task_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String, nullable=False, index=True)
    args = Column(JSON, default=list)
    kwargs = Column(JSON, default=dict)
    status = Column(String, default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, default=5, index=True)
    queue = Column(String, default="celery", index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    result = Column(JSON)
    error = Column(Text)
    traceback = Column(Text)
    
    worker_id = Column(String)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_countdown = Column(Integer)
    
    # Create composite index for efficient polling
    __table_args__ = (
        Index('idx_queue_status_priority', 'queue', 'status', 'priority'),
    )


class TaskResult:
    """Mimics Celery's AsyncResult class."""
    
    def __init__(self, task_id: str, db_queue: 'DBQueue'):
        self.id = task_id
        self.task_id = task_id
        self._db_queue = db_queue
        self.backend = "database"
    
    @property
    def state(self) -> str:
        """Get current task state."""
        with self._db_queue._get_db_session() as session:
            task = session.query(TaskQueueModel).filter_by(id=self.id).first()
            return task.status if task else TaskStatus.PENDING
    
    @property
    def info(self) -> Any:
        """Get task result or error info."""
        with self._db_queue._get_db_session() as session:
            task = session.query(TaskQueueModel).filter_by(id=self.id).first()
            if not task:
                return None
            if task.status == TaskStatus.SUCCESS:
                return task.result
            elif task.status == TaskStatus.FAILURE:
                return {"error": task.error, "traceback": task.traceback}
            return None
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """Wait for task result."""
        # Simple polling implementation
        import time
        start_time = time.time()
        
        while True:
            state = self.state
            if state in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
                return self.info
            
            if timeout and (time.time() - start_time) >= timeout:
                raise TimeoutError(f"Task {self.id} did not complete within {timeout} seconds")
            
            time.sleep(0.5)
    
    def revoke(self) -> None:
        """Cancel the task."""
        with self._db_queue._get_db_session() as session:
            task = session.query(TaskQueueModel).filter_by(id=self.id).first()
            if task and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.REVOKED
                session.commit()


class Task:
    """Represents a task that can be executed."""
    
    def __init__(self, func: Callable, name: str, db_queue: 'DBQueue', 
                 bind: bool = False, max_retries: int = 3):
        self.func = func
        self.name = name
        self.db_queue = db_queue
        self.bind = bind
        self.max_retries = max_retries
        self.request = None  # Will be set during execution
        
        # Make the task callable
        functools.update_wrapper(self, func)
    
    def __call__(self, *args, **kwargs):
        """Direct task execution."""
        if self.bind and self.request:
            return self.func(self, *args, **kwargs)
        return self.func(*args, **kwargs)
    
    def apply_async(self, args: tuple = None, kwargs: dict = None, 
                   task_id: str = None, priority: int = 5, 
                   queue: str = 'celery', countdown: int = None) -> TaskResult:
        """Queue task for async execution (Celery-compatible)."""
        args = args or []
        kwargs = kwargs or {}
        task_id = task_id or str(uuid.uuid4())
        
        with self.db_queue._get_db_session() as session:
            task = TaskQueueModel(
                id=task_id,
                task_name=self.name,
                args=list(args),
                kwargs=dict(kwargs),
                priority=priority,
                queue=queue,
                max_retries=self.max_retries,
                retry_countdown=countdown
            )
            session.add(task)
            session.commit()
        
        logger.info(f"Task {self.name}[{task_id}] queued with priority {priority}")
        return TaskResult(task_id, self.db_queue)
    
    def delay(self, *args, **kwargs) -> TaskResult:
        """Shortcut for apply_async with just args/kwargs."""
        return self.apply_async(args=args, kwargs=kwargs)
    
    def retry(self, exc: Exception = None, countdown: int = 60):
        """Retry the current task."""
        if not self.request:
            raise RuntimeError("retry() can only be called from within a task")
        
        with self.db_queue._get_db_session() as session:
            task = session.query(TaskQueueModel).filter_by(id=self.request.id).first()
            if task:
                task.retry_count += 1
                task.status = TaskStatus.RETRY
                task.error = str(exc) if exc else None
                task.retry_countdown = countdown
                session.commit()
        
        # Re-raise to stop current execution
        raise exc if exc else Exception("Task retry requested")


class TaskRequest:
    """Represents the current task execution context."""
    
    def __init__(self, task_id: str, retries: int = 0):
        self.id = task_id
        self.retries = retries
        self.delivery_info = {"routing_key": "celery"}


class DBQueue:
    """Main database queue implementation mimicking Celery interface."""
    
    def __init__(self, name: str = "hoistscout", broker: str = None, backend: str = None):
        self.name = name
        self.main = name
        self.tasks = {}
        self.conf = {
            "broker_url": broker or "postgresql://",
            "result_backend": backend or "postgresql://",
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "UTC",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": 30 * 60,
            "task_soft_time_limit": 25 * 60,
            "worker_prefetch_multiplier": 1,
            "worker_max_tasks_per_child": 1000,
            "task_default_queue": "celery",
            "task_create_missing_queues": True,
        }
        
        # Initialize database
        settings = get_settings()
        self.engine = create_engine(settings.database_url, pool_pre_ping=True)
        TaskQueueBase.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # For async operations
        database_url = settings.database_url
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self.async_engine = create_async_engine(database_url)
        self.AsyncSessionLocal = async_sessionmaker(self.async_engine, class_=AsyncSession)
    
    def _get_db_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def task(self, name: str = None, bind: bool = False, max_retries: int = 3):
        """Decorator to register a task."""
        def decorator(func: Callable) -> Task:
            task_name = name or f"{self.name}.{func.__module__}.{func.__name__}"
            task = Task(func, task_name, self, bind=bind, max_retries=max_retries)
            self.tasks[task_name] = task
            return task
        return decorator
    
    def autodiscover_tasks(self, packages: List[str], related_name: str = None):
        """Autodiscover tasks in packages (compatibility method)."""
        # In our case, tasks are registered via decorator, so this is a no-op
        logger.info(f"Autodiscovering tasks in packages: {packages}")
    
    @property
    def control(self):
        """Mimics Celery's control interface."""
        return self
    
    def inspect(self):
        """Mimics Celery's inspect interface."""
        return self
    
    def stats(self) -> Dict[str, Any]:
        """Get worker stats."""
        with self._get_db_session() as session:
            pending = session.query(func.count(TaskQueueModel.id)).filter_by(
                status=TaskStatus.PENDING
            ).scalar()
            running = session.query(func.count(TaskQueueModel.id)).filter_by(
                status=TaskStatus.STARTED
            ).scalar()
            
            return {
                "db-worker": {
                    "pending": pending,
                    "running": running,
                    "status": "online"
                }
            }


class Worker:
    """Database queue worker that polls and executes tasks."""
    
    def __init__(self, db_queue: DBQueue, worker_id: str = None, 
                 queues: List[str] = None, concurrency: int = 1):
        self.db_queue = db_queue
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.queues = queues or ["celery"]
        self.concurrency = concurrency
        self.running = False
        self._tasks = []
        
        # Handle signals for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Worker {self.worker_id} received signal {signum}, shutting down...")
        self.running = False
    
    def _claim_task(self, session: Session) -> Optional[TaskQueueModel]:
        """Claim a pending task from the queue."""
        # Use SELECT FOR UPDATE SKIP LOCKED for efficient concurrent access
        task = session.query(TaskQueueModel).filter(
            and_(
                TaskQueueModel.status == TaskStatus.PENDING,
                TaskQueueModel.queue.in_(self.queues)
            )
        ).order_by(
            TaskQueueModel.priority.desc(),
            TaskQueueModel.created_at
        ).with_for_update(skip_locked=True).first()
        
        if task:
            task.status = TaskStatus.STARTED
            task.started_at = datetime.utcnow()
            task.worker_id = self.worker_id
            session.commit()
            
        return task
    
    def _execute_task(self, task_record: TaskQueueModel):
        """Execute a single task."""
        logger.info(f"Executing task {task_record.task_name}[{task_record.id}]")
        
        try:
            # Get the task function
            task_func = self.db_queue.tasks.get(task_record.task_name)
            if not task_func:
                raise ValueError(f"Unknown task: {task_record.task_name}")
            
            # Set up task context
            task_func.request = TaskRequest(task_record.id, task_record.retry_count)
            
            # Execute the task
            args = task_record.args or []
            kwargs = task_record.kwargs or {}
            
            # Handle async tasks
            if asyncio.iscoroutinefunction(task_func.func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(task_func(*args, **kwargs))
            else:
                result = task_func(*args, **kwargs)
            
            # Update task status
            with self.db_queue._get_db_session() as session:
                task = session.query(TaskQueueModel).filter_by(id=task_record.id).first()
                task.status = TaskStatus.SUCCESS
                task.completed_at = datetime.utcnow()
                task.result = result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result)
                session.commit()
            
            logger.info(f"Task {task_record.task_name}[{task_record.id}] completed successfully")
            
        except Exception as exc:
            logger.error(f"Task {task_record.task_name}[{task_record.id}] failed: {exc}")
            logger.error(traceback.format_exc())
            
            with self.db_queue._get_db_session() as session:
                task = session.query(TaskQueueModel).filter_by(id=task_record.id).first()
                
                # Check if task requested retry
                if task.status == TaskStatus.RETRY and task.retry_count <= task.max_retries:
                    # Re-queue for retry
                    task.status = TaskStatus.PENDING
                    task.worker_id = None
                    task.started_at = None
                    if task.retry_countdown:
                        task.created_at = datetime.utcnow() + timedelta(seconds=task.retry_countdown)
                else:
                    # Mark as failed
                    task.status = TaskStatus.FAILURE
                    task.completed_at = datetime.utcnow()
                    task.error = str(exc)
                    task.traceback = traceback.format_exc()
                
                session.commit()
    
    def run(self):
        """Start the worker loop."""
        logger.info(f"Worker {self.worker_id} starting, monitoring queues: {self.queues}")
        self.running = True
        
        while self.running:
            try:
                with self.db_queue._get_db_session() as session:
                    task = self._claim_task(session)
                    
                    if task:
                        self._execute_task(task)
                    else:
                        # No tasks available, sleep briefly
                        import time
                        time.sleep(1)
                        
            except Exception as exc:
                logger.error(f"Worker error: {exc}")
                logger.error(traceback.format_exc())
                import time
                time.sleep(5)  # Back off on errors
        
        logger.info(f"Worker {self.worker_id} stopped")


# Create a default instance to mimic Celery usage
celery_app = DBQueue("hoistscout")
celery = celery_app
worker = celery_app


# Register the scrape_website_task to match existing code
@celery_app.task(bind=True, name='app.worker.scrape_website_task', max_retries=3)
def scrape_website_task(self, website_id: int):
    """Scrape a single website."""
    logger.info(f"=== SCRAPE_WEBSITE_TASK STARTED ===")
    logger.info(f"Task ID: {self.request.id}")
    logger.info(f"Website ID: {website_id}")
    logger.info(f"Retry count: {self.request.retries}")
    
    try:
        # Run async scraping in sync context
        logger.info("Creating new event loop for async operations...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from .database import AsyncSessionLocal
        from .models.website import Website
        from .models.job import ScrapingJob, JobStatus
        from .models.opportunity import Opportunity
        from sqlalchemy import select
        
        async def run_scraping():
            async with AsyncSessionLocal() as db:
                # Get website
                stmt = select(Website).where(Website.id == website_id)
                result = await db.execute(stmt)
                website = result.scalar_one_or_none()
                
                if not website:
                    raise ValueError(f"Website {website_id} not found")
                
                # Update job status
                job_id = self.request.id
                if job_id:
                    job_stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
                    job_result = await db.execute(job_stmt)
                    job = job_result.scalar_one_or_none()
                    if job:
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.utcnow()
                        await db.commit()
                
                # Use Gemini scraper directly for production
                try:
                    from .core.gemini_scraper import GeminiScraper
                    
                    logger.info(f"Starting Gemini scraper for website {website_id}")
                    
                    # Create Gemini scraper
                    scraper = GeminiScraper()
                    
                    # Execute scraping
                    result = await scraper.scrape_website(website)
                    
                    logger.info(f"Scraping completed: {result.total_found} opportunities found")
                    
                except Exception as e:
                    logger.error(f"Gemini scraping failed: {e}")
                    # Return error result
                    from datetime import datetime
                    result = type('obj', (object,), {
                        'opportunities': [],
                        'success': False,
                        'error_message': f"Scraping error: {str(e)}",
                        'stats': {
                            'error': str(e),
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        'total_found': 0
                    })
                
                # Save opportunities
                for opp_data in result.opportunities:
                    opportunity = Opportunity(
                        website_id=website_id,
                        title=opp_data.get("title"),
                        description=opp_data.get("description"),
                        deadline=opp_data.get("deadline"),
                        value=opp_data.get("value"),
                        currency=opp_data.get("currency", "USD"),
                        reference_number=opp_data.get("reference_number"),
                        source_url=opp_data.get("source_url"),
                        categories=opp_data.get("categories", []),
                        location=opp_data.get("location"),
                        extracted_data=opp_data,
                        confidence_score=opp_data.get("confidence_score", 1.0)
                    )
                    db.add(opportunity)
                
                # Update job status
                if job:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    job.stats = getattr(result, 'stats', {})
                
                await db.commit()
                
                logger.info(f"Database commit successful for website {website_id}")
                return getattr(result, 'stats', {})
        
        logger.info("Starting async scraping operation...")
        result = loop.run_until_complete(run_scraping())
        logger.info(f"=== SCRAPE_WEBSITE_TASK COMPLETED SUCCESSFULLY ===")
        logger.info(f"Result: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"=== SCRAPE_WEBSITE_TASK FAILED ===")
        logger.error(f"Error type: {type(exc).__name__}")
        logger.error(f"Error message: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log error and retry
        retry_countdown = 60 * (self.request.retries + 1)
        logger.info(f"Retrying task in {retry_countdown} seconds...")
        self.retry(exc=exc, countdown=retry_countdown)


# Also register other tasks
@celery_app.task(name='app.worker.process_pdf_task')
def process_pdf_task(document_id: int):
    from .worker import process_pdf_task as original_task
    return original_task(document_id)


@celery_app.task(name='app.worker.scrape_all_active_websites')
def scrape_all_active_websites():
    from .worker import scrape_all_active_websites as original_task
    return original_task()


@celery_app.task(name='app.worker.cleanup_old_jobs')
def cleanup_old_jobs():
    from .worker import cleanup_old_jobs as original_task
    return original_task()


if __name__ == "__main__":
    # Allow running as a standalone worker
    worker = Worker(celery_app)
    worker.run()