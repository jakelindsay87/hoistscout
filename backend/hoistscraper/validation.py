"""Input validation for security."""

import re
from typing import Optional
from urllib.parse import urlparse
from pydantic import validator
from sqlmodel import SQLModel, Field


class SecureWebsiteBase(SQLModel):
    """Website model with enhanced validation."""
    url: str = Field(index=True, unique=True, min_length=10, max_length=2048)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    active: bool = True
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format and security."""
        # Basic URL validation
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string")
        
        # Remove whitespace
        v = v.strip()
        
        # Check URL format
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
            
            # Only allow http/https
            if result.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP/HTTPS URLs are allowed")
            
            # Prevent localhost/internal IPs (SSRF protection)
            hostname = result.hostname
            if hostname:
                # Block localhost variants
                if hostname in ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']:
                    raise ValueError("Local URLs are not allowed")
                
                # Block private IP ranges
                private_ip_patterns = [
                    r'^10\.',
                    r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
                    r'^192\.168\.',
                ]
                for pattern in private_ip_patterns:
                    if re.match(pattern, hostname):
                        raise ValueError("Private network URLs are not allowed")
            
            return v
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate name field."""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        
        # Remove excess whitespace
        v = ' '.join(v.split())
        
        # Check for suspicious patterns
        if re.search(r'[<>\"\'`]', v):
            raise ValueError("Name contains invalid characters")
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description field."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
        
        # Remove excess whitespace
        v = ' '.join(v.split())
        
        # Basic XSS prevention - remove script tags and event handlers
        if re.search(r'<script|javascript:|on\w+\s*=', v, re.IGNORECASE):
            raise ValueError("Description contains potentially malicious content")
        
        return v


class SecureOpportunityBase(SQLModel):
    """Opportunity model with enhanced validation."""
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    source_url: str = Field(min_length=10, max_length=2048)
    website_id: int = Field(foreign_key="website.id")
    job_id: int = Field(foreign_key="scrapejob.id")
    deadline: Optional[str] = Field(default=None, max_length=100)
    amount: Optional[str] = Field(default=None, max_length=100)
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title field."""
        if not v or not isinstance(v, str):
            raise ValueError("Title must be a non-empty string")
        
        v = ' '.join(v.split())
        
        if re.search(r'[<>\"\'`]', v):
            raise ValueError("Title contains invalid characters")
        
        return v
    
    @validator('source_url')
    def validate_source_url(cls, v):
        """Validate source URL."""
        # Use same validation as website URL
        return SecureWebsiteBase.validate_url(v)
    
    @validator('description')
    def validate_opportunity_description(cls, v):
        """Validate opportunity description."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
        
        v = ' '.join(v.split())
        
        if re.search(r'<script|javascript:|on\w+\s*=', v, re.IGNORECASE):
            raise ValueError("Description contains potentially malicious content")
        
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate amount field."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Amount must be a string")
        
        v = v.strip()
        
        # Basic validation for currency amounts
        if len(v) > 100:
            raise ValueError("Amount is too long")
        
        return v


def sanitize_html(text: str) -> str:
    """Basic HTML sanitization."""
    if not text:
        return text
    
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    text = re.sub(r'\s*on\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes