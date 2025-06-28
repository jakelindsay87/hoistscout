#!/usr/bin/env python3
"""Fix schema mismatch by updating models to match production database."""
import os
import sys

# Content for updated models.py
UPDATED_MODELS = '''from sqlmodel import SQLModel, Field
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
    name: str = Field(min_length=1, max_length=255) 
    description: Optional[str] = Field(default=None, max_length=1000)
    active: bool = True
    
    # Additional fields that exist in production database
    region: Optional[str] = Field(default=None, max_length=255)
    government_level: Optional[str] = Field(default=None, max_length=255)
    grant_type: Optional[str] = Field(default=None, max_length=255)
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
    """Grant opportunity extracted from scraped data."""
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    funding_amount: Optional[str] = Field(default=None, max_length=255)
    deadline: Optional[datetime] = None
    eligibility: Optional[str] = None
    application_url: Optional[str] = Field(default=None, max_length=2048)
    source_url: str = Field(max_length=2048)  # Original page URL
    website_id: int = Field(foreign_key="website.id")
    scrape_job_id: int = Field(foreign_key="scrapejob.id")

class Opportunity(OpportunityBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class OpportunityCreate(OpportunityBase):
    pass

class OpportunityRead(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: datetime
'''

def main():
    # Path to models.py
    models_path = "/root/hoistscraper/backend/hoistscraper/models.py"
    
    # Backup current models
    print("Backing up current models.py...")
    with open(models_path, 'r') as f:
        current_content = f.read()
    
    with open(models_path + '.backup', 'w') as f:
        f.write(current_content)
    
    print("✓ Backup created at models.py.backup")
    
    # Update models.py
    print("Updating models.py to match production schema...")
    with open(models_path, 'w') as f:
        f.write(UPDATED_MODELS)
    
    print("✓ models.py updated successfully")
    print("\nThe models have been updated to include:")
    print("  - region field")
    print("  - government_level field")
    print("  - grant_type field")
    print("  - credentials field")
    print("  - Opportunity model for extracted grant data")
    print("\nPlease rebuild and redeploy the backend to apply these changes.")

if __name__ == "__main__":
    main()