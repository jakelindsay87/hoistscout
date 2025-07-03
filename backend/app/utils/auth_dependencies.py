"""Authentication dependencies with optional demo mode"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.user import User
from .auth import get_current_user as _get_current_user
from ..config import get_settings

settings = get_settings()


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = None
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None (for optional auth endpoints)"""
    if not token:
        return None
    try:
        return await _get_current_user(token, db)
    except HTTPException:
        return None


async def get_current_user_or_demo(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Get current user or demo user for public endpoints"""
    if current_user:
        return current_user
    
    # For demo/public mode, create a virtual demo user
    # This allows the frontend to work without authentication
    from ..models.user import User
    demo_user = User(
        id=0,
        email="demo@hoistscout.com",
        username="demo",
        hashed_password="",  # Not used for virtual user
        is_active=True,
        is_superuser=False
    )
    return demo_user