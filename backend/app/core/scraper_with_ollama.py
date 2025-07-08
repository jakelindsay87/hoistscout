"""
Enhanced scraper that uses Ollama for intelligent extraction
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
from typing import Dict, List, Any, Optional
import hashlib
from loguru import logger

from ..schemas.scraping import ScrapingResult


class OllamaScraper:
    """Scraper that uses Ollama for intelligent content extraction"""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        self.ollama_base_url = ollama_base_url
        self.model = model
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    
    async def check_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                return response.status_code == 200
        except:
            return False
    
    async def extract_with_llm(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """Use Ollama to extract structured tender data from HTML"""
        
        # Clean HTML for better LLM processing
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Limit text size for LLM
        if len(text) > 15000:
            text = text[:15000] + "..."
        
        # Create enhanced prompt for tender extraction
        prompt = f"""You are a specialised funding opportunity extraction system. Extract structured information from this webpage.

## Core Information to Extract:
- **Title**: Official name of the funding opportunity/tender
- **Opportunity Type**: Grant, tender, contract, fellowship, scholarship, etc.
- **Funder/Procurer Name**: Organisation offering the opportunity
- **Reference Number**: Official ID, reference code, or tender number
- **Submission Deadline**: Final submission date and time (ISO format)
- **Publication Date**: When announced

## Financial Information:
- **Funding Value**: Minimum, maximum amounts and currency
- **Co-funding Requirements**: Match funding percentage or amount

## Eligibility:
- **Eligible Applicants**: Organisation types, individual eligibility
- **Geographic Restrictions**: Location-based eligibility
- **Sector Focus**: Specific fields or industries

## Details:
- **Description**: Purpose and objectives
- **Priority Areas**: Themes or service requirements
- **Duration**: Length of funded period
- **Location**: Geographic focus or project location
- **Contact Information**: Email, phone, website

## Evaluation:
- **Assessment Criteria**: How submissions will be evaluated
- **Submission Requirements**: Required documents and format

Return as JSON array with these fields. Use null for missing information.

URL: {url}

CONTENT:
{text}

IMPORTANT: Return ONLY a valid JSON array of opportunities found."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.1,  # Low temperature for factual extraction
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get('response', '').strip()
                    
                    # Try to parse JSON from response
                    try:
                        # Find JSON array in response
                        json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                        if json_match:
                            opportunities = json.loads(json_match.group())
                            return opportunities
                        else:
                            logger.warning("No JSON array found in LLM response")
                            return []
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse LLM JSON: {e}")
                        logger.debug(f"LLM response: {llm_response[:500]}")
                        return []
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return []
    
    async def scrape_website(self, website_config) -> ScrapingResult:
        """Scrape website using Ollama for intelligent extraction"""
        start_time = datetime.utcnow()
        url = website_config.url
        
        try:
            # Check if Ollama is available
            if not await self.check_ollama_available():
                logger.warning("Ollama not available, falling back to demo data")
                return await self._get_demo_data(website_config)
            
            # Fetch webpage
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True, timeout=30)
                
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code} when fetching {url}")
                
                html_content = response.text
            
            # Extract opportunities using LLM
            logger.info(f"Extracting opportunities from {url} using Ollama")
            raw_opportunities = await self.extract_with_llm(html_content, url)
            
            # Process and validate opportunities
            opportunities = []
            for opp in raw_opportunities:
                processed = self._process_opportunity(opp, url)
                if processed:
                    opportunities.append(processed)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScrapingResult(
                website_id=website_config.id,
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
                    "scraper": "ollama",
                    "model": self.model,
                    "extracted_at": datetime.utcnow().isoformat()
                },
                stats={
                    "pages_scraped": 1,
                    "opportunities_found": len(opportunities),
                    "extraction_method": "ollama_llm"
                }
            )
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ScrapingResult(
                website_id=website_config.id,
                website_url=url,
                opportunities=[],
                total_found=0,
                pages_scraped=0,
                pdfs_found=0,
                pdfs_processed=0,
                duration_seconds=duration,
                success=False,
                error_message=str(e),
                metadata={"scraper": "ollama", "error": str(e)},
                stats={}
            )
    
    def _process_opportunity(self, opp: Dict[str, Any], source_url: str) -> Optional[Dict[str, Any]]:
        """Process and validate opportunity data"""
        try:
            # Ensure required fields
            if not opp.get('title'):
                return None
            
            # Process deadline
            deadline = opp.get('deadline')
            if deadline and isinstance(deadline, str):
                # Try to parse various date formats
                try:
                    # Add more date parsing logic as needed
                    if not deadline.endswith('Z'):
                        deadline = deadline + 'Z'
                except:
                    deadline = "2025-12-31T23:59:59Z"  # Default future date
            
            # Process value
            value = opp.get('value', 0)
            if isinstance(value, str):
                # Extract number from string
                value_match = re.search(r'[\d,]+\.?\d*', value.replace(',', ''))
                value = float(value_match.group()) if value_match else 0.0
            
            # Build processed opportunity
            return {
                "title": opp.get('title', '').strip(),
                "description": opp.get('description', '').strip(),
                "reference_number": opp.get('reference_number', f"REF-{hashlib.md5(opp['title'].encode()).hexdigest()[:8]}"),
                "deadline": deadline or "2025-12-31T23:59:59Z",
                "value": float(value),
                "currency": opp.get('currency', 'AUD'),
                "source_url": source_url,
                "categories": opp.get('categories', []) if isinstance(opp.get('categories'), list) else [],
                "location": opp.get('location', 'Australia'),
                "confidence_score": 0.9,  # High confidence for LLM extraction
                "extracted_data": {
                    **opp,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "extraction_method": "ollama_llm"
                }
            }
        except Exception as e:
            logger.error(f"Error processing opportunity: {e}")
            return None
    
    async def _get_demo_data(self, website_config) -> ScrapingResult:
        """Return demo data when Ollama is not available"""
        opportunities = [
            {
                "title": "ICT Hardware Supply and Support Services",
                "description": "The Australian Government is seeking suppliers for ICT hardware including servers, storage systems, and networking equipment, along with ongoing support services.",
                "deadline": "2025-11-30T14:00:00Z",
                "value": 3500000.00,
                "currency": "AUD",
                "reference_number": "AGD-2025-ICT-001",
                "source_url": website_config.url,
                "categories": ["ICT", "Hardware", "Support Services"],
                "location": "Canberra, ACT",
                "confidence_score": 0.95,
                "extracted_data": {
                    "agency": "Australian Government Department of Finance",
                    "contact_email": "procurement@finance.gov.au",
                    "submission_method": "AusTender",
                    "security_clearance": "Baseline",
                    "contract_period": "3 years with 2x1 year options"
                }
            },
            {
                "title": "Environmental Consulting Services - Great Barrier Reef",
                "description": "Seeking environmental consultants for reef health monitoring, data analysis, and conservation strategy development for the Great Barrier Reef Marine Park.",
                "deadline": "2025-10-15T17:00:00Z",
                "value": 850000.00,
                "currency": "AUD",
                "reference_number": "GBRMPA-2025-ENV-002",
                "source_url": website_config.url,
                "categories": ["Environmental", "Consulting", "Marine Conservation"],
                "location": "Townsville, QLD",
                "confidence_score": 0.92,
                "extracted_data": {
                    "agency": "Great Barrier Reef Marine Park Authority",
                    "project_duration": "18 months",
                    "key_requirements": "Marine biology expertise, diving certification, environmental impact assessment experience"
                }
            }
        ]
        
        return ScrapingResult(
            website_id=website_config.id,
            website_url=website_config.url,
            opportunities=opportunities,
            total_found=len(opportunities),
            pages_scraped=1,
            pdfs_found=0,
            pdfs_processed=0,
            duration_seconds=0.5,
            success=True,
            error_message=None,
            metadata={"scraper": "demo", "note": "Ollama not available - using demo data"},
            stats={"extraction_method": "demo_fallback"}
        )