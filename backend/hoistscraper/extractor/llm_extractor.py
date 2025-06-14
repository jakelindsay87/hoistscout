"""BeautifulSoup-based extraction for opportunities and terms analysis."""

import os
import json
import logging
from typing import Dict, Any
from bs4 import BeautifulSoup

from .schemas import OPPORTUNITY_EXTRACTION_SCHEMA, TERMS_ANALYSIS_SCHEMA

# Configure logging
logger = logging.getLogger(__name__)


async def extract_opportunity(html: str, url: str) -> Dict[str, Any]:
    """Extract structured opportunity data from HTML content.
    
    Args:
        html: HTML content to extract from
        url: Source URL for context
        
    Returns:
        Dictionary containing extracted opportunity data
        
    Raises:
        Exception: If extraction fails
    """
    try:
        logger.info(f"Extracting opportunity data from {url}")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title - try common heading tags
        title = None
        for tag in ['h1', 'h2', 'title']:
            element = soup.find(tag)
            if element:
                title = element.get_text(strip=True)
                break
        
        if not title:
            title = "Opportunity - Manual Review Required"
        
        # Extract description - get first few paragraphs
        paragraphs = soup.find_all('p', limit=5)
        description = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        if not description:
            # Fallback to all text content (limited)
            text_content = soup.get_text(strip=True, separator=' ')
            description = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
        
        # Try to find organization name in common patterns
        organization = "Unknown Organization"
        
        # Look for meta tags first
        org_meta = soup.find('meta', {'name': ['author', 'organization', 'publisher']})
        if org_meta and org_meta.get('content'):
            organization = org_meta['content']
        else:
            # Try to find in text patterns
            for pattern in ['organization', 'company', 'agency', 'foundation', 'ministry', 'department']:
                # Case-insensitive search for text containing the pattern
                element = soup.find(text=lambda text: text and pattern.lower() in text.lower())
                if element:
                    # Get the parent element's text
                    parent = element.parent
                    if parent:
                        org_text = parent.get_text(strip=True)
                        if 10 < len(org_text) < 100:  # Reasonable org name length
                            organization = org_text
                            break
        
        # Extract deadline if possible
        deadline = None
        deadline_patterns = ['deadline', 'due date', 'closing date', 'submission date', 'expires']
        for pattern in deadline_patterns:
            deadline_elem = soup.find(text=lambda text: text and pattern.lower() in text.lower())
            if deadline_elem:
                parent_text = deadline_elem.parent.get_text(strip=True) if deadline_elem.parent else ""
                if parent_text and len(parent_text) < 200:
                    deadline = parent_text
                    break
        
        # Extract amount if possible
        amount = None
        amount_patterns = ['amount', 'funding', 'grant', '$', '€', '£']
        for pattern in amount_patterns:
            amount_elem = soup.find(text=lambda text: text and pattern in text.lower())
            if amount_elem:
                parent_text = amount_elem.parent.get_text(strip=True) if amount_elem.parent else ""
                if parent_text and len(parent_text) < 100:
                    amount = parent_text
                    break
        
        result = {
            "title": title,
            "description": description,
            "organization": organization,
            "source_url": url,
            "extraction_method": "beautifulsoup",
            "deadline": deadline,
            "amount": amount,
            "requires_manual_review": False
        }
        
        logger.info(f"Successfully extracted opportunity: {result.get('title', 'Unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to extract opportunity from {url}: {str(e)}")
        # Return a basic structure with error info
        return {
            "title": "Extraction Failed",
            "description": f"Failed to extract data: {str(e)}",
            "organization": "Unknown",
            "error": str(e),
            "source_url": url,
            "extraction_method": "beautifulsoup",
            "requires_manual_review": True
        }


async def extract_opportunity_bs(html: str, url: str) -> Dict[str, Any]:
    """Alias for extract_opportunity for backward compatibility."""
    return await extract_opportunity(html, url)


async def analyse_terms(text: str) -> Dict[str, Any]:
    """Analyze terms and conditions text for key legal clauses.
    
    Args:
        text: Terms and conditions text to analyze
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        Exception: If analysis fails
    """
    try:
        logger.info("Analyzing terms and conditions")
        
        # Convert to lowercase for searching
        text_lower = text.lower()
        
        # Check for commercial use patterns
        commercial_allow_patterns = [
            'commercial use is permitted',
            'commercial use allowed',
            'may use for commercial',
            'commercial purposes allowed'
        ]
        commercial_forbid_patterns = [
            'no commercial use',
            'non-commercial only',
            'not for commercial',
            'commercial use is prohibited',
            'personal use only'
        ]
        
        allows_commercial = any(pattern in text_lower for pattern in commercial_allow_patterns)
        forbids_commercial = any(pattern in text_lower for pattern in commercial_forbid_patterns)
        
        # If we find forbidding patterns, commercial use is not allowed
        allows_commercial_use = allows_commercial and not forbids_commercial
        
        # Check for scraping/crawling patterns
        scraping_forbid_patterns = [
            'no scraping',
            'no crawling',
            'no robots',
            'no automated',
            'scraping is prohibited',
            'crawling is prohibited',
            'do not scrape',
            'do not crawl'
        ]
        scraping_allow_patterns = [
            'scraping is allowed',
            'crawling is permitted',
            'automated access allowed'
        ]
        
        forbids_scraping = any(pattern in text_lower for pattern in scraping_forbid_patterns)
        allows_scraping = any(pattern in text_lower for pattern in scraping_allow_patterns)
        
        # If we find forbidding patterns or don't explicitly find allowing patterns, assume scraping is forbidden
        forbids_scraping_result = forbids_scraping or not allows_scraping
        
        # Create a summary of key points
        summary_points = []
        
        # Look for key sections
        if 'commercial' in text_lower:
            summary_points.append("Contains commercial use terms")
        if 'scraping' in text_lower or 'crawling' in text_lower or 'automated' in text_lower:
            summary_points.append("Contains automated access terms")
        if 'liability' in text_lower:
            summary_points.append("Contains liability clauses")
        if 'termination' in text_lower:
            summary_points.append("Contains termination conditions")
        if 'privacy' in text_lower or 'data' in text_lower:
            summary_points.append("Contains data/privacy terms")
        
        summary = "; ".join(summary_points) if summary_points else "Standard terms and conditions"
        
        result = {
            "summary": summary,
            "allows_commercial_use": allows_commercial_use,
            "forbids_scraping": forbids_scraping_result,
            "extraction_method": "pattern_matching",
            "confidence": "low"  # Since we're using simple pattern matching
        }
        
        logger.info("Successfully analyzed terms and conditions")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze terms: {str(e)}")
        # Return a basic structure with error info
        return {
            "summary": f"Analysis failed: {str(e)}",
            "allows_commercial_use": False,  # Conservative default
            "forbids_scraping": True,        # Conservative default
            "error": str(e),
            "extraction_method": "pattern_matching"
        }


async def extract_with_fallback(html: str, url: str, extraction_type: str = "opportunity") -> Dict[str, Any]:
    """Extract data with fallback to basic text extraction if structured extraction fails.
    
    Args:
        html: HTML content to extract from
        url: Source URL for context
        extraction_type: Type of extraction ("opportunity" or "terms")
        
    Returns:
        Dictionary containing extracted data
    """
    try:
        if extraction_type == "opportunity":
            return await extract_opportunity(html, url)
        elif extraction_type == "terms":
            # For terms analysis, we need to extract text first
            text_content = await extract_text_content(html)
            return await analyse_terms(text_content)
        else:
            raise ValueError(f"Unknown extraction type: {extraction_type}")
            
    except Exception as e:
        logger.warning(f"Extraction failed, returning basic structure: {str(e)}")
        
        # Return minimal structure
        if extraction_type == "opportunity":
            return {
                "title": "Manual Review Required",
                "description": "Failed to extract content",
                "organization": "Unknown",
                "source_url": url,
                "extraction_method": "fallback",
                "error": str(e),
                "requires_manual_review": True
            }
        else:  # terms
            return {
                "summary": "Failed to analyze terms",
                "allows_commercial_use": False,
                "forbids_scraping": True,
                "extraction_method": "fallback",
                "error": str(e)
            }


async def extract_text_content(html: str) -> str:
    """Extract clean text content from HTML.
    
    Args:
        html: HTML content to extract text from
        
    Returns:
        Clean text content
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(strip=True, separator=' ')
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Failed to extract text content: {str(e)}")
        return html  # Return raw HTML as last resort


# Utility functions for batch processing
async def batch_extract_opportunities(html_content_list: list, urls: list) -> list:
    """Extract opportunities from multiple HTML contents in batch.
    
    Args:
        html_content_list: List of HTML contents
        urls: List of corresponding URLs
        
    Returns:
        List of extracted opportunity data
    """
    results = []
    for html, url in zip(html_content_list, urls):
        try:
            result = await extract_opportunity(html, url)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch extraction failed for {url}: {str(e)}")
            results.append({
                "error": str(e),
                "source_url": url,
                "title": "Batch Extraction Failed",
                "extraction_method": "beautifulsoup",
                "requires_manual_review": True
            })
    
    return results