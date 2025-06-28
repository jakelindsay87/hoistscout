"""Debug endpoints - disabled in production."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, text
import os
import sys
from typing import Dict, Any

from ..db import get_session, engine
from ..security import block_in_production
from ..models import Website

router = APIRouter(
    prefix="/api/debug",
    tags=["debug"],
    dependencies=[Depends(block_in_production)]  # Block all debug endpoints in production
)

@router.get("")
async def debug_endpoint(session: Session = Depends(get_session)):
    """Debug endpoint to diagnose production issues."""
    # This endpoint should be disabled in production via block_in_production
    debug_info: Dict[str, Any] = {
        "status": "checking",
        "environment": {
            "python_version": sys.version,
            "python_path": sys.path[:3],  # Only show first 3 paths
            "working_dir": os.getcwd()
        }
    }
    
    # Check database
    try:
        # Test basic connection
        result = session.exec(text("SELECT 1")).first()
        debug_info["database"] = {"connection": "OK", "test_query": result}
        
        # Check tables
        tables_result = session.exec(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )).all()
        debug_info["database"]["tables"] = [t[0] for t in tables_result]
        
        # Check for specific columns
        cols_result = session.exec(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'website' AND table_schema = 'public'"
        )).all()
        debug_info["database"]["website_columns"] = [c[0] for c in cols_result]
        
    except Exception as e:
        debug_info["database"] = {"connection": f"FAILED: {type(e).__name__}: {str(e)}"}
    
    return debug_info

@router.get("/deployment")
async def debug_deployment():
    """Get deployment configuration info."""
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "system": os.uname().sysname if hasattr(os, 'uname') else "unknown",
        "environment": os.getenv("NODE_ENV", "development"),
        "render": os.getenv("RENDER", "false"),
        "database_url": "configured" if os.getenv("DATABASE_URL") else "not configured",
        "redis_url": "configured" if os.getenv("REDIS_URL") else "not configured",
        "ollama_host": os.getenv("OLLAMA_HOST", "not configured"),
        "cors_origins": os.getenv("CORS_ORIGINS", "not configured")
    }

@router.get("/schema")
async def check_schema(session: Session = Depends(get_session)):
    """Check database schema."""
    try:
        # Get all columns for website table
        result = session.exec(text(
            """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'website' 
            ORDER BY ordinal_position
            """
        )).all()
        
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES"
            }
            for row in result
        ]
        
        return {
            "table": "website",
            "columns": columns,
            "missing_columns": []  # Will be populated by comparing with model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))