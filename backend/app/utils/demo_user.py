"""Create demo user for testing"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User, UserRole
from ..utils.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)


async def ensure_demo_user(db: AsyncSession) -> None:
    """Ensure demo user exists in the database"""
    try:
        # Check if demo user already exists by email or username "demo"
        result = await db.execute(
            select(User).where(
                (User.email == "demo@hoistscout.com") | (User.email == "demo")
            )
        )
        demo_user = result.scalar_one_or_none()
        
        if not demo_user:
            # Create demo user with EDITOR role
            demo_user = User(
                email="demo@hoistscout.com",
                password_hash=get_password_hash("demo123"),
                full_name="Demo User",
                role=UserRole.EDITOR,
                is_active=True
            )
            db.add(demo_user)
            await db.commit()
            logger.info("Demo user created successfully")
        else:
            logger.info("Demo user already exists")
            # Update role if it's not EDITOR
            if demo_user.role != UserRole.EDITOR:
                demo_user.role = UserRole.EDITOR
                await db.commit()
                logger.info("Updated demo user role to EDITOR")
            
    except Exception as e:
        logger.error(f"Error creating demo user: {e}")
        await db.rollback()
        raise