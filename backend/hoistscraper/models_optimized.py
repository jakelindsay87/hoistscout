"""Optimized database models with proper indexing for performance."""
from sqlmodel import SQLModel, Field, Index
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import validator
import re

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WebsiteBase(SQLModel):
    url: str = Field(index=True, unique=True, min_length=10, max_length=2048)
    name: str = Field(min_length=1, max_length=255, index=True) 
    description: Optional[str] = Field(default=None, max_length=1000)
    active: bool = Field(default=True, index=True)
    
    # Additional fields that exist in production database
    region: Optional[str] = Field(default=None, max_length=255, index=True)
    government_level: Optional[str] = Field(default=None, max_length=255, index=True)
    grant_type: Optional[str] = Field(default=None, max_length=255, index=True)
    credentials: Optional[str] = Field(default=None)  # For encrypted credentials
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format and prevent SSRF."""
        from urllib.parse import urlparse
        
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string")
        
        v = v.strip()
        
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
            
            if result.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP/HTTPS URLs are allowed")
            
            # Prevent SSRF attacks
            hostname = result.hostname
            if hostname and hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                raise ValueError("Local URLs are not allowed")
                
            return v
        except ValueError:
            raise
        except Exception:
            raise ValueError("Invalid URL format")
    
    @validator('name', 'description')
    def sanitize_text(cls, v):
        """Basic XSS prevention."""
        if v is None:
            return v
        
        if not isinstance(v, str):
            raise ValueError("Value must be a string")
        
        # Remove excess whitespace
        v = ' '.join(v.split())
        
        # Check for script tags or javascript
        if re.search(r'<script|javascript:', v, re.IGNORECASE):
            raise ValueError("Text contains potentially malicious content")
        
        return v

class Website(WebsiteBase, table=True):
    __table_args__ = (
        Index("idx_website_active_created", "active", "created_at"),
        Index("idx_website_region_type", "region", "grant_type"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

class WebsiteCreate(WebsiteBase):
    pass

class WebsiteRead(WebsiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ScrapeJobBase(SQLModel):
    website_id: int = Field(foreign_key="website.id", index=True)
    status: JobStatus = Field(default=JobStatus.PENDING, index=True)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    raw_data: Optional[str] = None

class ScrapeJob(ScrapeJobBase, table=True):
    __table_args__ = (
        Index("idx_scrapejob_status_created", "status", "created_at"),
        Index("idx_scrapejob_website_status", "website_id", "status"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

class ScrapeJobCreate(ScrapeJobBase):
    pass

class ScrapeJobRead(ScrapeJobBase):
    id: int
    created_at: datetime
    updated_at: datetime

class OpportunityBase(SQLModel):
    """Grant opportunity extracted from scraped data."""
    title: str = Field(min_length=1, max_length=500, index=True)
    description: Optional[str] = None
    funding_amount: Optional[str] = Field(default=None, max_length=255)
    deadline: Optional[datetime] = Field(default=None, index=True)
    eligibility: Optional[str] = None
    application_url: Optional[str] = Field(default=None, max_length=2048)
    source_url: str = Field(max_length=2048)  # Original page URL
    website_id: int = Field(foreign_key="website.id", index=True)
    scrape_job_id: int = Field(foreign_key="scrapejob.id", index=True)

class Opportunity(OpportunityBase, table=True):
    __table_args__ = (
        Index("idx_opportunity_website_created", "website_id", "created_at"),
        Index("idx_opportunity_deadline", "deadline"),
        Index("idx_opportunity_title_text", "title"),  # For text search
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class OpportunityCreate(OpportunityBase):
    pass

class OpportunityRead(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: datetime