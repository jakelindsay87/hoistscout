"""Enhanced background worker for scraping jobs with Ollama integration."""
import os
import json
import logging
import asyncio
import base64
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import stealth_async
from sqlmodel import Session
import time
import uuid

from hoistscraper.db import engine
from hoistscraper.models import Website, ScrapeJob, JobStatus, Opportunity
from hoistscraper.extractor.ollama_extractor import (
    extract_opportunities_from_listing_with_ollama,
    extract_opportunity_with_ollama
)
from hoistscraper.logging_config import get_logger, log_performance, log_security_event

logger = get_logger(__name__)

# Data directory for storing scraped content
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))


class EnhancedScraperWorker:
    """Enhanced scraper worker with Ollama integration."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.ollama_available = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama service is available."""
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        start_time = time.time()
        try:
            import httpx
            response = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
            duration = time.time() - start_time
            log_performance(logger, "ollama_availability_check", duration, status="available")
            logger.info(f"Ollama service available at {ollama_host}")
            return response.status_code == 200
        except Exception as e:
            duration = time.time() - start_time
            log_performance(logger, "ollama_availability_check", duration, status="unavailable")
            logger.warning(f"Ollama service not available at {ollama_host}: {str(e)}, using fallback extraction")
            return False
    
    async def initialize_browser(self):
        """Initialize Playwright browser."""
        if not self.playwright:
            logger.info("Initializing Playwright browser")
            start_time = time.time()
            self.playwright = await async_playwright().start()
            duration = time.time() - start_time
            log_performance(logger, "playwright_initialization", duration)
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def scrape_website(self, website_id: int, job_id: int) -> Dict[str, Any]:
        """
        Scrape a website and extract opportunities.
        
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
            
            # Generate correlation ID for this scrape
            correlation_id = str(uuid.uuid4())
            logger.info(f"Starting scrape for website {website.name} (ID: {website_id})", 
                       extra={'extra_fields': {'correlation_id': correlation_id, 'job_id': job_id}})
            
            try:
                # Initialize browser if needed
                await self.initialize_browser()
                
                # Create a new page
                page = await self.browser.new_page()
                await stealth_async(page)
                logger.debug(f"Created new browser page with stealth mode")
                
                # Check if website requires authentication
                if hasattr(website, 'requires_auth') and website.requires_auth:
                    log_security_event(logger, "authentication_attempt", 
                                     website_id=website_id, 
                                     correlation_id=correlation_id)
                    await self._handle_login(page, website)
                
                # Navigate to the website
                logger.info(f"Navigating to {website.url}")
                nav_start = time.time()
                await page.goto(website.url, wait_until='networkidle', timeout=30000)
                nav_duration = time.time() - nav_start
                log_performance(logger, "page_navigation", nav_duration, 
                              url=website.url, correlation_id=correlation_id)
                
                # Wait for content to load
                await page.wait_for_load_state('domcontentloaded')
                
                # Get the HTML content
                html_content = await page.content()
                current_url = page.url
                
                # Save raw HTML
                DATA_DIR.mkdir(exist_ok=True)
                html_path = DATA_DIR / f"job_{job_id}_listing.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Extract opportunities
                opportunities_found = []
                
                extraction_start = time.time()
                if self.ollama_available:
                    # Use Ollama to identify opportunity links
                    logger.info("Extracting opportunities with Ollama")
                    opportunity_links = await extract_opportunities_from_listing_with_ollama(
                        html_content, current_url
                    )
                    extraction_method = "ollama"
                else:
                    # Fallback to basic extraction
                    logger.info("Using fallback extraction (Ollama not available)")
                    opportunity_links = self._extract_links_basic(html_content, current_url)
                    extraction_method = "fallback"
                
                extraction_duration = time.time() - extraction_start
                log_performance(logger, "opportunity_extraction", extraction_duration,
                              method=extraction_method,
                              opportunities_count=len(opportunity_links),
                              correlation_id=correlation_id)
                
                logger.info(f"Found {len(opportunity_links)} potential opportunities")
                
                # Process each opportunity link
                opportunities_limit = int(os.getenv('OPPORTUNITIES_LIMIT', '10'))
                logger.info(f"Processing up to {opportunities_limit} opportunities")
                
                for idx, link_info in enumerate(opportunity_links[:opportunities_limit]):
                    opp_start = time.time()
                    try:
                        opportunity_url = link_info.get('url')
                        logger.info(f"Processing opportunity {idx+1}/{len(opportunity_links[:opportunities_limit])}: {opportunity_url}")
                        
                        # Navigate to opportunity detail page
                        detail_nav_start = time.time()
                        await page.goto(opportunity_url, wait_until='networkidle', timeout=30000)
                        detail_nav_duration = time.time() - detail_nav_start
                        log_performance(logger, "opportunity_page_navigation", detail_nav_duration,
                                      opportunity_index=idx+1,
                                      url=opportunity_url)
                        
                        detail_html = await page.content()
                        
                        # Save detail page HTML
                        detail_path = DATA_DIR / f"job_{job_id}_detail_{idx+1}.html"
                        with open(detail_path, 'w', encoding='utf-8') as f:
                            f.write(detail_html)
                        
                        # Extract opportunity details
                        if self.ollama_available:
                            opportunity_data = await extract_opportunity_with_ollama(
                                detail_html, opportunity_url
                            )
                        else:
                            opportunity_data = self._extract_opportunity_basic(
                                detail_html, opportunity_url
                            )
                        
                        # Create opportunity record
                        opportunity = Opportunity(
                            title=opportunity_data.get('title', 'Unknown Opportunity'),
                            description=opportunity_data.get('description'),
                            source_url=opportunity_url,
                            website_id=website_id,
                            job_id=job_id,
                            deadline=self._parse_deadline(opportunity_data.get('deadline')),
                            amount=opportunity_data.get('amount')
                        )
                        session.add(opportunity)
                        opportunities_found.append(opportunity_data)
                        
                        # Log opportunity processing performance
                        opp_duration = time.time() - opp_start
                        log_performance(logger, "opportunity_processing", opp_duration,
                                      opportunity_index=idx+1,
                                      success=True)
                        
                        # Rate limiting
                        rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '2'))
                        logger.debug(f"Rate limiting: waiting {rate_limit_delay} seconds")
                        await asyncio.sleep(rate_limit_delay)
                        
                    except Exception as e:
                        opp_duration = time.time() - opp_start
                        log_performance(logger, "opportunity_processing", opp_duration,
                                      opportunity_index=idx+1,
                                      success=False)
                        logger.error(f"Failed to process opportunity {opportunity_url}: {str(e)}",
                                   exc_info=True,
                                   extra={'extra_fields': {'correlation_id': correlation_id}})
                        continue
                
                # Commit all opportunities
                session.commit()
                
                # Save summary
                summary_path = DATA_DIR / f"job_{job_id}_summary.json"
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "website_id": website_id,
                        "url": website.url,
                        "scraped_at": datetime.now(UTC).isoformat(),
                        "opportunities_found": len(opportunities_found),
                        "extraction_method": "ollama" if self.ollama_available else "basic",
                        "opportunities": opportunities_found
                    }, f, indent=2)
                
                # Update job status to completed
                if job:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now(UTC)
                    job.raw_data = str(summary_path)
                    session.commit()
                
                logger.info(f"Successfully scraped {website.url} - found {len(opportunities_found)} opportunities")
                await page.close()
                
                return {
                    "status": "success",
                    "opportunities_found": len(opportunities_found),
                    "summary_path": str(summary_path)
                }
                
            except Exception as e:
                logger.error(f"Error scraping {website.url}: {str(e)}")
                
                # Update job status to failed
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now(UTC)
                    job.error_message = str(e)
                    session.commit()
                
                raise
    
    async def _handle_login(self, page: Page, website: Website):
        """Handle website authentication if required."""
        from hoistscraper.auth import get_website_credentials
        
        with Session(engine) as session:
            creds = get_website_credentials(session, website.id)
            
            if not creds:
                logger.warning(f"No credentials found for website {website.id}")
                return
            
            username, password, additional_data = creds
            auth_type = additional_data.get('auth_type', 'basic')
            
            logger.info(f"Attempting {auth_type} authentication for {website.url}")
            
            if auth_type == 'basic':
                # Basic HTTP authentication
                await page.set_extra_http_headers({
                    'Authorization': f'Basic {base64.b64encode(f"{username}:{password}".encode()).decode()}'
                })
            
            elif auth_type == 'form':
                # Form-based authentication
                login_url = additional_data.get('login_url', website.url + '/login')
                username_field = additional_data.get('username_field', 'username')
                password_field = additional_data.get('password_field', 'password')
                submit_button = additional_data.get('submit_button', 'button[type="submit"]')
                
                # Navigate to login page
                await page.goto(login_url, wait_until='networkidle')
                
                # Fill in credentials
                await page.fill(f'input[name="{username_field}"]', username)
                await page.fill(f'input[name="{password_field}"]', password)
                
                # Submit form
                await page.click(submit_button)
                
                # Wait for navigation or specific element
                await page.wait_for_load_state('networkidle')
                
                # Check if login was successful
                success_indicator = additional_data.get('success_indicator')
                if success_indicator:
                    try:
                        await page.wait_for_selector(success_indicator, timeout=5000)
                        logger.info("Form authentication successful")
                    except:
                        logger.error("Form authentication failed - success indicator not found")
                        from hoistscraper.auth import credential_manager
                        credential_manager.mark_invalid(session, website.id)
            
            elif auth_type == 'cookie':
                # Cookie-based authentication
                cookies = additional_data.get('cookies', [])
                for cookie in cookies:
                    await page.context.add_cookies([cookie])
                logger.info("Added authentication cookies")
            
            else:
                logger.warning(f"Unsupported auth type: {auth_type}")
    
    def _extract_links_basic(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Basic link extraction without Ollama."""
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Look for links with common tender/grant keywords
        keywords = ['tender', 'grant', 'opportunity', 'ATM', 'RFT', 'EOI', 'procurement']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            if any(keyword in text.lower() or keyword in href.lower() for keyword in keywords):
                absolute_url = urljoin(base_url, href)
                links.append({
                    'url': absolute_url,
                    'title': text,
                    'source_page': base_url
                })
        
        return links[:20]  # Limit to first 20
    
    def _extract_opportunity_basic(self, html: str, url: str) -> Dict[str, Any]:
        """Basic opportunity extraction without Ollama."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = None
        for tag in ['h1', 'h2', 'h3']:
            element = soup.find(tag)
            if element:
                title = element.get_text(strip=True)
                break
        
        # Extract description
        paragraphs = soup.find_all('p', limit=5)
        description = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return {
            'title': title or 'Unknown Opportunity',
            'description': description[:1000] if description else None,
            'source_url': url,
            'extraction_method': 'basic'
        }
    
    def _parse_deadline(self, deadline_str: Optional[str]) -> Optional[datetime]:
        """Parse deadline string to datetime."""
        if not deadline_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        except:
            # Try other common formats
            from dateutil import parser
            try:
                return parser.parse(deadline_str)
            except:
                return None


async def scrape_website_job_v2(website_id: int, job_id: int) -> Dict[str, Any]:
    """
    Enhanced RQ job function for scraping a website.
    
    This is the function that will be enqueued to RQ.
    """
    # Convert to sync for RQ compatibility
    worker = EnhancedScraperWorker()
    try:
        # Run async function in sync context
        return asyncio.run(worker.scrape_website(website_id, job_id))
    finally:
        asyncio.run(worker.cleanup())


# Worker entry point for RQ
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode - run a single scrape
        website_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        job_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        result = asyncio.run(scrape_website_job_v2(website_id, job_id))
        print(f"Test scrape completed: {result}")
    else:
        # Normal RQ worker mode
        from rq import Worker, Queue, Connection
        from hoistscraper.queue import redis_conn
        
        # Start RQ worker
        with Connection(redis_conn):
            worker = Worker(Queue('scraper'))
            worker.work()