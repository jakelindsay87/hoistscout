"""CLI tool for importing websites from CSV files."""
import sys
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlmodel import Session, select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hoistscraper.db import get_session
from hoistscraper.models import Website

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def process_chunk(df: pd.DataFrame) -> tuple[int, int]:
    """Process a chunk of CSV data."""
    imported = 0
    skipped = 0
    
    # Get database session
    with next(get_session()) as session:
        # Get existing URLs for deduplication
        existing_urls = set()
        stmt = select(Website.url)
        for row in session.exec(stmt):
            existing_urls.add(row)
        
        # Process each row
        for _, row in df.iterrows():
            url = str(row.get('url', '')).strip()
            name = str(row.get('name', '')).strip()
            description = str(row.get('description', '')).strip() or None
            
            # Validate required fields
            if not url or not name:
                logger.warning(f"Skipping row with missing url or name: {row}")
                skipped += 1
                continue
            
            # Skip if URL already exists
            if url in existing_urls:
                logger.debug(f"Skipping duplicate URL: {url}")
                skipped += 1
                continue
            
            # Create website
            try:
                website = Website(
                    url=url,
                    name=name,
                    description=description
                )
                session.add(website)
                existing_urls.add(url)  # Track in current batch
                imported += 1
                
            except Exception as e:
                logger.error(f"Error creating website {url}: {e}")
                skipped += 1
        
        # Commit the batch
        try:
            session.commit()
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            session.rollback()
            return 0, len(df)
    
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