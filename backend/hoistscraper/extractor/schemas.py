"""Schema definitions for structured data extraction."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class OpportunitySchema(BaseModel):
    """Schema for opportunity/grant extraction."""
    title: str = Field(description="Title of the opportunity")
    description: str = Field(description="Detailed description")
    organization: str = Field(description="Organization offering the opportunity")
    deadline: Optional[str] = Field(description="Application deadline")
    amount: Optional[str] = Field(description="Funding amount or value")
    eligibility: Optional[str] = Field(description="Eligibility criteria")
    categories: List[str] = Field(default=[], description="Categories or tags")
    location: Optional[str] = Field(description="Geographic location or scope")
    contact_info: Optional[str] = Field(description="Contact information")
    application_url: Optional[str] = Field(description="Application URL")
    requirements: List[str] = Field(default=[], description="Application requirements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Research Grant for AI Innovation",
                "description": "Funding for artificial intelligence research projects",
                "organization": "Tech Foundation",
                "deadline": "2024-12-31",
                "amount": "$50,000",
                "eligibility": "Academic institutions and researchers",
                "categories": ["AI", "Research", "Technology"],
                "location": "United States",
                "contact_info": "grants@techfoundation.org",
                "application_url": "https://techfoundation.org/apply",
                "requirements": ["Research proposal", "Budget breakdown", "CV"]
            }
        }


class TermsAnalysisSchema(BaseModel):
    """Schema for terms and conditions analysis."""
    summary: str = Field(description="Summary of key clauses and terms")
    allows_commercial_use: bool = Field(description="Whether commercial use is allowed")
    forbids_scraping: bool = Field(description="Whether scraping/crawling is forbidden")
    data_usage_rights: Optional[str] = Field(description="Rights regarding data usage")
    liability_clauses: Optional[str] = Field(description="Key liability limitations")
    termination_conditions: Optional[str] = Field(description="Conditions for termination")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Standard terms allowing personal use, restricting commercial use without permission",
                "allows_commercial_use": False,
                "forbids_scraping": True,
                "data_usage_rights": "Personal use only, no redistribution",
                "liability_clauses": "Service provided as-is, no warranties",
                "termination_conditions": "May terminate for violation of terms"
            }
        }


# Firecrawl schema definitions for API calls
OPPORTUNITY_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Title of the opportunity"},
        "description": {"type": "string", "description": "Detailed description"},
        "organization": {"type": "string", "description": "Organization offering the opportunity"},
        "deadline": {"type": "string", "description": "Application deadline"},
        "amount": {"type": "string", "description": "Funding amount or value"},
        "eligibility": {"type": "string", "description": "Eligibility criteria"},
        "categories": {"type": "array", "items": {"type": "string"}, "description": "Categories or tags"},
        "location": {"type": "string", "description": "Geographic location or scope"},
        "contact_info": {"type": "string", "description": "Contact information"},
        "application_url": {"type": "string", "description": "Application URL"},
        "requirements": {"type": "array", "items": {"type": "string"}, "description": "Application requirements"}
    },
    "required": ["title", "description", "organization"]
}

TERMS_ANALYSIS_SCHEMA = {
    "type": "object", 
    "properties": {
        "summary": {"type": "string", "description": "Summary of key clauses and terms"},
        "allows_commercial_use": {"type": "boolean", "description": "Whether commercial use is allowed"},
        "forbids_scraping": {"type": "boolean", "description": "Whether scraping/crawling is forbidden"},
        "data_usage_rights": {"type": "string", "description": "Rights regarding data usage"},
        "liability_clauses": {"type": "string", "description": "Key liability limitations"},
        "termination_conditions": {"type": "string", "description": "Conditions for termination"}
    },
    "required": ["summary", "allows_commercial_use", "forbids_scraping"]
} 