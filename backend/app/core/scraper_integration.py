"""
Integration layer to ensure all scraping components work together
according to the PRD architecture.
"""
import os
from typing import Optional, Dict, Any, List
from loguru import logger

from .scraper import BulletproofTenderScraper, SCRAPEGRAPH_AVAILABLE
from .scraper_with_ollama import OllamaScraper
from .demo_scraper import DemoScraper
from .anti_detection import AntiDetectionManager
from .pdf_processor import PDFProcessor
from ..schemas.scraping import ScrapingResult
from ..config import get_settings


class ScraperFactory:
    """
    Factory to create the appropriate scraper based on available services.
    Ensures PRD architecture is maintained with proper fallbacks.
    """
    
    @staticmethod
    async def create_scraper() -> Any:
        """
        Create scraper instance with this priority:
        1. BulletproofTenderScraper (with ScrapeGraphAI) - Full PRD implementation
        2. OllamaScraper - Direct LLM extraction without ScrapeGraphAI
        3. DemoScraper - Fallback for testing
        """
        settings = get_settings()
        
        # First, try the full BulletproofTenderScraper
        if SCRAPEGRAPH_AVAILABLE and settings.ollama_base_url:
            logger.info("Initializing BulletproofTenderScraper with ScrapeGraphAI")
            return BulletproofTenderScraper()
        
        # Second, try direct Ollama integration
        if settings.ollama_base_url:
            logger.info("ScrapeGraphAI not available, using OllamaScraper")
            return OllamaScraper(
                ollama_base_url=settings.ollama_base_url,
                model=settings.ollama_model
            )
        
        # Last resort - demo scraper
        logger.warning("No LLM service available, using DemoScraper")
        return DemoScraper()


class IntegratedScrapingPipeline:
    """
    Complete scraping pipeline that integrates all PRD components:
    - Anti-detection (Cloudflare bypass, CAPTCHA solving, proxy rotation)
    - LLM-driven extraction (ScrapeGraphAI or Ollama)
    - PDF processing
    - Credential management
    """
    
    def __init__(self):
        self.anti_detection = AntiDetectionManager()
        self.pdf_processor = PDFProcessor()
        self.settings = get_settings()
        
    async def scrape_with_full_pipeline(self, website_config) -> ScrapingResult:
        """
        Execute complete scraping pipeline as per PRD.
        """
        logger.info(f"Starting integrated scraping pipeline for {website_config.url}")
        
        # Step 1: Check if Cloudflare protection is present
        if await self._needs_cloudflare_bypass(website_config.url):
            logger.info("Cloudflare detected, attempting bypass...")
            bypass_result = await self.anti_detection.handle_cloudflare(website_config.url)
            if bypass_result:
                # Use bypassed content
                website_config.cookies = bypass_result.get("cookies")
                website_config.user_agent = bypass_result.get("user_agent")
        
        # Step 2: Create appropriate scraper
        scraper = await ScraperFactory.create_scraper()
        
        # Step 3: Execute scraping with anti-detection
        try:
            result = await scraper.scrape_website(website_config)
            
            # Step 4: Process any discovered PDFs
            if hasattr(result, 'pdf_urls') and result.pdf_urls:
                logger.info(f"Processing {len(result.pdf_urls)} PDFs...")
                pdf_results = await self.pdf_processor.process_batch(result.pdf_urls)
                
                # Merge PDF extracted data into opportunities
                result = self._merge_pdf_data(result, pdf_results)
            
            return result
            
        except Exception as e:
            logger.error(f"Scraping pipeline failed: {e}")
            return ScrapingResult(
                website_id=website_config.id,
                website_url=website_config.url,
                opportunities=[],
                success=False,
                error_message=str(e)
            )
    
    async def _needs_cloudflare_bypass(self, url: str) -> bool:
        """Check if URL needs Cloudflare bypass."""
        # Simple check - in production, actually test the URL
        cloudflare_indicators = [
            "Checking your browser",
            "Please wait",
            "DDoS protection by Cloudflare",
            "cf-browser-verification"
        ]
        
        # For now, check known problematic domains
        problematic_domains = ["tenders.vic.gov.au", "tenders.nsw.gov.au"]
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        return any(prob in domain for prob in problematic_domains)
    
    def _merge_pdf_data(self, result: ScrapingResult, pdf_results: Dict) -> ScrapingResult:
        """Merge PDF extracted data into opportunities."""
        for opportunity in result.opportunities:
            # Check if this opportunity has associated PDFs
            source_url = opportunity.get("source_url", "")
            
            for pdf_url, pdf_data in pdf_results.items():
                if pdf_url in source_url or source_url in pdf_url:
                    # Merge PDF data
                    if "extracted_data" not in opportunity:
                        opportunity["extracted_data"] = {}
                    
                    opportunity["extracted_data"]["pdf_content"] = pdf_data.extracted_text
                    opportunity["extracted_data"]["pdf_metadata"] = pdf_data.metadata
                    
                    # Update description with PDF content if better
                    if len(pdf_data.extracted_text) > len(opportunity.get("description", "")):
                        opportunity["description"] = pdf_data.extracted_text[:1000]
        
        return result


def get_service_status() -> Dict[str, Any]:
    """
    Check status of all required services for the scraping pipeline.
    """
    settings = get_settings()
    
    status = {
        "scrapegraph_ai": SCRAPEGRAPH_AVAILABLE,
        "ollama": bool(settings.ollama_base_url),
        "flaresolverr": bool(settings.flaresolverr_url),
        "minio": bool(settings.minio_endpoint),
        "2captcha": bool(os.getenv("TWO_CAPTCHA_API_KEY")),
        "proxies": False  # Check proxy configuration
    }
    
    # Determine scraper that will be used
    if status["scrapegraph_ai"] and status["ollama"]:
        status["active_scraper"] = "BulletproofTenderScraper (Full PRD)"
    elif status["ollama"]:
        status["active_scraper"] = "OllamaScraper (LLM only)"
    else:
        status["active_scraper"] = "DemoScraper (Fallback)"
    
    # Overall health
    critical_services = ["ollama"]  # At minimum need LLM
    status["healthy"] = all(status.get(svc, False) for svc in critical_services)
    
    return status