from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..database import get_db
from ..models.user import User, UserRole
from ..models.job import ScrapingJob, JobStatus
from ..schemas.job import JobCreate, JobResponse
from .auth import get_current_user

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
    # Create job
    job = ScrapingJob(
        website_id=job_data.website_id,
        job_type=job_data.job_type,
        priority=job_data.priority,
        scheduled_at=job_data.scheduled_at or datetime.utcnow()
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # TODO: Queue job with Celery
    
    return job


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