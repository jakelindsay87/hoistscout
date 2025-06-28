"""Admin endpoints with proper authentication."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, delete
from typing import Optional
from datetime import datetime, timezone
import os

from ..models import Website, ScrapeJob, Opportunity
from ..db import get_session
from ..security import require_admin_auth
from ..logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_auth)]  # Require auth for all admin endpoints
)

@router.post("/clear-database")
async def clear_database(
    confirm: bool = Query(False, description="Set to true to confirm database clearing"),
    tables: Optional[str] = Query(None, description="Comma-separated list of tables to clear"),
    session: Session = Depends(get_session),
    api_key: str = Depends(require_admin_auth)
):
    """Clear database tables - DANGEROUS operation requiring confirmation."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Database clearing requires confirmation. Set confirm=true"
        )
    
    # Only allow in development unless explicitly enabled
    if os.getenv("RENDER") == "true" and os.getenv("ALLOW_PROD_DB_CLEAR") != "true":
        raise HTTPException(
            status_code=403,
            detail="Database clearing is disabled in production"
        )
    
    cleared_tables = []
    
    try:
        if tables:
            table_list = [t.strip().lower() for t in tables.split(",")]
        else:
            table_list = ["opportunity", "scrapejob", "website"]
        
        # Clear tables in order to respect foreign key constraints
        if "opportunity" in table_list:
            count = session.exec(select(Opportunity)).all()
            session.exec(delete(Opportunity))
            cleared_tables.append(f"opportunity ({len(count)} records)")
        
        if "scrapejob" in table_list:
            count = session.exec(select(ScrapeJob)).all()
            session.exec(delete(ScrapeJob))
            cleared_tables.append(f"scrapejob ({len(count)} records)")
        
        if "website" in table_list:
            count = session.exec(select(Website)).all()
            session.exec(delete(Website))
            cleared_tables.append(f"website ({len(count)} records)")
        
        session.commit()
        
        logger.warning(f"Database cleared by admin. Tables: {cleared_tables}")
        
        return {
            "status": "success",
            "cleared_tables": cleared_tables,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to clear database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear database: {str(e)}"
        )

@router.get("/stats")
async def get_admin_stats(
    session: Session = Depends(get_session),
    api_key: str = Depends(require_admin_auth)
):
    """Get detailed system statistics."""
    stats = {
        "websites": {
            "total": len(session.exec(select(Website)).all()),
            "active": len(session.exec(select(Website).where(Website.active == True)).all()),
            "inactive": len(session.exec(select(Website).where(Website.active == False)).all())
        },
        "jobs": {
            "total": len(session.exec(select(ScrapeJob)).all()),
            "pending": len(session.exec(select(ScrapeJob).where(ScrapeJob.status == "pending")).all()),
            "running": len(session.exec(select(ScrapeJob).where(ScrapeJob.status == "running")).all()),
            "completed": len(session.exec(select(ScrapeJob).where(ScrapeJob.status == "completed")).all()),
            "failed": len(session.exec(select(ScrapeJob).where(ScrapeJob.status == "failed")).all())
        },
        "opportunities": {
            "total": len(session.exec(select(Opportunity)).all())
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return stats