"""Database configuration and models for HoistScraper."""
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy.engine import Engine

# Database URL from environment
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/hoistscraper")

# Create engine
engine: Optional[Engine] = None


def init_db() -> None:
    """Initialize database connection and create tables."""
    global engine
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)


def get_engine() -> Engine:
    """Get database engine, initializing if needed."""
    if engine is None:
        init_db()
    return engine


@contextmanager
def get_session():
    """Get database session context manager."""
    with Session(get_engine()) as session:
        yield session


# Models
class Website(SQLModel, table=True):
    """Website model for storing scraping targets."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScrapeJob(SQLModel, table=True):
    """Scrape job model for tracking scraping tasks."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    website_id: int = Field(foreign_key="website.id")
    status: str = Field(default="pending")  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)