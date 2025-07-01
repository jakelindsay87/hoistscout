from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class OpportunityCreate(BaseModel):
    website_id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    value: Optional[Decimal] = None
    currency: str = "USD"
    reference_number: Optional[str] = None
    source_url: str
    categories: Optional[List[str]] = None
    location: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class OpportunityResponse(BaseModel):
    id: int
    website_id: int
    title: str
    description: Optional[str]
    deadline: Optional[datetime]
    value: Optional[Decimal]
    currency: str
    reference_number: Optional[str]
    source_url: str
    categories: Optional[List[str]]
    location: Optional[str]
    extracted_data: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class OpportunitySearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    deadline_after: Optional[datetime] = None
    deadline_before: Optional[datetime] = None
    website_ids: Optional[List[int]] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)