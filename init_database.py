#!/usr/bin/env python3
"""Initialize the database and create tables."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from hoistscraper.db import create_db_and_tables, engine
from hoistscraper.models import Website, ScrapeJob
from sqlmodel import Session, select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database and create tables."""
    try:
        logger.info("Creating database tables...")
        create_db_and_tables()
        logger.info("✓ Database tables created successfully")
        
        # Test the connection
        with Session(engine) as session:
            # Try to count websites
            count = len(session.exec(select(Website)).all())
            logger.info(f"✓ Found {count} websites in database")
            
            # Add a test website if none exist
            if count == 0:
                logger.info("Adding test website...")
                test_site = Website(
                    name="Australian Government Grants",
                    url="https://www.grants.gov.au",
                    crawl_enabled=True
                )
                session.add(test_site)
                session.commit()
                logger.info("✓ Added test website")
                
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)