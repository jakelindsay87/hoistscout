from celery import Celery
from celery.schedules import crontab
import asyncio
from typing import Dict, Any
from datetime import datetime

from .config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "hoistscout",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker"]
)

# Make celery_app available as 'worker' for the celery command
worker = celery_app

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "scrape-all-active-websites": {
        "task": "app.worker.scrape_all_active_websites",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    "cleanup-old-jobs": {
        "task": "app.worker.cleanup_old_jobs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}


@celery_app.task(bind=True, max_retries=3)
def scrape_website_task(self, website_id: int):
    """Scrape a single website."""
    try:
        # Run async scraping in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from .database import AsyncSessionLocal
        from .models.website import Website
        from .models.job import ScrapingJob, JobStatus
        from .models.opportunity import Opportunity
        from sqlalchemy import select
        
        async def run_scraping():
            async with AsyncSessionLocal() as db:
                # Get website
                stmt = select(Website).where(Website.id == website_id)
                result = await db.execute(stmt)
                website = result.scalar_one_or_none()
                
                if not website:
                    raise ValueError(f"Website {website_id} not found")
                
                # Update job status
                job_id = self.request.id
                if job_id:
                    job_stmt = select(ScrapingJob).where(ScrapingJob.id == job_id)
                    job_result = await db.execute(job_stmt)
                    job = job_result.scalar_one_or_none()
                    if job:
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.utcnow()
                        await db.commit()
                
                # Import and run scraper (lazy import to avoid startup issues)
                try:
                    from .core import BulletproofTenderScraper
                    scraper = BulletproofTenderScraper()
                    result = await scraper.scrape_website(website)
                except ImportError as e:
                    # If scraper not available, return empty result
                    from datetime import datetime
                    result = type('obj', (object,), {
                        'opportunities': [],
                        'success': False,
                        'error_message': f"Scraper not available: {str(e)}"
                    })
                
                # Save opportunities
                for opp_data in result.opportunities:
                    opportunity = Opportunity(
                        website_id=website_id,
                        title=opp_data.get("title"),
                        description=opp_data.get("description"),
                        deadline=opp_data.get("deadline"),
                        value=opp_data.get("value"),
                        currency=opp_data.get("currency", "USD"),
                        reference_number=opp_data.get("reference_number"),
                        source_url=opp_data.get("source_url"),
                        categories=opp_data.get("categories", []),
                        location=opp_data.get("location"),
                        extracted_data=opp_data,
                        confidence_score=opp_data.get("confidence_score", 1.0)
                    )
                    db.add(opportunity)
                
                # Update job status
                if job:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    job.stats = result.stats
                
                await db.commit()
                
                return result.stats
        
        result = loop.run_until_complete(run_scraping())
        return result
        
    except Exception as exc:
        # Log error and retry
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task
def process_pdf_task(document_id: int):
    """Process a PDF document."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from .database import AsyncSessionLocal
        from .models.opportunity import Document
        from sqlalchemy import select
        
        async def run_processing():
            async with AsyncSessionLocal() as db:
                # Get document
                stmt = select(Document).where(Document.id == document_id)
                result = await db.execute(stmt)
                document = result.scalar_one_or_none()
                
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                # Process PDF (lazy import)
                try:
                    from .core import PDFProcessor
                    processor = PDFProcessor()
                    # Implement PDF processing logic
                except ImportError as e:
                    # PDF processing not available
                    pass
                
                await db.commit()
        
        loop.run_until_complete(run_processing())
        
    except Exception as exc:
        raise


@celery_app.task
def scrape_all_active_websites():
    """Periodic task to scrape all active websites."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    from .database import AsyncSessionLocal
    from .models.website import Website
    from sqlalchemy import select
    
    async def run_task():
        async with AsyncSessionLocal() as db:
            stmt = select(Website).where(Website.is_active == True)
            result = await db.execute(stmt)
            websites = result.scalars().all()
            
            for website in websites:
                scrape_website_task.delay(website.id)
    
    loop.run_until_complete(run_task())


@celery_app.task
def cleanup_old_jobs():
    """Clean up old completed jobs."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    from .database import AsyncSessionLocal
    from .models.job import ScrapingJob, JobStatus
    from sqlalchemy import select, and_
    from datetime import datetime, timedelta
    
    async def run_cleanup():
        async with AsyncSessionLocal() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            stmt = select(ScrapingJob).where(
                and_(
                    ScrapingJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                    ScrapingJob.created_at < cutoff_date
                )
            )
            result = await db.execute(stmt)
            old_jobs = result.scalars().all()
            
            for job in old_jobs:
                await db.delete(job)
            
            await db.commit()
    
    loop.run_until_complete(run_cleanup())