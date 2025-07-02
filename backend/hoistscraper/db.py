from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hoistscraper")

# Render uses postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging in development
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=300  # Recreate connections every 5 minutes
)

def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """
    Lazy session generator for dependency injection.
    Automatically commits and closes the session.
    """
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close() 