"""Sites API routes."""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import select, func
from pydantic import BaseModel, HttpUrl

from ..db import get_session, Website

router = APIRouter(prefix="/api/sites", tags=["sites"])


class SiteCreate(BaseModel):
    """Schema for creating a new site."""
    url: HttpUrl
    name: str
    description: Optional[str] = None


class SiteResponse(BaseModel):
    """Schema for site response."""
    id: int
    url: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class SiteListResponse(BaseModel):
    """Schema for paginated site list response."""
    items: List[SiteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(site: SiteCreate):
    """Create a new site. Returns 409 if URL already exists."""
    with get_session() as session:
        # Check if URL already exists
        existing = session.exec(
            select(Website).where(Website.url == str(site.url))
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Website with URL {site.url} already exists"
            )
        
        # Create new website
        db_site = Website(
            url=str(site.url),
            name=site.name,
            description=site.description
        )
        session.add(db_site)
        session.commit()
        session.refresh(db_site)
        
        return SiteResponse(
            id=db_site.id,
            url=db_site.url,
            name=db_site.name,
            description=db_site.description,
            created_at=db_site.created_at,
            updated_at=db_site.updated_at
        )


@router.get("", response_model=SiteListResponse)
async def list_sites(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """List all sites with pagination."""
    with get_session() as session:
        # Count total items
        count_query = select(func.count()).select_from(Website)
        total = session.exec(count_query).one()
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Get paginated results
        query = select(Website).offset(offset).limit(page_size).order_by(Website.created_at.desc())
        sites = session.exec(query).all()
        
        return SiteListResponse(
            items=[
                SiteResponse(
                    id=site.id,
                    url=site.url,
                    name=site.name,
                    description=site.description,
                    created_at=site.created_at,
                    updated_at=site.updated_at
                )
                for site in sites
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(site_id: int):
    """Get a single site by ID."""
    with get_session() as session:
        site = session.get(Website, site_id)
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        return SiteResponse(
            id=site.id,
            url=site.url,
            name=site.name,
            description=site.description,
            created_at=site.created_at,
            updated_at=site.updated_at
        )