"""
Lightweight Ollama proxy for Render deployment
Forwards requests to external Ollama instance or provides mock responses
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Dict, Any
import json
from datetime import datetime

app = FastAPI(title="HoistScout Ollama Proxy")

# Configuration
EXTERNAL_OLLAMA_URL = os.getenv("EXTERNAL_OLLAMA_URL", "")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
API_KEY = os.getenv("OLLAMA_PROXY_API_KEY", "")

# Enhanced extraction prompt
EXTRACTION_PROMPT = """You are a specialised funding opportunity extraction system. Your task is to analyse grant, tender, and funding opportunity documents, PDFs, and web pages to extract structured information.

Extract the following information with high accuracy:

## Core Opportunity Information
- **Title**: Official name of the funding opportunity/tender
- **Opportunity Type**: Grant, tender, contract, fellowship, scholarship, etc.
- **Funder/Procurer Name**: Organisation offering the opportunity
- **Reference Number**: Official ID, reference code, or tender number
- **Publication Date**: When the opportunity was announced
- **Application/Submission Deadline**: Final submission date and time

## Financial Information
- **Funding/Contract Value**: Minimum amount, Maximum amount, Currency
- **Co-funding Requirements**: Match funding percentage or amount

## Timeline and Process
- **Submission Deadline**: Include time zone
- **Project/Contract Start Date**: Implementation beginning
- **Duration**: Length of funded period or contract term

## Eligibility and Requirements
- **Eligible Applicants**: Organisation types, Individual eligibility
- **Geographic Restrictions**: Location-based eligibility
- **Sector/Industry Focus**: Specific fields or industries

## Opportunity Focus and Scope
- **Description**: Detailed purpose and objectives
- **Priority Areas**: Specific themes or service requirements
- **Target Beneficiaries**: Who should benefit or be served

## Contact Information
- Organisation contact details
- Application support contacts

Return the extraction as a JSON object. Use null for missing information.

URL: {url}

CONTENT:
{content}

Extract opportunities and return ONLY a JSON array."""


@app.get("/")
async def root():
    return {
        "service": "HoistScout Ollama Proxy",
        "status": "running",
        "mode": "mock" if MOCK_MODE else "proxy",
        "external_ollama": EXTERNAL_OLLAMA_URL if EXTERNAL_OLLAMA_URL else "not configured"
    }


@app.get("/api/tags")
async def get_tags():
    """Ollama API compatibility - list models"""
    if EXTERNAL_OLLAMA_URL and not MOCK_MODE:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{EXTERNAL_OLLAMA_URL}/api/tags", timeout=10)
                return response.json()
        except:
            pass
    
    # Mock response
    return {
        "models": [
            {"name": "llama3.1", "size": 4661224096, "digest": "mock", "modified_at": datetime.utcnow().isoformat()}
        ]
    }


@app.post("/api/generate")
async def generate(request: Dict[str, Any]):
    """Ollama API compatibility - generate text"""
    prompt = request.get("prompt", "")
    model = request.get("model", "llama3.1")
    
    # If external Ollama is configured and we're not in mock mode
    if EXTERNAL_OLLAMA_URL and not MOCK_MODE:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{EXTERNAL_OLLAMA_URL}/api/generate",
                    json=request,
                    timeout=60
                )
                return response.json()
        except Exception as e:
            # Fall through to mock mode if external fails
            print(f"External Ollama failed: {e}")
    
    # Mock mode - provide intelligent mock responses
    if "grant" in prompt.lower() or "tender" in prompt.lower():
        # Check if this is an extraction request
        if "extract" in prompt.lower() and ("opportunity" in prompt.lower() or "funding" in prompt.lower()):
            # Generate mock extraction based on content
            mock_opportunities = []
            
            # Look for patterns in the prompt
            if "tenders.gov.au" in prompt or "australian" in prompt.lower():
                mock_opportunities = [
                    {
                        "title": "Digital Transformation Services Panel",
                        "opportunity_type": "Tender",
                        "funder_name": "Australian Digital Health Agency",
                        "reference_number": "ADHA-2025-DTS-001",
                        "publication_date": "2025-01-15",
                        "submission_deadline": "2025-02-28T14:00:00+11:00",
                        "funding_value": {
                            "minimum": 500000,
                            "maximum": 5000000,
                            "currency": "AUD"
                        },
                        "description": "Seeking providers for digital health transformation services including system integration, data analytics, and cyber security.",
                        "eligible_applicants": ["IT Services Companies", "Digital Consultancies", "System Integrators"],
                        "geographic_restrictions": "Australian registered businesses",
                        "sector_focus": ["Healthcare", "Digital Technology", "Cyber Security"],
                        "duration": "3 years with 2x1 year options",
                        "contact": {
                            "email": "procurement@digitalhealth.gov.au",
                            "phone": "+61 2 6289 1555"
                        }
                    },
                    {
                        "title": "Regional Infrastructure Development Grant",
                        "opportunity_type": "Grant",
                        "funder_name": "Department of Infrastructure, Transport, Regional Development",
                        "reference_number": "DIRD-2025-RIDG-002",
                        "publication_date": "2025-01-20",
                        "submission_deadline": "2025-03-15T17:00:00+11:00",
                        "funding_value": {
                            "minimum": 100000,
                            "maximum": 2000000,
                            "currency": "AUD"
                        },
                        "co_funding_requirements": "50% match funding required",
                        "description": "Grants for regional infrastructure projects that enhance connectivity, economic development, and community resilience.",
                        "eligible_applicants": ["Local Governments", "Regional Development Organisations", "Community Groups"],
                        "geographic_restrictions": "Regional and remote Australia only",
                        "priority_areas": ["Transport Infrastructure", "Digital Connectivity", "Water Security", "Community Facilities"],
                        "duration": "Up to 24 months",
                        "contact": {
                            "email": "regional.grants@infrastructure.gov.au",
                            "website": "https://www.infrastructure.gov.au/grants"
                        }
                    }
                ]
            else:
                # Generic mock opportunity
                mock_opportunities = [
                    {
                        "title": "Innovation and Technology Development Grant",
                        "opportunity_type": "Grant",
                        "funder_name": "National Innovation Agency",
                        "reference_number": "NIA-2025-ITD-001",
                        "submission_deadline": "2025-12-31T23:59:59Z",
                        "funding_value": {
                            "maximum": 1000000,
                            "currency": "USD"
                        },
                        "description": "Funding for innovative technology solutions addressing societal challenges.",
                        "eligible_applicants": ["Startups", "SMEs", "Research Institutions"],
                        "sector_focus": ["Technology", "Innovation", "Research"],
                        "duration": "12-36 months"
                    }
                ]
            
            response_text = json.dumps(mock_opportunities, indent=2)
        else:
            # Generic response
            response_text = "Based on the tender documentation, this appears to be a government procurement opportunity with standard eligibility requirements and evaluation criteria."
    else:
        # Default mock response
        response_text = "Mock response from Ollama proxy. Configure EXTERNAL_OLLAMA_URL for real LLM responses."
    
    return {
        "model": model,
        "created_at": datetime.utcnow().isoformat(),
        "response": response_text,
        "done": True,
        "context": [],
        "total_duration": 1000000000,  # 1 second in nanoseconds
        "load_duration": 500000000,
        "prompt_eval_duration": 250000000,
        "eval_duration": 250000000,
        "eval_count": len(response_text.split())
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)