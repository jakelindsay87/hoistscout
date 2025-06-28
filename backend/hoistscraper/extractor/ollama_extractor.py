"""Ollama-based extraction for intelligent opportunity and terms analysis."""

import os
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


class OllamaExtractor:
    """Extract structured data from HTML using Ollama LLM."""
    
    def __init__(self, model: str = "mistral:7b-instruct"):
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
        self.ollama_url = f"{OLLAMA_HOST}/api/generate"
    
    async def extract_opportunities_from_listing(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract all opportunity links from a listing page."""
        try:
            # First, use BeautifulSoup to get all links
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all links that look like tender/grant opportunities
            opportunity_links = []
            
            # Common patterns for tender links
            link_patterns = [
                r'ATM\d+',  # Australian Tenders pattern
                r'tender',
                r'grant',
                r'opportunity',
                r'procurement',
                r'RFT',
                r'EOI',
                r'RFQ'
            ]
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # Check if link matches any pattern
                if any(re.search(pattern, href + text, re.I) for pattern in link_patterns):
                    # Make absolute URL
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(base_url, href)
                    
                    opportunity_links.append({
                        'url': href,
                        'title': text,
                        'source_page': base_url
                    })
            
            # Now use Ollama to identify which links are actual opportunities
            if opportunity_links:
                prompt = f"""
                Analyze these links and identify which ones are actual grant/tender opportunities.
                Return a JSON array of objects with url, title, and is_opportunity (true/false).
                
                Links:
                {json.dumps(opportunity_links[:20], indent=2)}  # Limit to first 20
                
                Return ONLY valid JSON array, no explanation.
                """
                
                response = await self._query_ollama(prompt)
                try:
                    filtered_links = json.loads(response)
                    return [link for link in filtered_links if link.get('is_opportunity', False)]
                except:
                    # If Ollama fails, return all links
                    return opportunity_links
            
            return opportunity_links
            
        except Exception as e:
            logger.error(f"Failed to extract opportunity links: {str(e)}")
            return []
    
    async def extract_opportunity_details(self, html: str, url: str) -> Dict[str, Any]:
        """Extract detailed opportunity information from a detail page."""
        try:
            # Clean HTML for better extraction
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Limit text length for context window
            if len(text) > 8000:
                text = text[:8000] + "..."
            
            prompt = f"""
            Extract grant/tender opportunity information from this webpage.
            
            URL: {url}
            Content: {text}
            
            Extract the following information and return as JSON:
            {{
                "title": "Full title of the opportunity",
                "organization": "Organization offering the grant/tender",
                "description": "Detailed description (2-3 paragraphs)",
                "deadline": "Closing date/deadline in ISO format if found",
                "amount": "Funding amount or value if specified",
                "eligibility": "Who can apply or eligibility criteria",
                "contact": "Contact person or email if provided",
                "reference_number": "ATM ID, tender number, or reference",
                "category": "Category or type of opportunity",
                "location": "Geographic location or area",
                "documents": ["List of downloadable documents mentioned"]
            }}
            
            If a field is not found, use null.
            Return ONLY valid JSON, no explanation.
            """
            
            response = await self._query_ollama(prompt)
            
            # Parse response
            try:
                opportunity = json.loads(response)
                opportunity['source_url'] = url
                opportunity['extraction_method'] = 'ollama'
                opportunity['extracted_at'] = datetime.utcnow().isoformat()
                return opportunity
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Ollama response as JSON: {response[:200]}")
                return self._fallback_extraction(soup, url)
                
        except Exception as e:
            logger.error(f"Failed to extract opportunity details: {str(e)}")
            return self._fallback_extraction(BeautifulSoup(html, 'html.parser'), url)
    
    async def extract_terms_and_conditions(self, text: str) -> Dict[str, Any]:
        """Analyze terms and conditions for key information."""
        try:
            # Limit text length
            if len(text) > 6000:
                text = text[:6000] + "..."
            
            prompt = f"""
            Analyze these terms and conditions for key legal and usage information.
            
            Text: {text}
            
            Extract and return as JSON:
            {{
                "summary": "2-3 sentence summary of key points",
                "allows_commercial_use": true/false,
                "allows_scraping": true/false,
                "requires_attribution": true/false,
                "has_indemnity_clause": true/false,
                "has_liability_limitation": true/false,
                "governing_law": "Jurisdiction if specified",
                "key_restrictions": ["List of main restrictions"],
                "key_permissions": ["List of main permissions"]
            }}
            
            Return ONLY valid JSON.
            """
            
            response = await self._query_ollama(prompt)
            
            try:
                terms = json.loads(response)
                terms['extraction_method'] = 'ollama'
                terms['analyzed_at'] = datetime.utcnow().isoformat()
                return terms
            except json.JSONDecodeError:
                return self._fallback_terms_analysis(text)
                
        except Exception as e:
            logger.error(f"Failed to analyze terms: {str(e)}")
            return self._fallback_terms_analysis(text)
    
    async def _query_ollama(self, prompt: str) -> str:
        """Query Ollama API and return response."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,  # Low temperature for more consistent extraction
                "top_p": 0.9
            }
            
            response = await self.client.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Ollama query failed: {str(e)}")
            raise
    
    def _fallback_extraction(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Fallback extraction using BeautifulSoup."""
        # Try to extract basic information
        title = None
        for tag in ['h1', 'h2', 'h3', 'title']:
            element = soup.find(tag)
            if element:
                title = element.get_text(strip=True)
                break
        
        # Get description from first few paragraphs
        paragraphs = soup.find_all('p', limit=5)
        description = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return {
            "title": title or "Unknown Opportunity",
            "description": description or "No description available",
            "source_url": url,
            "extraction_method": "fallback",
            "requires_manual_review": True,
            "organization": None,
            "deadline": None,
            "amount": None,
            "eligibility": None,
            "contact": None,
            "reference_number": None,
            "category": None,
            "location": None,
            "documents": []
        }
    
    def _fallback_terms_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback terms analysis using pattern matching."""
        text_lower = text.lower()
        
        return {
            "summary": "Terms analysis failed - manual review required",
            "allows_commercial_use": 'commercial use' in text_lower and 'prohibited' not in text_lower,
            "allows_scraping": 'scraping' not in text_lower or 'permitted' in text_lower,
            "requires_attribution": 'attribution' in text_lower,
            "has_indemnity_clause": 'indemnify' in text_lower or 'indemnification' in text_lower,
            "has_liability_limitation": 'limitation of liability' in text_lower,
            "governing_law": "Unknown",
            "key_restrictions": [],
            "key_permissions": [],
            "extraction_method": "fallback",
            "requires_manual_review": True
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Convenience functions for backward compatibility
async def extract_opportunity_with_ollama(html: str, url: str) -> Dict[str, Any]:
    """Extract opportunity using Ollama."""
    extractor = OllamaExtractor()
    try:
        return await extractor.extract_opportunity_details(html, url)
    finally:
        await extractor.close()


async def extract_opportunities_from_listing_with_ollama(html: str, base_url: str) -> List[Dict[str, Any]]:
    """Extract opportunity links from listing page using Ollama."""
    extractor = OllamaExtractor()
    try:
        return await extractor.extract_opportunities_from_listing(html, base_url)
    finally:
        await extractor.close()


async def analyze_terms_with_ollama(text: str) -> Dict[str, Any]:
    """Analyze terms and conditions using Ollama."""
    extractor = OllamaExtractor()
    try:
        return await extractor.extract_terms_and_conditions(text)
    finally:
        await extractor.close()