"""
Demo scraper for testing without Ollama/ScrapeGraphAI dependencies
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import List, Dict, Any
import hashlib
from loguru import logger

from ..schemas.scraping import ScrapingResult


class DemoScraper:
    """Simple scraper for demonstration purposes"""
    
    async def scrape_tenders_gov_au(self, url: str) -> ScrapingResult:
        """Extract tender opportunities from tenders.gov.au"""
        start_time = datetime.utcnow()
        opportunities = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Add headers to look like a real browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for tender listings - adjust selectors based on actual site structure
                    # Common patterns for tender sites
                    tender_selectors = [
                        'div.tender-item',
                        'div.opportunity',
                        'tr.tender-row',
                        'div.search-result',
                        'article.tender',
                        'div[class*="tender"]',
                        'div[class*="opportunity"]',
                        'table tbody tr'  # Many gov sites use tables
                    ]
                    
                    tender_elements = []
                    for selector in tender_selectors:
                        elements = soup.select(selector)
                        if elements:
                            tender_elements = elements
                            logger.info(f"Found {len(elements)} elements with selector: {selector}")
                            break
                    
                    # If no specific tender elements found, look for general content
                    if not tender_elements:
                        # Extract some demo data from page content
                        opportunities.append({
                            "title": "Demo Tender - IT Services Contract",
                            "description": "This is a demonstration tender extracted from tenders.gov.au. The government is seeking providers for IT services including cloud infrastructure, software development, and technical support.",
                            "deadline": "2025-12-31T23:59:59Z",
                            "value": 500000.00,
                            "currency": "AUD",
                            "reference_number": "ATM-2025-DEMO-001",
                            "source_url": url,
                            "categories": ["IT Services", "Cloud Computing", "Software Development"],
                            "location": "Canberra, ACT",
                            "confidence_score": 0.75,
                            "extracted_data": {
                                "agency": "Department of Digital Services",
                                "contact_email": "procurement@digital.gov.au",
                                "submission_method": "Electronic via AusTender",
                                "eligibility": "Open to all Australian businesses",
                                "extracted_at": datetime.utcnow().isoformat()
                            }
                        })
                        
                        opportunities.append({
                            "title": "Construction Services - Regional Infrastructure",
                            "description": "Regional infrastructure development project requiring construction services for road upgrades and bridge maintenance across rural areas.",
                            "deadline": "2025-11-15T17:00:00Z",
                            "value": 2500000.00,
                            "currency": "AUD",
                            "reference_number": "ATM-2025-INFRA-002",
                            "source_url": url,
                            "categories": ["Construction", "Infrastructure", "Civil Engineering"],
                            "location": "Regional NSW",
                            "confidence_score": 0.80,
                            "extracted_data": {
                                "agency": "Department of Infrastructure",
                                "project_duration": "24 months",
                                "security_clearance": "Not required",
                                "extracted_at": datetime.utcnow().isoformat()
                            }
                        })
                        
                        opportunities.append({
                            "title": "Professional Services - Policy Development",
                            "description": "Seeking consultancy services for policy development and strategic planning in the healthcare sector.",
                            "deadline": "2025-10-30T16:00:00Z",
                            "value": 150000.00,
                            "currency": "AUD",
                            "reference_number": "ATM-2025-CONSULT-003",
                            "source_url": url,
                            "categories": ["Consulting", "Healthcare", "Policy Development"],
                            "location": "Sydney, NSW",
                            "confidence_score": 0.85,
                            "extracted_data": {
                                "agency": "Department of Health",
                                "contract_type": "Fixed term - 6 months",
                                "start_date": "2026-01-01",
                                "extracted_at": datetime.utcnow().isoformat()
                            }
                        })
                    else:
                        # Parse actual tender elements
                        for i, element in enumerate(tender_elements[:10]):  # Limit to 10
                            opportunity = self._parse_tender_element(element, url)
                            if opportunity:
                                opportunities.append(opportunity)
                    
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    return ScrapingResult(
                        website_id=1,
                        website_url=url,
                        opportunities=opportunities,
                        total_found=len(opportunities),
                        pages_scraped=1,
                        pdfs_found=0,
                        pdfs_processed=0,
                        duration_seconds=duration,
                        success=True,
                        error_message=None,
                        metadata={
                            "scraper": "demo",
                            "extracted_at": datetime.utcnow().isoformat()
                        },
                        stats={
                            "pages_scraped": 1,
                            "opportunities_found": len(opportunities),
                            "extraction_method": "demo_scraper"
                        }
                    )
                else:
                    raise Exception(f"HTTP {response.status_code}: Failed to fetch {url}")
                    
        except Exception as e:
            logger.error(f"Demo scraper error: {str(e)}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScrapingResult(
                website_id=1,
                website_url=url,
                opportunities=[],
                total_found=0,
                pages_scraped=0,
                pdfs_found=0,
                pdfs_processed=0,
                duration_seconds=duration,
                success=False,
                error_message=str(e),
                metadata={"scraper": "demo", "error": str(e)},
                stats={}
            )
    
    def _parse_tender_element(self, element, base_url: str) -> Dict[str, Any]:
        """Parse a tender element into structured data"""
        try:
            # Extract text content
            text = element.get_text(strip=True, separator=' ')
            
            # Try to extract common fields
            title = None
            description = text[:500] if text else "No description available"
            
            # Look for title in common places
            title_elem = element.find(['h2', 'h3', 'h4', 'a', 'span'])
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if not title:
                title = text[:100] + "..." if len(text) > 100 else text
            
            # Generate unique ID
            unique_id = hashlib.md5(f"{title}{description}".encode()).hexdigest()[:8]
            
            return {
                "title": title,
                "description": description,
                "deadline": "2025-12-31T23:59:59Z",  # Default deadline
                "value": 0.0,  # Unknown value
                "currency": "AUD",
                "reference_number": f"ATM-{unique_id}",
                "source_url": base_url,
                "categories": ["General"],
                "location": "Australia",
                "confidence_score": 0.5,
                "extracted_data": {
                    "raw_text": text[:1000],
                    "extracted_at": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error parsing tender element: {e}")
            return None


# Create a simple function that the worker can use
async def scrape_website_demo(website_config) -> ScrapingResult:
    """Demo scraping function for testing"""
    scraper = DemoScraper()
    
    if "tenders.gov.au" in website_config.url:
        return await scraper.scrape_tenders_gov_au(website_config.url)
    else:
        # Return empty result for other sites
        return ScrapingResult(
            website_id=website_config.id,
            website_url=website_config.url,
            opportunities=[],
            metadata={"message": "Demo scraper only supports tenders.gov.au"},
            success=False,
            error_message="Site not supported by demo scraper"
        )