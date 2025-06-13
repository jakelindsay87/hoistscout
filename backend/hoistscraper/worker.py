"""Background worker for scraping jobs."""
import os
import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import stealth_sync
from sqlmodel import Session

from hoistscraper.db import get_session, engine
from hoistscraper.models import Website, ScrapeJob, JobStatus
from hoistscraper.crawler.base import BaseCrawler

logger = logging.getLogger(__name__)

# Data directory for storing scraped content
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(exist_ok=True)


class ScraperWorker:
    """Base scraper worker class."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    def initialize_browser(self):
        """Initialize Playwright browser."""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def scrape_website(self, website_id: int, job_id: int) -> Dict[str, Any]:
        """
        Scrape a website and save results.
        
        Args:
            website_id: ID of the website to scrape
            job_id: ID of the scrape job
            
        Returns:
            Dictionary with scrape results
        """
        with Session(engine) as session:
            # Get website details
            website = session.get(Website, website_id)
            if not website:
                raise ValueError(f"Website {website_id} not found")
            
            # Update job status to running
            job = session.get(ScrapeJob, job_id)
            if job:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(UTC)
                session.commit()
            
            try:
                # Initialize browser if needed
                self.initialize_browser()
                
                # Create a new page
                page = self.browser.new_page()
                stealth_sync(page)
                
                # Check if website requires authentication
                if hasattr(website, 'requires_auth') and website.requires_auth:
                    self._handle_login(page, website)
                
                # Navigate to the website
                logger.info(f"Navigating to {website.url}")
                page.goto(website.url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                page.wait_for_load_state('domcontentloaded')
                
                # Extract data
                result = {
                    "website_id": website_id,
                    "url": website.url,
                    "scraped_at": datetime.now(UTC).isoformat(),
                    "title": page.title(),
                    "content": page.content(),
                    "metadata": {
                        "viewport": page.viewport_size,
                        "url": page.url,
                    }
                }
                
                # Save raw HTML
                html_path = DATA_DIR / f"{job_id}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(result["content"])
                
                # Save metadata as JSON
                json_path = DATA_DIR / f"{job_id}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "website_id": website_id,
                        "url": website.url,
                        "title": result["title"],
                        "scraped_at": result["scraped_at"],
                        "html_path": str(html_path),
                        "metadata": result["metadata"]
                    }, f, indent=2)
                
                # Update job status to completed
                if job:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(UTC)
                    job.raw_data = str(json_path)
                    session.commit()
                
                logger.info(f"Successfully scraped {website.url}")
                page.close()
                return result
                
            except Exception as e:
                logger.error(f"Error scraping {website.url}: {str(e)}")
                
                # Update job status to failed
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(UTC)
                    job.error_message = str(e)
                    session.commit()
                
                raise
    
    def _handle_login(self, page: Page, website: Website):
        """Handle website authentication if required."""
        # This is a placeholder for login logic
        # In a real implementation, this would:
        # 1. Check for stored credentials
        # 2. Navigate to login page
        # 3. Fill in credentials
        # 4. Submit and verify login success
        logger.info(f"Login required for {website.url} - not implemented yet")
        pass


def scrape_website_job(website_id: int, job_id: int) -> Dict[str, Any]:
    """
    RQ job function for scraping a website.
    
    This is the function that will be enqueued to RQ.
    """
    worker = ScraperWorker()
    try:
        return worker.scrape_website(website_id, job_id)
    finally:
        worker.cleanup()


# Worker entry point for RQ
if __name__ == '__main__':
    import sys
    from rq import Worker, Queue, Connection
    from hoistscraper.queue import redis_conn
    
    # Start RQ worker
    with Connection(redis_conn):
        worker = Worker(Queue('scraper'))
        worker.work()