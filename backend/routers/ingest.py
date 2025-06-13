"""CSV ingest API routes."""
import io
import logging
import os
import tempfile
from typing import Optional, List
import chardet
import re
from urllib.parse import urlparse

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import pandas as pd
from sqlmodel import Session, select

from ..hoistscraper.db import get_session
from ..hoistscraper.models import Website

router = APIRouter(prefix="/api/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Configuration
MAX_FILE_SIZE = int(os.getenv("CSV_MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB default
CHUNK_SIZE = int(os.getenv("CSV_CHUNK_SIZE", 1000))
ALLOWED_CONTENT_TYPES = {"text/csv", "application/csv", "text/plain"}
URL_REGEX = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


class IngestResponse(BaseModel):
    """Response schema for CSV ingest."""
    imported: int = Field(description="Number of successfully imported websites")
    skipped: int = Field(description="Number of skipped websites (duplicates or invalid)")
    total: int = Field(description="Total number of rows processed")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


def validate_url(url: str) -> bool:
    """Validate URL format and safety."""
    if not url or len(url) > 2048:  # Max URL length
        return False
    return bool(URL_REGEX.match(url))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize and truncate string input."""
    if not value:
        return ""
    # Remove control characters and normalize whitespace
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    value = ' '.join(value.split())
    return value[:max_length]


def process_csv_chunk(chunk: pd.DataFrame, session: Session) -> tuple[int, int, List[str]]:
    """Process a chunk of CSV data with proper validation."""
    imported = 0
    skipped = 0
    chunk_errors = []
    
    # Get existing URLs for this chunk
    urls_in_chunk = [str(row.get('url', '')).strip() for _, row in chunk.iterrows()]
    existing_urls = set()
    if urls_in_chunk:
        existing = session.exec(select(Website.url).where(Website.url.in_(urls_in_chunk))).all()
        existing_urls = set(existing)
    
    # Batch create websites
    websites_to_create = []
    
    for idx, row in chunk.iterrows():
        try:
            url = str(row.get('url', '')).strip()
            name = str(row.get('name', '')).strip()
            description = str(row.get('description', '')).strip() or None
            
            # Validate required fields
            if not url or not name:
                chunk_errors.append(f"Row {idx + 1}: Missing required url or name")
                skipped += 1
                continue
            
            # Validate URL
            if not validate_url(url):
                chunk_errors.append(f"Row {idx + 1}: Invalid URL format: {url[:50]}...")
                skipped += 1
                continue
            
            # Skip if URL already exists
            if url in existing_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                skipped += 1
                continue
            
            # Sanitize inputs
            name = sanitize_string(name, 255)
            if description:
                description = sanitize_string(description, 1000)
            
            # Create website object
            website = Website(
                url=url,
                name=name,
                description=description
            )
            websites_to_create.append(website)
            existing_urls.add(url)  # Track in current batch
            
        except Exception as e:
            chunk_errors.append(f"Row {idx + 1}: {str(e)}")
            skipped += 1
    
    # Bulk insert
    if websites_to_create:
        try:
            session.bulk_save_objects(websites_to_create)
            session.commit()
            imported = len(websites_to_create)
        except Exception as e:
            session.rollback()
            chunk_errors.append(f"Database error: {str(e)}")
            return 0, len(chunk), chunk_errors
    
    return imported, skipped, chunk_errors


@router.post("/csv", response_model=IngestResponse)
async def ingest_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Upload and process a CSV file containing websites.
    
    Expected CSV format:
        url,name,description (optional)
    
    The file is processed in chunks to handle large files efficiently.
    Security features:
    - File size validation
    - Content type validation
    - URL format validation
    - Input sanitization
    - Optional authentication via Bearer token
    """
    # Optional authentication check
    if os.getenv("REQUIRE_AUTH_FOR_INGEST", "false").lower() == "true":
        if not credentials:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Add your token validation logic here
    
    # Validate filename and content type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must have .csv extension")
    
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid content type. Expected one of: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    # Stream file to temporary location to avoid memory issues
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tf:
            temp_file = tf.name
            
            # Stream file in chunks to avoid memory issues
            total_size = 0
            chunk_size = 8192  # 8KB chunks
            
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    os.unlink(temp_file)
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"
                    )
                
                tf.write(chunk)
        
        # Detect encoding
        with open(temp_file, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            logger.info(f"Detected encoding: {encoding} (confidence: {result.get('confidence', 0):.2f})")
        
        logger.info(f"Processing CSV upload: {file.filename} ({total_size} bytes)")
    
        # Process the CSV
        total_imported = 0
        total_skipped = 0
        total_processed = 0
        all_errors = []
        
        try:
            # Validate CSV structure first
            preview_df = pd.read_csv(temp_file, nrows=5, encoding=encoding)
            required_columns = {'url', 'name'}
            missing_columns = required_columns - set(preview_df.columns)
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            # Process in chunks
            for chunk_num, chunk in enumerate(pd.read_csv(
                temp_file,
                chunksize=CHUNK_SIZE,
                dtype={'url': str, 'name': str, 'description': str},
                keep_default_na=False,
                encoding=encoding,
                on_bad_lines='skip'
            )):
                try:
                    imported, skipped, chunk_errors = process_csv_chunk(chunk, session)
                    total_imported += imported
                    total_skipped += skipped
                    total_processed += len(chunk)
                    
                    if chunk_errors:
                        all_errors.extend(chunk_errors)
                    
                    logger.info(f"Processed chunk {chunk_num + 1}: imported={imported}, skipped={skipped}")
                    
                except Exception as e:
                    error_msg = f"Error processing chunk {chunk_num + 1}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    all_errors.append(error_msg)
                    # Continue processing other chunks
        
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error processing CSV: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
        
        logger.info(f"CSV ingest complete: imported={total_imported}, skipped={total_skipped}, total={total_processed}")
        
        # Limit errors in response to prevent oversized responses
        if len(all_errors) > 100:
            all_errors = all_errors[:100] + [f"... and {len(all_errors) - 100} more errors"]
        
        return IngestResponse(
            imported=total_imported,
            skipped=total_skipped,
            total=total_processed,
            errors=all_errors if all_errors else None
        )
    
    except Exception as e:
        # Ensure temp file is cleaned up on any error
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        raise