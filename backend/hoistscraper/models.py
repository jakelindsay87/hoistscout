from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WebsiteBase(SQLModel):
    url: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None
    active: bool = True

class Website(WebsiteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WebsiteCreate(WebsiteBase):
    pass

class WebsiteRead(WebsiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ScrapeJobBase(SQLModel):
    website_id: int = Field(foreign_key="website.id")
    status: JobStatus = JobStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    raw_data: Optional[str] = None

class ScrapeJob(ScrapeJobBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScrapeJobCreate(ScrapeJobBase):
    pass

class ScrapeJobRead(ScrapeJobBase):
    id: int
    created_at: datetime
    updated_at: datetime

class OpportunityBase(SQLModel):
    title: str
    description: Optional[str] = None
    source_url: str
    website_id: int = Field(foreign_key="website.id")
    job_id: int = Field(foreign_key="scrapejob.id")
    deadline: Optional[datetime] = None
    amount: Optional[str] = None

class Opportunity(OpportunityBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityRead(OpportunityBase):
    id: int
    scraped_at: datetime

 