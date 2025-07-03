"""Create demo user for testing"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..utils.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)


async def ensure_demo_user(db: AsyncSession) -> None:
    """Ensure demo user exists in the database"""
    try:
        # Check if demo user already exists
        result = await db.execute(
            select(User).where(User.username == "demo")
        )
        demo_user = result.scalar_one_or_none()
        
        if not demo_user:
            # Create demo user
            demo_user = User(
                email="demo@hoistscout.com",
                username="demo",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
                is_superuser=False
            )
            db.add(demo_user)
            await db.commit()
            logger.info("Demo user created successfully")
        else:
            logger.info("Demo user already exists")
            
    except Exception as e:
        logger.error(f"Error creating demo user: {e}")
        await db.rollback()
        raise