"""Database configuration with better error handling."""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
import logging

logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL with fallback options."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.warning("DATABASE_URL not set, using SQLite fallback")
        return "sqlite:///./hoistscout.db"
    
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Converted postgres:// to postgresql:// for SQLAlchemy compatibility")
    
    return database_url

DATABASE_URL = get_database_url()

# Create engine with error handling
try:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        # Additional settings for PostgreSQL
        connect_args={
            "connect_timeout": 10,
        } if DATABASE_URL.startswith("postgresql://") else {}
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # Create a simple in-memory SQLite engine as fallback
    engine = create_engine("sqlite:///:memory:", echo=False)
    logger.warning("Using in-memory SQLite as fallback")

def create_db_and_tables():
    """Create all database tables with error handling."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def get_session() -> Generator[Session, None, None]:
    """Get database session with error handling."""
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()