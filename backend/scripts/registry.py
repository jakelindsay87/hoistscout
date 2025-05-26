"""Registry system for managing site crawlers."""

import logging
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Browser

from hoistscraper.crawler import ConfigurableSiteCrawler, ConfigLoader
from hoistscraper.extractor import extract_opportunity, analyse_terms

logger = logging.getLogger(__name__)


class CrawlerRegistry:
    """Registry for managing and executing site crawlers."""
    
    def __init__(self, site_config: Dict[str, Any], proxy_pool: List[str] = None):
        """Initialize crawler registry with site configuration.
        
        Args:
            site_config: Site configuration dictionary
            proxy_pool: List of proxy server URLs
        """
        self.site_config = site_config
        self.proxy_pool = proxy_pool or []
        self.crawler: Optional[ConfigurableSiteCrawler] = None
        self.browser: Optional[Browser] = None
        
    async def setup(self):
        """Setup the crawler and browser instance."""
        try:
            # Load site configuration
            config = ConfigLoader.load_from_dict(self.site_config)
            self.crawler = ConfigurableSiteCrawler(config, self.proxy_pool)
            
            # Initialize browser
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Setup crawler with browser
            await self.crawler.setup(self.browser)
            
            logger.info(f"Initialized crawler for site: {config.name}")
            
        except Exception as e:
            logger.error(f"Failed to setup crawler for {self.site_config.get('name', 'unknown')}: {str(e)}")
            raise
    
    async def crawl(self) -> Dict[str, Any]:
        """Execute the crawling process for this site.
        
        Returns:
            Dictionary containing crawl results and extracted data
        """
        if not self.crawler:
            await self.setup()
        
        try:
            logger.info(f"Starting crawl for site: {self.site_config['name']}")
            
            # Execute crawling
            crawl_results = await self.crawler.crawl()
            
            # Process and extract data from crawled pages
            extracted_opportunities = []
            for page_data in crawl_results.get("pages", []):
                try:
                    # Extract opportunity data using LLM
                    opportunity = await extract_opportunity(
                        page_data["content"], 
                        page_data["url"]
                    )
                    
                    # Add metadata
                    opportunity["crawl_timestamp"] = page_data.get("timestamp")
                    opportunity["site_name"] = self.site_config["name"]
                    
                    extracted_opportunities.append(opportunity)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract opportunity from {page_data['url']}: {str(e)}")
                    extracted_opportunities.append({
                        "error": str(e),
                        "source_url": page_data["url"],
                        "site_name": self.site_config["name"]
                    })
            
            # Compile final results
            results = {
                "site": self.site_config["name"],
                "status": "completed",
                "crawl_summary": {
                    "total_pages": crawl_results.get("total_pages", 0),
                    "errors": crawl_results.get("errors", []),
                    "opportunities_found": len(extracted_opportunities)
                },
                "opportunities": extracted_opportunities,
                "raw_crawl_data": crawl_results
            }
            
            logger.info(f"Completed crawl for {self.site_config['name']}: "
                       f"{len(extracted_opportunities)} opportunities found")
            
            return results
            
        except Exception as e:
            logger.error(f"Crawl failed for {self.site_config['name']}: {str(e)}")
            return {
                "site": self.site_config["name"],
                "status": "failed",
                "error": str(e),
                "opportunities": []
            }
    
    async def analyze_terms(self, terms_url: str = None) -> Dict[str, Any]:
        """Analyze terms and conditions for the site.
        
        Args:
            terms_url: URL to terms page, if different from main site
            
        Returns:
            Dictionary containing terms analysis
        """
        if not self.crawler:
            await self.setup()
        
        try:
            # Use provided URL or try to find terms page
            target_url = terms_url or self._find_terms_url()
            
            if not target_url:
                return {
                    "error": "No terms URL provided or found",
                    "site": self.site_config["name"]
                }
            
            # Fetch terms page
            html_content = await self.crawler.fetch_html(target_url)
            
            # Extract text and analyze
            from hoistscraper.extractor.llm_extractor import extract_text_content
            text_content = await extract_text_content(html_content)
            
            # Analyze terms
            analysis = await analyse_terms(text_content)
            analysis["site"] = self.site_config["name"]
            analysis["terms_url"] = target_url
            
            return analysis
            
        except Exception as e:
            logger.error(f"Terms analysis failed for {self.site_config['name']}: {str(e)}")
            return {
                "error": str(e),
                "site": self.site_config["name"],
                "allows_commercial_use": False,  # Conservative default
                "forbids_scraping": True         # Conservative default
            }
    
    def _find_terms_url(self) -> Optional[str]:
        """Try to find terms and conditions URL for the site."""
        base_urls = self.site_config.get("start_urls", [])
        if not base_urls:
            return None
        
        base_url = base_urls[0]
        
        # Common terms page patterns
        terms_patterns = [
            "/terms",
            "/terms-of-service",
            "/terms-and-conditions",
            "/legal/terms",
            "/privacy-policy",
            "/legal"
        ]
        
        # Try to construct terms URL
        for pattern in terms_patterns:
            if base_url.endswith('/'):
                terms_url = base_url.rstrip('/') + pattern
            else:
                from urllib.parse import urljoin
                terms_url = urljoin(base_url, pattern)
            
            return terms_url  # Return first attempt for now
        
        return None
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.crawler:
                await self.crawler.cleanup()
            
            if self.browser:
                await self.browser.close()
                
        except Exception as e:
            logger.warning(f"Cleanup warning for {self.site_config.get('name', 'unknown')}: {str(e)}")


# Alias for backward compatibility with the script
Registry = CrawlerRegistry 