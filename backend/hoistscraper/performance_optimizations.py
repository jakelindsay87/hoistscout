"""Performance optimizations for HoistScraper API."""
from functools import lru_cache, wraps
from datetime import datetime, timedelta
import asyncio
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select, func
from sqlalchemy import text
from sqlalchemy.orm import selectinload
import time
import logging

from .models import Website, ScrapeJob, Opportunity
from .db import engine

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Central class for performance optimizations."""
    
    @staticmethod
    def cache_with_ttl(ttl_seconds: int = 300):
        """Decorator for caching with time-to-live."""
        def decorator(func):
            cache = {}
            cache_time = {}
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key from function arguments
                key = str(args) + str(kwargs)
                
                # Check if cached value exists and is still valid
                if key in cache and key in cache_time:
                    if time.time() - cache_time[key] < ttl_seconds:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cache[key]
                
                # Call function and cache result
                result = func(*args, **kwargs)
                cache[key] = result
                cache_time[key] = time.time()
                
                return result
            
            # Add cache clear method
            wrapper.clear_cache = lambda: (cache.clear(), cache_time.clear())
            return wrapper
        
        return decorator
    
    @staticmethod
    @cache_with_ttl(ttl_seconds=60)
    def get_website_count() -> int:
        """Get total website count with caching."""
        with Session(engine) as session:
            return session.exec(select(func.count(Website.id))).one()
    
    @staticmethod
    @cache_with_ttl(ttl_seconds=30)
    def get_job_statistics() -> Dict[str, Any]:
        """Get job statistics with caching."""
        with Session(engine) as session:
            # Use single query with aggregation
            stats = session.exec(
                select(
                    ScrapeJob.status,
                    func.count(ScrapeJob.id).label('count')
                ).group_by(ScrapeJob.status)
            ).all()
            
            return {
                status: count for status, count in stats
            }
    
    @staticmethod
    def get_websites_optimized(
        limit: int = 100,
        offset: int = 0,
        active_only: bool = False
    ) -> List[Website]:
        """Get websites with optimized query."""
        with Session(engine) as session:
            query = select(Website)
            
            if active_only:
                query = query.where(Website.active == True)
            
            # Use specific column selection for better performance
            query = query.offset(offset).limit(limit)
            
            return session.exec(query).all()
    
    @staticmethod
    def get_recent_jobs_optimized(limit: int = 50) -> List[ScrapeJob]:
        """Get recent jobs with optimized query."""
        with Session(engine) as session:
            # Use index on created_at for faster sorting
            query = (
                select(ScrapeJob)
                .order_by(ScrapeJob.created_at.desc())
                .limit(limit)
            )
            
            return session.exec(query).all()
    
    @staticmethod
    def batch_create_jobs(website_ids: List[int]) -> List[ScrapeJob]:
        """Create multiple jobs in a single transaction."""
        jobs = []
        
        with Session(engine) as session:
            for website_id in website_ids:
                job = ScrapeJob(website_id=website_id)
                session.add(job)
                jobs.append(job)
            
            session.commit()
            
            # Refresh all jobs to get IDs
            for job in jobs:
                session.refresh(job)
        
        return jobs
    
    @staticmethod
    def vacuum_old_data(days: int = 30) -> int:
        """Remove old completed jobs to improve performance."""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = 0
        
        with Session(engine) as session:
            # Delete in batches to avoid locking
            while True:
                result = session.exec(
                    select(ScrapeJob)
                    .where(ScrapeJob.status == "completed")
                    .where(ScrapeJob.completed_at < cutoff_date)
                    .limit(100)
                ).all()
                
                if not result:
                    break
                
                for job in result:
                    session.delete(job)
                    deleted += 1
                
                session.commit()
                
                # Small delay to prevent database overload
                time.sleep(0.1)
        
        logger.info(f"Deleted {deleted} old completed jobs")
        return deleted
    
    @staticmethod
    async def warmup_cache():
        """Pre-populate caches for better initial performance."""
        logger.info("Warming up caches...")
        
        # Trigger cached functions
        PerformanceOptimizer.get_website_count()
        PerformanceOptimizer.get_job_statistics()
        
        logger.info("Cache warmup complete")


class DatabaseOptimizations:
    """Database-specific optimizations."""
    
    @staticmethod
    def create_indexes():
        """Create performance indexes if they don't exist."""
        index_queries = [
            # Composite index for common website queries
            """
            CREATE INDEX IF NOT EXISTS idx_website_active_created 
            ON website(active, created_at DESC);
            """,
            
            # Index for job status queries
            """
            CREATE INDEX IF NOT EXISTS idx_scrapejob_status_created 
            ON scrapejob(status, created_at DESC);
            """,
            
            # Index for job website lookups
            """
            CREATE INDEX IF NOT EXISTS idx_scrapejob_website_status 
            ON scrapejob(website_id, status);
            """,
            
            # Index for opportunity queries
            """
            CREATE INDEX IF NOT EXISTS idx_opportunity_website_created 
            ON opportunity(website_id, created_at DESC);
            """
        ]
        
        with Session(engine) as session:
            for query in index_queries:
                try:
                    session.exec(text(query))
                    session.commit()
                    logger.info(f"Created index: {query.strip()[:50]}...")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
                    session.rollback()
    
    @staticmethod
    def analyze_tables():
        """Run ANALYZE on tables for better query planning."""
        tables = ['website', 'scrapejob', 'opportunity']
        
        with Session(engine) as session:
            for table in tables:
                try:
                    session.exec(text(f"ANALYZE {table};"))
                    session.commit()
                    logger.info(f"Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"Table analysis failed: {e}")
                    session.rollback()


class ConnectionPooling:
    """Database connection pooling configuration."""
    
    @staticmethod
    def configure_pool():
        """Configure optimal connection pool settings."""
        # This should be done during engine creation
        # Included here for reference
        pool_config = {
            "pool_size": 10,  # Number of connections to maintain
            "max_overflow": 20,  # Maximum overflow connections
            "pool_timeout": 30,  # Timeout for getting connection
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Test connections before use
        }
        return pool_config


class APIOptimizations:
    """API-specific optimizations."""
    
    @staticmethod
    def get_pagination_params(
        page: int = 1,
        per_page: int = 50,
        max_per_page: int = 100
    ) -> tuple[int, int]:
        """Calculate optimized pagination parameters."""
        # Ensure reasonable limits
        per_page = min(per_page, max_per_page)
        per_page = max(per_page, 1)
        
        page = max(page, 1)
        
        offset = (page - 1) * per_page
        
        return offset, per_page
    
    @staticmethod
    def format_response_minimal(data: Any) -> Dict[str, Any]:
        """Format response with minimal overhead."""
        return {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "count": len(data) if isinstance(data, list) else 1
        }


# Initialize optimizations on module import
def initialize_optimizations():
    """Initialize all performance optimizations."""
    try:
        # Create database indexes
        DatabaseOptimizations.create_indexes()
        
        # Analyze tables for better query planning
        DatabaseOptimizations.analyze_tables()
        
        # Warm up caches
        asyncio.create_task(PerformanceOptimizer.warmup_cache())
        
        logger.info("Performance optimizations initialized")
    except Exception as e:
        logger.error(f"Failed to initialize optimizations: {e}")


# Export optimized functions for use in API endpoints
__all__ = [
    'PerformanceOptimizer',
    'DatabaseOptimizations',
    'ConnectionPooling',
    'APIOptimizations',
    'initialize_optimizations'
]