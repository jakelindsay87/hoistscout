from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field
from ..models.website import AuthType


class WebsiteConfig(BaseModel):
    id: int
    url: str
    auth_type: AuthType
    credentials: Optional[bytes] = None
    requires_auth: bool = False
    is_search_based: bool = False
    max_pages: Optional[int] = None
    extraction_hints: Optional[str] = None


class WebsiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    category: Optional[str] = Field(None, max_length=50)
    auth_type: AuthType = AuthType.NONE
    credentials: Optional[Dict[str, str]] = None
    scraping_config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class WebsiteUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, max_length=50)
    auth_type: Optional[AuthType] = None
    credentials: Optional[Dict[str, str]] = None
    scraping_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WebsiteResponse(BaseModel):
    id: int
    name: str
    url: str
    category: Optional[str]
    auth_type: AuthType
    scraping_config: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}