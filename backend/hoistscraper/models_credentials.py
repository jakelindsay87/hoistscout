"""Credential models for secure storage of website authentication data."""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class WebsiteCredentialBase(SQLModel):
    """Base model for website credentials."""
    website_id: int
    username: str
    password_encrypted: str  # Changed from encrypted_password to match credential_manager.py
    auth_type: str = "basic"
    additional_fields: Optional[str] = None  # JSON string for extra auth fields
    notes: Optional[str] = None
    is_valid: bool = True
    last_used_at: Optional[datetime] = None


class WebsiteCredential(WebsiteCredentialBase, table=True):
    """Database model for website credentials."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebsiteCredentialCreate(SQLModel):
    """Model for creating website credentials."""
    website_id: int
    username: str
    password: str  # Plain text, will be encrypted before storage
    auth_type: str = "basic"
    additional_fields: Optional[str] = None
    notes: Optional[str] = None


class WebsiteCredentialRead(SQLModel):
    """Model for reading website credentials (without password)."""
    id: int
    website_id: int
    username: str
    auth_type: str
    additional_fields: Optional[str] = None
    notes: Optional[str] = None
    is_valid: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None