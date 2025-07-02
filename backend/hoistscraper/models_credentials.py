"""Credential models stub - placeholder for future implementation."""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class WebsiteCredentialBase(SQLModel):
    """Base model for website credentials."""
    website_id: int
    username: str
    encrypted_password: str
    encrypted_token: Optional[str] = None


class WebsiteCredential(WebsiteCredentialBase, table=True):
    """Database model for website credentials."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebsiteCredentialCreate(WebsiteCredentialBase):
    """Model for creating website credentials."""
    password: str
    token: Optional[str] = None