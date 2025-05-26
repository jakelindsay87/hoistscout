"""LLM-powered extraction using Firecrawl and Ollama."""

import os
import json
import logging
from typing import Dict, Any, Optional
from firecrawl import Firecrawl

from .schemas import OPPORTUNITY_EXTRACTION_SCHEMA, TERMS_ANALYSIS_SCHEMA

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firecrawl with Ollama backend
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
FC = Firecrawl(model="ollama/mistral:7b-q4_K_M", api_base=OLLAMA_HOST)


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
        
        # Use Firecrawl's extract_async with structured schema
        resp = await FC.extract_async(
            html=html,
            url=url,
            schema=OPPORTUNITY_EXTRACTION_SCHEMA,
            system_prompt=(
                "Extract opportunity/grant information from the provided content. "
                "Return STRICT JSON only, following the exact schema provided. "
                "If a field is not found, use null for optional fields or empty array for lists. "
                "Focus on funding opportunities, grants, competitions, or similar opportunities."
            )
        )
        
        # Parse and validate the response
        if hasattr(resp, 'json'):
            result = resp.json()
        else:
            result = json.loads(str(resp))
            
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
            "source_url": url
        }


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
        
        prompt = (
            "Analyze the following terms and conditions text. "
            "Summarize the key clauses, then answer ONLY true/false for each question: "
            "(a) Is commercial use allowed? "
            "(b) Is web scraping/crawling forbidden? "
            "Also identify key data usage rights, liability clauses, and termination conditions. "
            "Output JSON following the exact schema provided."
        )
        
        # Use Firecrawl's chat_async for analysis
        resp = await FC.chat_async(
            text,
            system_prompt=prompt,
            schema=TERMS_ANALYSIS_SCHEMA
        )
        
        # Parse and validate the response
        if hasattr(resp, 'json'):
            result = resp.json()
        else:
            result = json.loads(str(resp))
            
        logger.info("Successfully analyzed terms and conditions")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze terms: {str(e)}")
        # Return a basic structure with error info
        return {
            "summary": f"Analysis failed: {str(e)}",
            "allows_commercial_use": False,  # Conservative default
            "forbids_scraping": True,        # Conservative default
            "error": str(e)
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
        logger.warning(f"Structured extraction failed, falling back to basic extraction: {str(e)}")
        
        # Fallback to basic text extraction
        try:
            text_content = await extract_text_content(html)
            
            if extraction_type == "opportunity":
                return {
                    "title": "Manual Review Required",
                    "description": text_content[:500] + "..." if len(text_content) > 500 else text_content,
                    "organization": "Unknown",
                    "source_url": url,
                    "extraction_method": "fallback",
                    "full_text": text_content
                }
            else:  # terms
                return {
                    "summary": text_content[:200] + "..." if len(text_content) > 200 else text_content,
                    "allows_commercial_use": False,
                    "forbids_scraping": True,
                    "extraction_method": "fallback",
                    "full_text": text_content
                }
                
        except Exception as fallback_error:
            logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
            return {
                "error": f"All extraction methods failed: {str(e)}, {str(fallback_error)}",
                "source_url": url
            }


async def extract_text_content(html: str) -> str:
    """Extract clean text content from HTML.
    
    Args:
        html: HTML content to extract text from
        
    Returns:
        Clean text content
    """
    try:
        # Use Firecrawl's scrape functionality to get clean text
        resp = await FC.scrape_async(html=html, formats=["text"])
        
        if hasattr(resp, 'text'):
            return resp.text
        elif hasattr(resp, 'content'):
            return resp.content
        else:
            # Fallback to basic HTML stripping
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(strip=True, separator=' ')
            
    except Exception as e:
        logger.warning(f"Failed to extract text with Firecrawl, using BeautifulSoup fallback: {str(e)}")
        
        # Fallback to BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(strip=True, separator=' ')
        except Exception as bs_error:
            logger.error(f"BeautifulSoup fallback also failed: {str(bs_error)}")
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
                "title": "Batch Extraction Failed"
            })
    
    return results 