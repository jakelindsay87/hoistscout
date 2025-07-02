from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..models.job import JobType, JobStatus as JobStatusEnum


class JobCreate(BaseModel):
    website_id: int
    job_type: JobType = JobType.FULL
    priority: int = Field(5, ge=1, le=10)
    scheduled_at: Optional[datetime] = None


class JobResponse(BaseModel):
    id: int
    website_id: int
    job_type: JobType
    status: JobStatusEnum
    priority: int
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    stats: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class JobStatus(BaseModel):
    job_id: int
    status: JobStatusEnum
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    current_action: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None