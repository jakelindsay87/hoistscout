"""
Jobs API endpoint with database queue support.
This version can use either Celery or the database queue based on configuration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import traceback
import os

from ..database import get_db
from ..models.user import User, UserRole
from ..models.job import ScrapingJob, JobStatus
from ..schemas.job import JobCreate, JobResponse
from .auth import get_current_user

# Configure detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()

# Determine which queue system to use based on environment
USE_DB_QUEUE = os.getenv("USE_DB_QUEUE", "false").lower() == "true"

if USE_DB_QUEUE:
    logger.info("Using database queue instead of Celery")
    from ..db_queue import celery_app, scrape_website_task
else:
    logger.info("Using Celery with Redis")
    try:
        from ..worker import celery_app, scrape_website_task
    except ImportError:
        logger.warning("Celery import failed, falling back to database queue")
        USE_DB_QUEUE = True
        from ..db_queue import celery_app, scrape_website_task


def require_editor_role(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.EDITOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user


@router.post("/", response_model=JobResponse)
async def create_scraping_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_role)
):
    logger.info(f"=== CREATE_SCRAPING_JOB START ===")
    logger.info(f"User {current_user.email} creating job for website_id: {job_data.website_id}")
    logger.info(f"Job type: {job_data.job_type}, Priority: {job_data.priority}")
    logger.info(f"Using queue system: {'Database Queue' if USE_DB_QUEUE else 'Celery/Redis'}")
    
    try:
        # Create job in database
        job = ScrapingJob(
            website_id=job_data.website_id,
            job_type=job_data.job_type,
            priority=job_data.priority,
            scheduled_at=job_data.scheduled_at or datetime.utcnow()
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"✅ Job created in database with ID: {job.id}")
        logger.info(f"Job details: website_id={job.website_id}, status={job.status}, scheduled_at={job.scheduled_at}")
        
        # Queue the task
        logger.info("=== ATTEMPTING TO SEND TASK TO QUEUE ===")
        
        try:
            # Check queue status
            if USE_DB_QUEUE:
                logger.info("Using database queue backend")
                stats = celery_app.stats()
                logger.info(f"Database queue stats: {stats}")
            else:
                logger.info("Checking Celery connection...")
                try:
                    inspect = celery_app.control.inspect()
                    stats = inspect.stats()
                    if stats:
                        logger.info(f"✅ Celery workers available: {list(stats.keys())}")
                    else:
                        logger.warning("⚠️ No Celery workers detected!")
                except Exception as conn_error:
                    logger.error(f"❌ Celery connection check failed: {str(conn_error)}")
            
            # Send task to queue
            logger.info(f"Sending task to queue with task_id: {job.id}")
            logger.info(f"Task arguments: [website_id={job.website_id}]")
            
            result = scrape_website_task.apply_async(
                args=[job.website_id],
                task_id=str(job.id),
                priority=job.priority,
                queue='celery'
            )
            
            logger.info(f"✅ Task sent successfully!")
            logger.info(f"Task ID: {result.id}")
            logger.info(f"Task state: {result.state}")
            
        except Exception as queue_error:
            logger.error(f"❌ Failed to send task to queue: {str(queue_error)}")
            logger.error(f"Queue error type: {type(queue_error).__name__}")
            logger.error(f"Queue error traceback: {traceback.format_exc()}")
            
            # Update job status to failed
            job.status = JobStatus.FAILED
            job.error_message = f"Failed to queue task: {str(queue_error)}"
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to queue scraping task: {str(queue_error)}"
            )
        
        logger.info(f"=== CREATE_SCRAPING_JOB COMPLETED SUCCESSFULLY ===")
        return job
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as unexpected_error:
        logger.error(f"❌ Unexpected error in create_scraping_job: {str(unexpected_error)}")
        logger.error(f"Unexpected error traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(unexpected_error)}"
        )


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[JobStatus] = None,
    website_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    stmt = select(ScrapingJob)
    
    if status:
        stmt = stmt.where(ScrapingJob.status == status)
    if website_id:
        stmt = stmt.where(ScrapingJob.website_id == website_id)
    
    stmt = stmt.order_by(ScrapingJob.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_editor_role)
):
    stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending or running jobs"
        )
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.utcnow()
    
    await db.commit()
    
    # Cancel task in queue
    try:
        if USE_DB_QUEUE:
            from ..db_queue import TaskResult
            task_result = TaskResult(str(job_id), celery_app)
            task_result.revoke()
        else:
            celery_app.control.revoke(str(job_id), terminate=True)
    except Exception as e:
        logger.warning(f"Failed to revoke task: {e}")
    
    return {"detail": "Job cancelled successfully"}


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # TODO: Implement log streaming
    return {
        "job_id": job_id,
        "logs": [
            {"timestamp": datetime.utcnow(), "message": "Job started"},
            {"timestamp": datetime.utcnow(), "message": "Scraping website..."},
        ]
    }