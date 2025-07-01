from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from .base import Base, TimestampMixin


class JobType(str, enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    TEST = "test"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingJob(Base, TimestampMixin):
    __tablename__ = "scraping_jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), nullable=False)
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type"),
        default=JobType.FULL,
        nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True
    )
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    stats: Mapped[Optional[dict]] = mapped_column(JSONB)  # pages_scraped, pdfs_found, etc.
    
    # Relationships
    website: Mapped["Website"] = relationship(back_populates="scraping_jobs")