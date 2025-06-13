"""Job management API routes."""
import logging
from typing import List, Optional
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from hoistscraper.db import get_session
from hoistscraper.models import Website, ScrapeJob, JobStatus
from hoistscraper.queue import enqueue_job, get_job_status, cancel_job
from hoistscraper.worker import scrape_website_job

router = APIRouter(prefix="/api", tags=["jobs"])
logger = logging.getLogger(__name__)


class JobResponse(BaseModel):
    """Response schema for job information."""
    id: int
    website_id: int
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_path: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response schema for job status check."""
    job_id: str
    status: str
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("/scrape/{website_id}", response_model=JobResponse)
def trigger_scrape(
    website_id: int,
    session: Session = Depends(get_session)
):
    """
    Trigger a scrape job for a specific website.
    
    Args:
        website_id: ID of the website to scrape
        
    Returns:
        Job information including job ID and status
    """
    # Verify website exists
    website = session.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail=f"Website {website_id} not found")
    
    # Create job record in database
    scrape_job = ScrapeJob(
        website_id=website_id,
        status=JobStatus.PENDING,
        created_at=datetime.now(UTC)
    )
    session.add(scrape_job)
    session.commit()
    session.refresh(scrape_job)
    
    # Enqueue job to RQ
    try:
        rq_job = enqueue_job(
            scrape_website_job,
            website_id,
            scrape_job.id,
            queue_name="scraper",
            job_id=f"scrape-{scrape_job.id}",
            description=f"Scrape {website.url}"
        )
        logger.info(f"Enqueued scrape job {scrape_job.id} for website {website_id}")
    except Exception as e:
        # Update job status to failed if enqueue fails
        scrape_job.status = JobStatus.FAILED
        scrape_job.error_message = f"Failed to enqueue job: {str(e)}"
        session.commit()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {str(e)}")
    
    return JobResponse(
        id=scrape_job.id,
        website_id=scrape_job.website_id,
        status=scrape_job.status,
        created_at=scrape_job.created_at,
        started_at=scrape_job.started_at,
        completed_at=scrape_job.completed_at,
        error_message=scrape_job.error_message,
        result_path=scrape_job.raw_data
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    session: Session = Depends(get_session)
):
    """
    Get information about a specific job.
    
    Args:
        job_id: ID of the job
        
    Returns:
        Job information
    """
    job = session.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobResponse(
        id=job.id,
        website_id=job.website_id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        result_path=job.raw_data
    )


@router.get("/jobs/{job_id}/status")
def check_job_status(job_id: str):
    """
    Check the status of a job in the queue.
    
    Args:
        job_id: RQ job ID (format: scrape-{db_job_id})
        
    Returns:
        Job status information from RQ
    """
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found in queue")
    
    return JobStatusResponse(
        job_id=job_id,
        status=status["status"],
        created_at=status["created_at"],
        started_at=status["started_at"],
        ended_at=status["ended_at"],
        result=status["result"],
        error=status["exc_info"]
    )


@router.post("/jobs/{job_id}/cancel")
def cancel_scrape_job(
    job_id: int,
    session: Session = Depends(get_session)
):
    """
    Cancel a pending or running job.
    
    Args:
        job_id: ID of the job to cancel
        
    Returns:
        Success status
    """
    # Get job from database
    job = session.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Check if job can be cancelled
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job in {job.status} status"
        )
    
    # Cancel in RQ
    rq_job_id = f"scrape-{job_id}"
    if cancel_job(rq_job_id):
        # Update database
        job.status = JobStatus.FAILED
        job.error_message = "Cancelled by user"
        job.completed_at = datetime.now(UTC)
        session.commit()
        
        return {"success": True, "message": f"Job {job_id} cancelled"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.get("/websites/{website_id}/jobs", response_model=List[JobResponse])
def get_website_jobs(
    website_id: int,
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """
    Get all jobs for a specific website.
    
    Args:
        website_id: ID of the website
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        
    Returns:
        List of jobs for the website
    """
    # Verify website exists
    website = session.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail=f"Website {website_id} not found")
    
    # Get jobs
    statement = (
        select(ScrapeJob)
        .where(ScrapeJob.website_id == website_id)
        .order_by(ScrapeJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    jobs = session.exec(statement).all()
    
    return [
        JobResponse(
            id=job.id,
            website_id=job.website_id,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            result_path=job.raw_data
        )
        for job in jobs
    ]