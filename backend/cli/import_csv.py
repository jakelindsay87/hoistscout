"""CLI tool for importing websites from CSV files."""
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from sqlmodel import Session, select
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hoistscraper.db import get_session
from hoistscraper.models import Website

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL validation regex
URL_REGEX = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


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


def run(path: str, batch_size: int = 1000) -> int:
    """
    Import websites from CSV file.
    
    Args:
        path: Path to CSV file
        batch_size: Number of rows to process at once (default 1000)
        
    Returns:
        Number of imported websites
        
    Expected CSV format:
        url,name,description (optional)
    """
    csv_path = Path(path)
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {path}")
        return 0
        
    if not csv_path.suffix.lower() == '.csv':
        logger.error(f"File must be a CSV: {path}")
        return 0
    
    logger.info(f"Starting import from {path}")
    
    # Track statistics
    total_processed = 0
    total_imported = 0
    total_skipped = 0
    
    try:
        # Process CSV in chunks for memory efficiency
        for chunk_num, chunk in enumerate(pd.read_csv(
            csv_path, 
            chunksize=batch_size,
            dtype={'url': str, 'name': str, 'description': str},
            keep_default_na=False
        )):
            logger.info(f"Processing chunk {chunk_num + 1} ({len(chunk)} rows)")
            
            # Process this chunk
            imported, skipped = process_chunk(chunk)
            
            total_processed += len(chunk)
            total_imported += imported
            total_skipped += skipped
            
            logger.info(f"Chunk {chunk_num + 1}: imported={imported}, skipped={skipped}")
    
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        return total_imported
    
    logger.info(f"Import complete: processed={total_processed}, imported={total_imported}, skipped={total_skipped}")
    return total_imported


def process_chunk(df: pd.DataFrame) -> Tuple[int, int]:
    """Process a chunk of CSV data."""
    imported = 0
    skipped = 0
    
    # Get database session
    session_gen = get_session()
    session = next(session_gen)
    try:
        # Get URLs from this chunk for batch duplicate check
        urls_in_chunk = []
        for _, row in df.iterrows():
            url = str(row.get('url', '')).strip()
            if url and validate_url(url):
                urls_in_chunk.append(url)
        
        # Batch check for existing URLs
        existing_urls = set()
        if urls_in_chunk:
            existing = session.exec(
                select(Website.url).where(Website.url.in_(urls_in_chunk))
            ).all()
            existing_urls = set(existing)
        
        # Prepare batch insert
        websites_to_create = []
        
        # Process each row
        for idx, row in df.iterrows():
            url = str(row.get('url', '')).strip()
            name = str(row.get('name', '')).strip()
            description = str(row.get('description', '')).strip() or None
            
            # Validate required fields
            if not url or not name:
                logger.warning(f"Row {idx + 1}: Missing required url or name")
                skipped += 1
                continue
            
            # Validate URL format
            if not validate_url(url):
                logger.warning(f"Row {idx + 1}: Invalid URL format: {url[:50]}...")
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
            try:
                website = Website(
                    url=url,
                    name=name,
                    description=description
                )
                websites_to_create.append(website)
                existing_urls.add(url)  # Track in current batch
                
            except Exception as e:
                logger.error(f"Error creating website object for {url}: {e}")
                skipped += 1
        
        # Bulk insert
        if websites_to_create:
            try:
                session.bulk_save_objects(websites_to_create)
                session.commit()
                imported = len(websites_to_create)
            except Exception as e:
                logger.error(f"Error committing batch: {e}")
                session.rollback()
                return 0, len(df)
    
    finally:
        # Properly close the session
        try:
            session_gen.close()
        except:
            pass
    
    return imported, skipped


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m backend.cli.import_csv <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    imported = run(csv_file)
    
    if imported > 0:
        print(f"Successfully imported {imported} websites")
        sys.exit(0)
    else:
        print("No websites imported")
        sys.exit(1)


if __name__ == "__main__":
    main()