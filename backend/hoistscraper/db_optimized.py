"""Optimized database configuration with connection pooling."""
import os
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy import event
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hoistscraper.db")

# Determine if we're using SQLite or PostgreSQL
is_sqlite = DATABASE_URL.startswith("sqlite")

# Configure engine with optimized settings
if is_sqlite:
    # SQLite doesn't benefit from connection pooling
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,  # Number of persistent connections
        max_overflow=40,  # Maximum overflow connections
        pool_timeout=30,  # Timeout for getting connection from pool
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL debugging
        connect_args={
            "connect_timeout": 10,
            "application_name": "hoistscraper",
            "options": "-c statement_timeout=30000"  # 30 second statement timeout
        }
    )

# Add connection pool status logging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log when new connection is created."""
    logger.debug(f"New database connection created: {id(dbapi_connection)}")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connection is checked out from pool."""
    logger.debug(f"Connection checked out from pool: {id(dbapi_connection)}")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log when connection is returned to pool."""
    logger.debug(f"Connection returned to pool: {id(dbapi_connection)}")

def init_db():
    """Initialize database tables."""
    logger.info("Initializing database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables initialized successfully")

def get_session():
    """Get a new database session."""
    with Session(engine) as session:
        yield session

@contextmanager
def get_db_session():
    """Context manager for database sessions."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def check_db_connection():
    """Check if database connection is working."""
    try:
        with Session(engine) as session:
            session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

def get_pool_status():
    """Get current connection pool status."""
    if hasattr(engine.pool, 'status'):
        return {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "total": engine.pool.size() + engine.pool.overflow()
        }
    return {"status": "Pool status not available"}

# Performance optimization for bulk operations
class BulkOperations:
    """Helper class for bulk database operations."""
    
    @staticmethod
    def bulk_insert(session: Session, objects: list):
        """Efficiently bulk insert objects."""
        if not objects:
            return
        
        try:
            session.bulk_save_objects(objects)
            session.commit()
            logger.info(f"Bulk inserted {len(objects)} objects")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    @staticmethod
    def bulk_update(session: Session, mapper, mappings: list):
        """Efficiently bulk update objects."""
        if not mappings:
            return
        
        try:
            session.bulk_update_mappings(mapper, mappings)
            session.commit()
            logger.info(f"Bulk updated {len(mappings)} objects")
        except Exception as e:
            session.rollback()
            logger.error(f"Bulk update failed: {e}")
            raise

# Query optimization helpers
class QueryOptimizer:
    """Helper class for optimized queries."""
    
    @staticmethod
    def paginate(query, page: int = 1, per_page: int = 20):
        """Add pagination to query."""
        offset = (page - 1) * per_page
        return query.offset(offset).limit(per_page)
    
    @staticmethod
    def batch_query(session: Session, model, batch_size: int = 1000):
        """Query large datasets in batches."""
        offset = 0
        while True:
            batch = session.query(model).offset(offset).limit(batch_size).all()
            if not batch:
                break
            yield batch
            offset += batch_size