from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    filename: str
    file_size: int
    mime_type: str
    pages: int = 0
    has_images: bool = False
    has_tables: bool = False


class ProcessedDocument(BaseModel):
    source_url: str
    minio_object_key: Optional[str] = None
    extracted_text: str
    extracted_data: Dict[str, Any]
    metadata: Optional[DocumentMetadata] = None
    processing_status: str
    processed_at: datetime