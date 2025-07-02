from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from ..database import get_db
from ..models.user import User
from ..models.opportunity import Opportunity
from ..schemas.opportunity import OpportunityResponse, OpportunitySearch
from .auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[OpportunityResponse])
async def search_opportunities(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    deadline_after: Optional[datetime] = None,
    deadline_before: Optional[datetime] = None,
    website_ids: Optional[str] = Query(None, description="Comma-separated website IDs"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    # Build query
    stmt = select(Opportunity)
    conditions = []
    
    # Full-text search
    if query:
        search_condition = or_(
            Opportunity.title.ilike(f"%{query}%"),
            Opportunity.description.ilike(f"%{query}%"),
            Opportunity.reference_number.ilike(f"%{query}%")
        )
        conditions.append(search_condition)
    
    # Category filter
    if category:
        conditions.append(Opportunity.categories.contains([category]))
    
    # Location filter
    if location:
        conditions.append(Opportunity.location.ilike(f"%{location}%"))
    
    # Value range
    if min_value is not None:
        conditions.append(Opportunity.value >= min_value)
    if max_value is not None:
        conditions.append(Opportunity.value <= max_value)
    
    # Deadline range
    if deadline_after:
        conditions.append(Opportunity.deadline >= deadline_after)
    if deadline_before:
        conditions.append(Opportunity.deadline <= deadline_before)
    
    # Website filter
    if website_ids:
        website_id_list = [int(id.strip()) for id in website_ids.split(",")]
        conditions.append(Opportunity.website_id.in_(website_id_list))
    
    # Apply conditions
    if conditions:
        stmt = stmt.where(and_(*conditions))
    
    # Order by deadline (nearest first)
    stmt = stmt.order_by(Opportunity.deadline.asc().nullslast())
    
    # Pagination
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    opportunities = result.scalars().all()
    
    return opportunities


# Alias for search functionality
@router.get("/search", response_model=List[OpportunityResponse])
async def search_opportunities_alias(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    deadline_after: Optional[datetime] = None,
    deadline_before: Optional[datetime] = None,
    website_ids: Optional[str] = Query(None, description="Comma-separated website IDs"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Alias endpoint for search - delegates to main search endpoint"""
    return await search_opportunities(
        db, current_user, query, category, location, 
        min_value, max_value, deadline_after, deadline_before,
        website_ids, limit, offset
    )


@router.get("/stats")
async def get_opportunity_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Total opportunities
    total_stmt = select(func.count(Opportunity.id))
    total_result = await db.execute(total_stmt)
    total_count = total_result.scalar()
    
    # Opportunities by category
    category_stmt = select(
        func.unnest(Opportunity.categories).label('category'),
        func.count(Opportunity.id).label('count')
    ).group_by('category')
    category_result = await db.execute(category_stmt)
    categories = category_result.all()
    
    # Average value
    avg_value_stmt = select(func.avg(Opportunity.value))
    avg_value_result = await db.execute(avg_value_stmt)
    avg_value = avg_value_result.scalar()
    
    # Upcoming deadlines (next 7 days)
    upcoming_stmt = select(func.count(Opportunity.id)).where(
        and_(
            Opportunity.deadline >= datetime.utcnow(),
            Opportunity.deadline <= datetime.utcnow() + timedelta(days=7)
        )
    )
    upcoming_result = await db.execute(upcoming_stmt)
    upcoming_count = upcoming_result.scalar()
    
    return {
        "total_opportunities": total_count,
        "categories": [{"category": c[0], "count": c[1]} for c in categories],
        "average_value": float(avg_value) if avg_value else 0,
        "upcoming_deadlines": upcoming_count
    }


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    return opportunity


@router.post("/export")
async def export_opportunities(
    search: OpportunitySearch,
    format: str = Query("csv", enum=["csv", "excel", "json"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # TODO: Implement export functionality
    return {
        "detail": "Export job created",
        "job_id": "export-123",
        "format": format
    }