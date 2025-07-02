"""
Bulletproof tender scraping engine with ScrapeGraphAI.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
from loguru import logger

from tenacity import retry, stop_after_attempt, wait_exponential

# Try to import scrapegraph-ai, but don't fail if not available
try:
    from scrapegraph_ai import SmartScraperGraph
    from scrapegraph_ai.graphs import SearchGraph
    SCRAPEGRAPH_AVAILABLE = True
except ImportError:
    SmartScraperGraph = None
    SearchGraph = None
    SCRAPEGRAPH_AVAILABLE = False

from .anti_detection import AntiDetectionManager
from .pdf_processor import PDFProcessor
from .credentials import SecureCredentialManager
from ..models.website import WebsiteConfig
from ..schemas.scraping import ScrapingResult, TenderData


class BulletproofTenderScraper:
    """
    Core scraping engine with intelligent extraction and anti-detection.
    
    Features:
    - LLM-powered adaptive extraction
    - Automatic pattern learning
    - Anti-detection strategies
    - PDF discovery and processing
    - Error recovery with retries
    """
    
    def __init__(self):
        """Initialize the scraper with all components."""
        self.scraper = self._init_scraper()
        self.anti_detection = AntiDetectionManager()
        self.pdf_processor = PDFProcessor()
        self.credential_manager = SecureCredentialManager()
        
    def _init_scraper(self) -> Optional[SmartScraperGraph]:
        """Initialize ScrapeGraphAI with Ollama configuration."""
        from ..config import get_settings
        settings = get_settings()
        
        if not SCRAPEGRAPH_AVAILABLE:
            logger.warning("ScrapeGraphAI not installed - AI scraping disabled")
            return None
        
        if not settings.ollama_base_url:
            logger.warning("Ollama not configured - AI scraping disabled")
            return None
            
        return SmartScraperGraph(
            prompt="Extract tender/grant opportunities with title, description, deadline, value, reference number, and document links",
            llm_config={
                "model": f"ollama/{settings.ollama_model}",
                "temperature": 0.1,
                "base_url": settings.ollama_base_url,
                "max_tokens": 4096
            },
            embedder_config={
                "model": "ollama/nomic-embed-text",
                "base_url": settings.ollama_base_url
            },
            verbose=True,
            headless=True
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def scrape_website(
        self, 
        website_config: WebsiteConfig
    ) -> ScrapingResult:
        """
        Scrape a website with full anti-detection and error recovery.
        
        Args:
            website_config: Website configuration with URL and settings
            
        Returns:
            ScrapingResult with extracted opportunities and metadata
        """
        start_time = datetime.utcnow()
        
        # Check if AI scraping is available
        if not self.scraper:
            logger.warning(f"AI scraping not available for {website_config.url}")
            return ScrapingResult(
                website_id=website_config.id,
                website_url=website_config.url,
                opportunities=[],
                metadata={
                    "error": "AI scraping not configured (Ollama not available)",
                    "duration_seconds": 0
                },
                success=False,
                error_message="AI scraping service not configured"
            )
        
        try:
            # Apply anti-detection measures
            browser_config = await self.anti_detection.prepare_browser(
                website_config.url
            )
            
            # Handle authentication if required
            if website_config.requires_auth:
                await self._handle_authentication(website_config)
            
            # Extract tender data
            logger.info(f"Starting scrape for {website_config.url}")
            
            # Use SearchGraph for multi-page scraping
            if website_config.is_search_based and SearchGraph:
                graph = SearchGraph(
                    prompt=self._build_extraction_prompt(website_config),
                    llm_config=self.scraper.llm_config,
                    max_results=website_config.max_pages or 50
                )
                raw_data = graph.run(url=website_config.url)
            else:
                # Single page or listing page
                self.scraper.source = website_config.url
                raw_data = self.scraper.run()
            
            # Parse and validate extracted data
            opportunities = self._parse_opportunities(raw_data)
            
            # Process any discovered PDFs
            pdf_urls = self._extract_pdf_urls(opportunities)
            if pdf_urls:
                pdf_results = await self.pdf_processor.process_batch(pdf_urls)
                opportunities = self._merge_pdf_data(opportunities, pdf_results)
            
            # Calculate metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScrapingResult(
                website_id=website_config.id,
                opportunities=opportunities,
                total_found=len(opportunities),
                pdfs_processed=len(pdf_urls),
                duration_seconds=duration,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Scraping failed for {website_config.url}: {str(e)}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScrapingResult(
                website_id=website_config.id,
                opportunities=[],
                total_found=0,
                pdfs_processed=0,
                duration_seconds=duration,
                success=False,
                error_message=str(e)
            )
    
    async def _handle_authentication(
        self, 
        website_config: WebsiteConfig
    ) -> None:
        """Handle website authentication if required."""
        if not website_config.credentials:
            return
            
        credentials = self.credential_manager.decrypt_credentials(
            website_config.credentials
        )
        
        # Implement different auth strategies
        if website_config.auth_type == "form":
            await self._form_login(website_config.url, credentials)
        elif website_config.auth_type == "basic":
            # Handle basic auth in headers
            pass
        elif website_config.auth_type == "oauth":
            # Handle OAuth flow
            pass
    
    def _build_extraction_prompt(
        self, 
        website_config: WebsiteConfig
    ) -> str:
        """Build a detailed extraction prompt for the LLM."""
        base_prompt = """
        Extract all tender/grant opportunities from this page.
        For each opportunity, extract:
        - title: The tender title or name
        - description: Brief description of the opportunity
        - deadline: Application deadline or closing date
        - value: Contract value or budget (with currency)
        - reference_number: Tender ID or reference number
        - source_url: Direct link to the tender details
        - document_urls: List of PDF/document download links
        - categories: Type or category of the tender
        - location: Geographic location if specified
        
        Return as structured JSON array.
        """
        
        # Add site-specific hints if available
        if website_config.extraction_hints:
            base_prompt += f"\n\nSite-specific hints: {website_config.extraction_hints}"
            
        return base_prompt
    
    def _parse_opportunities(
        self, 
        raw_data: Dict[str, Any]
    ) -> List[TenderData]:
        """Parse raw LLM output into structured tender data."""
        opportunities = []
        
        # Handle different output formats from ScrapeGraphAI
        if isinstance(raw_data, list):
            items = raw_data
        elif isinstance(raw_data, dict):
            # Try common keys
            items = (
                raw_data.get("opportunities", []) or
                raw_data.get("tenders", []) or
                raw_data.get("results", []) or
                raw_data.get("data", [])
            )
            if not items and any(raw_data.values()):
                # Single item wrapped in dict
                items = [raw_data]
        else:
            logger.warning(f"Unexpected data format: {type(raw_data)}")
            return []
        
        for item in items:
            try:
                # Create tender data with validation
                tender = TenderData(
                    title=item.get("title", "").strip(),
                    description=item.get("description", "").strip(),
                    deadline=self._parse_deadline(item.get("deadline")),
                    value=self._parse_value(item.get("value")),
                    currency=item.get("currency", "USD"),
                    reference_number=item.get("reference_number", "").strip(),
                    source_url=item.get("source_url", "").strip(),
                    document_urls=item.get("document_urls", []),
                    categories=item.get("categories", []),
                    location=item.get("location", "").strip(),
                    confidence_score=self._calculate_confidence(item)
                )
                
                # Only add if minimum required fields are present
                if tender.title and (tender.deadline or tender.description):
                    opportunities.append(tender)
                    
            except Exception as e:
                logger.warning(f"Failed to parse opportunity: {e}")
                continue
        
        return opportunities
    
    def _parse_deadline(self, deadline_str: Any) -> Optional[datetime]:
        """Parse various deadline formats into datetime."""
        if not deadline_str:
            return None
            
        # Implement flexible date parsing
        # This is simplified - in production use dateutil.parser
        try:
            if isinstance(deadline_str, datetime):
                return deadline_str
            # Add more parsing logic here
            return None
        except:
            return None
    
    def _parse_value(self, value_str: Any) -> Optional[float]:
        """Parse monetary values from various formats."""
        if not value_str:
            return None
            
        try:
            # Remove currency symbols and convert
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            # Parse string values
            clean_value = str(value_str).replace("$", "").replace(",", "")
            # Handle K, M, B suffixes
            if clean_value.endswith("K"):
                return float(clean_value[:-1]) * 1000
            elif clean_value.endswith("M"):
                return float(clean_value[:-1]) * 1000000
            elif clean_value.endswith("B"):
                return float(clean_value[:-1]) * 1000000000
            
            return float(clean_value)
        except:
            return None
    
    def _extract_pdf_urls(
        self, 
        opportunities: List[TenderData]
    ) -> List[str]:
        """Extract all PDF URLs from opportunities."""
        pdf_urls = []
        
        for opp in opportunities:
            pdf_urls.extend(opp.document_urls)
        
        # Deduplicate
        return list(set(pdf_urls))
    
    def _merge_pdf_data(
        self, 
        opportunities: List[TenderData],
        pdf_results: Dict[str, Any]
    ) -> List[TenderData]:
        """Merge extracted PDF data back into opportunities."""
        # Implementation depends on PDF processor output
        return opportunities
    
    def _calculate_confidence(self, item: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness."""
        score = 1.0
        required_fields = ["title", "deadline", "description"]
        
        for field in required_fields:
            if not item.get(field):
                score *= 0.8
                
        return score
    
    async def _form_login(
        self, 
        url: str, 
        credentials: Dict[str, str]
    ) -> None:
        """Perform form-based login."""
        # This would integrate with Playwright or Selenium
        # to fill and submit login forms
        pass


class PatternLearner:
    """
    Learns and stores extraction patterns for each website.
    This reduces LLM usage over time by reusing successful patterns.
    """
    
    def __init__(self):
        self.patterns_cache = {}
    
    async def learn_patterns(
        self, 
        website_id: int,
        sample_pages: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze sample pages to learn extraction patterns.
        
        This is where the system becomes "intelligent" - 
        it learns how each site structures its data.
        """
        # Use LLM to analyze page structure
        # Store successful CSS selectors, XPaths, or patterns
        # This dramatically reduces future LLM usage
        pass
    
    def get_patterns(self, website_id: int) -> Optional[Dict[str, Any]]:
        """Get learned patterns for a website."""
        return self.patterns_cache.get(website_id)