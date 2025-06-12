"""CSV ingest API routes."""
import io
import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
import pandas as pd

from ..cli.import_csv import process_chunk

router = APIRouter(prefix="/api/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


class IngestResponse(BaseModel):
    """Response schema for CSV ingest."""
    imported: int
    skipped: int
    total: int
    errors: Optional[list[str]] = None


@router.post("/csv", response_model=IngestResponse)
async def ingest_csv(file: UploadFile = File(...)):
    """
    Upload and process a CSV file containing websites.
    
    Expected CSV format:
        url,name,description (optional)
    
    The file is processed in chunks to handle large files efficiently.
    """
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Check file size (optional - can be configured)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    # Reset file pointer
    await file.seek(0)
    
    logger.info(f"Processing CSV upload: {file.filename} ({len(contents)} bytes)")
    
    # Process the CSV
    total_imported = 0
    total_skipped = 0
    total_processed = 0
    errors = []
    
    try:
        # Read CSV in chunks using pandas
        csv_buffer = io.StringIO(contents.decode('utf-8'))
        
        for chunk_num, chunk in enumerate(pd.read_csv(
            csv_buffer,
            chunksize=1000,
            dtype={'url': str, 'name': str, 'description': str},
            keep_default_na=False
        )):
            try:
                imported, skipped = process_chunk(chunk)
                total_imported += imported
                total_skipped += skipped
                total_processed += len(chunk)
                
                logger.info(f"Processed chunk {chunk_num + 1}: imported={imported}, skipped={skipped}")
                
            except Exception as e:
                error_msg = f"Error processing chunk {chunk_num + 1}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    logger.info(f"CSV ingest complete: imported={total_imported}, skipped={total_skipped}, total={total_processed}")
    
    return IngestResponse(
        imported=total_imported,
        skipped=total_skipped,
        total=total_processed,
        errors=errors if errors else None
    )