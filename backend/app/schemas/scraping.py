from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TenderData(BaseModel):
    title: str
    description: str
    deadline: Optional[datetime] = None
    value: Optional[float] = None
    currency: str = "USD"
    reference_number: Optional[str] = None
    source_url: str
    document_urls: List[str] = []
    categories: List[str] = []
    location: Optional[str] = None
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)


class ScrapingResult(BaseModel):
    website_id: int
    opportunities: List[TenderData]
    total_found: int
    pdfs_processed: int
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None