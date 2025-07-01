"""Optimized worker with async operations and batch processing."""
import os
import json
import asyncio
import aiohttp
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import stealth_async
from sqlmodel import Session, select
import time

from hoistscraper.db_optimized import engine, BulkOperations, get_db_session
from hoistscraper.models_optimized import Website, ScrapeJob, JobStatus, Opportunity
from hoistscraper.logging_config import get_logger, log_performance

logger = get_logger(__name__)

# Configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
CONCURRENT_PAGES = int(os.getenv("CONCURRENT_PAGES", "5"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

class OptimizedScraperWorker:
    """High-performance scraper with async operations and batching."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self._ollama_available: Optional[bool] = None
        self._ollama_session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(CONCURRENT_PAGES)
    
    @asynccontextmanager
    async def get_ollama_session(self):
        """Get or create aiohttp session for Ollama."""
        if self._ollama_session is None:
            self._ollama_session = aiohttp.ClientSession()
        try:
            yield self._ollama_session
        except Exception as e:
            logger.error(f"Ollama session error: {e}")
            raise
    
    async def check_ollama_availability(self) -> bool:
        """Async check for Ollama availability with caching."""
        if self._ollama_available is not None:
            return self._ollama_available
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        start_time = time.time()
        
        try:
            async with self.get_ollama_session() as session:
                async with session.get(f"{ollama_host}/api/tags", timeout=5.0) as response:
                    self._ollama_available = response.status == 200
                    duration = time.time() - start_time
                    log_performance(logger, "ollama_check", duration, 
                                  status="available" if self._ollama_available else "unavailable")
                    return self._ollama_available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._ollama_available = False
            return False
    
    async def initialize_browser(self):
        """Initialize browser with performance optimizations."""
        if not self.playwright:
            logger.info("Initializing optimized browser")
            start_time = time.time()
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-zygote',
                    '--single-process',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            duration = time.time() - start_time
            log_performance(logger, "browser_init", duration)
    
    async def cleanup(self):
        """Clean up resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self._ollama_session:
            await self._ollama_session.close()
    
    async def scrape_page_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple pages concurrently with rate limiting."""
        results = []
        
        async def scrape_single(url: str) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    context = await self.browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                    page = await context.new_page()
                    await stealth_async(page)
                    
                    start_time = time.time()
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # Extract content
                    content = await page.content()
                    title = await page.title()
                    
                    # Take screenshot for debugging
                    screenshot = await page.screenshot(full_page=True)
                    
                    duration = time.time() - start_time
                    log_performance(logger, "page_scrape", duration, url=url)
                    
                    await context.close()
                    await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting
                    
                    return {
                        'url': url,
                        'title': title,
                        'content': content,
                        'screenshot': screenshot,
                        'success': True,
                        'duration': duration
                    }
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    return {
                        'url': url,
                        'success': False,
                        'error': str(e)
                    }
        
        # Scrape pages concurrently
        tasks = [scrape_single(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def extract_opportunities_batch(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract opportunities from multiple pages using Ollama or fallback."""
        opportunities = []
        
        if await self.check_ollama_availability():
            # Use Ollama for extraction
            for page in pages:
                if page.get('success'):
                    extracted = await self.extract_with_ollama(page['content'])
                    opportunities.extend(extracted)
        else:
            # Fallback extraction
            for page in pages:
                if page.get('success'):
                    extracted = self.fallback_extraction(page['content'])
                    opportunities.extend(extracted)
        
        return opportunities
    
    async def extract_with_ollama(self, content: str) -> List[Dict[str, Any]]:
        """Extract opportunities using Ollama (placeholder for actual implementation)."""
        # This would integrate with the actual Ollama extraction logic
        return []
    
    def fallback_extraction(self, content: str) -> List[Dict[str, Any]]:
        """Simple fallback extraction when Ollama is not available."""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(content, 'html.parser')
        opportunities = []
        
        # Find potential opportunity links
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip()
            href = link['href']
            
            # Simple heuristic for opportunity detection
            keywords = ['grant', 'funding', 'tender', 'rfp', 'proposal', 'opportunity']
            if any(keyword in text.lower() for keyword in keywords):
                opportunities.append({
                    'title': text[:200],
                    'url': href,
                    'description': text
                })
        
        return opportunities
    
    async def process_job_optimized(self, job_id: int, website_id: int):
        """Process a scraping job with optimizations."""
        start_time = time.time()
        
        with get_db_session() as session:
            # Update job status
            job = session.get(ScrapeJob, job_id)
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(UTC)
            session.commit()
            
            try:
                # Get website
                website = session.get(Website, website_id)
                if not website:
                    raise ValueError(f"Website {website_id} not found")
                
                # Initialize browser if needed
                if not self.browser:
                    await self.initialize_browser()
                
                # Scrape main page
                main_results = await self.scrape_page_batch([website.url])
                
                if not main_results[0]['success']:
                    raise Exception(f"Failed to scrape main page: {main_results[0].get('error')}")
                
                # Extract opportunity links from main page
                opportunity_links = self.fallback_extraction(main_results[0]['content'])
                
                # Batch scrape opportunity pages
                all_opportunities = []
                for i in range(0, len(opportunity_links), BATCH_SIZE):
                    batch_links = [opp['url'] for opp in opportunity_links[i:i+BATCH_SIZE]]
                    batch_results = await self.scrape_page_batch(batch_links)
                    
                    # Extract from batch
                    extracted = await self.extract_opportunities_batch(batch_results)
                    
                    # Create opportunity objects
                    opportunity_objects = []
                    for opp in extracted:
                        opportunity_objects.append(Opportunity(
                            title=opp.get('title', 'Unknown')[:500],
                            description=opp.get('description'),
                            funding_amount=opp.get('funding_amount'),
                            deadline=opp.get('deadline'),
                            eligibility=opp.get('eligibility'),
                            application_url=opp.get('url'),
                            source_url=website.url,
                            website_id=website_id,
                            scrape_job_id=job_id
                        ))
                    
                    # Bulk insert opportunities
                    if opportunity_objects:
                        BulkOperations.bulk_insert(session, opportunity_objects)
                        all_opportunities.extend(opportunity_objects)
                
                # Update job as completed
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(UTC)
                job.raw_data = json.dumps({
                    'opportunities_found': len(all_opportunities),
                    'duration': time.time() - start_time
                })
                session.commit()
                
                duration = time.time() - start_time
                log_performance(logger, "job_processing", duration, 
                              opportunities=len(all_opportunities))
                
                logger.info(f"Job {job_id} completed: {len(all_opportunities)} opportunities found in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.now(UTC)
                session.commit()
                raise


# Worker entry point
async def run_worker():
    """Run the optimized worker."""
    worker = OptimizedScraperWorker()
    
    try:
        # Example: process a job
        await worker.process_job_optimized(job_id=1, website_id=1)
    finally:
        await worker.cleanup()

if __name__ == "__main__":
    asyncio.run(run_worker())