from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import traceback

from ..database import get_db
from ..models.user import User, UserRole
from ..models.job import ScrapingJob, JobStatus
from ..schemas.job import JobCreate, JobResponse
from .auth import get_current_user

# Configure detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()


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
        
        # Import and log Celery app details
        logger.info("=== ATTEMPTING TO SEND TASK TO CELERY ===")
        
        try:
            from ..worker import scrape_website_task, celery_app
            
            # Log Celery configuration
            logger.info(f"Celery broker URL: {celery_app.conf.get('broker_url', 'NOT SET')}")
            logger.info(f"Celery backend URL: {celery_app.conf.get('result_backend', 'NOT SET')}")
            logger.info(f"Celery task routes: {celery_app.conf.get('task_routes', {})}")
            logger.info(f"Available queues: {list(celery_app.conf.get('task_queues', []))}")
            
            # Check if Celery connection is alive
            logger.info("Checking Celery connection...")
            try:
                # This will raise an exception if broker is not reachable
                inspect = celery_app.control.inspect()
                stats = inspect.stats()
                if stats:
                    logger.info(f"✅ Celery workers available: {list(stats.keys())}")
                else:
                    logger.warning("⚠️ No Celery workers detected!")
            except Exception as conn_error:
                logger.error(f"❌ Celery connection check failed: {str(conn_error)}")
                logger.error(f"Connection error traceback: {traceback.format_exc()}")
            
            # Send task to Celery
            logger.info(f"Sending task to Celery queue 'celery' with task_id: {job.id}")
            logger.info(f"Task arguments: [website_id={job.website_id}]")
            
            result = scrape_website_task.apply_async(
                args=[job.website_id],
                task_id=str(job.id),
                priority=job.priority,
                queue='celery'  # Explicitly set queue
            )
            
            logger.info(f"✅ Task sent successfully!")
            logger.info(f"Task ID: {result.id}")
            logger.info(f"Task state: {result.state}")
            logger.info(f"Task backend: {result.backend}")
            
            # Try to get task info
            try:
                task_info = result.info
                logger.info(f"Task info: {task_info}")
            except Exception as info_error:
                logger.warning(f"Could not get task info: {str(info_error)}")
            
        except ImportError as import_error:
            logger.error(f"❌ Failed to import Celery components: {str(import_error)}")
            logger.error(f"Import error traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import Celery worker: {str(import_error)}"
            )
        except Exception as celery_error:
            logger.error(f"❌ Failed to send task to Celery: {str(celery_error)}")
            logger.error(f"Celery error type: {type(celery_error).__name__}")
            logger.error(f"Celery error traceback: {traceback.format_exc()}")
            
            # Update job status to failed
            job.status = JobStatus.FAILED
            job.error_message = f"Failed to queue task: {str(celery_error)}"
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to queue scraping task: {str(celery_error)}"
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
    
    # TODO: Cancel Celery task
    
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