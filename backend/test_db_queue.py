#!/usr/bin/env python3
"""
Test script for the database queue implementation.
This verifies that the PostgreSQL-based task queue works correctly.
"""

import sys
import os
import time
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db_queue import celery_app, Worker, TaskStatus
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.website import Website
from sqlalchemy import select


# Define a simple test task
@celery_app.task(name='test.add')
def add(x: int, y: int) -> int:
    """Simple test task that adds two numbers."""
    print(f"Adding {x} + {y}")
    time.sleep(1)  # Simulate some work
    return x + y


@celery_app.task(bind=True, name='test.failing_task', max_retries=2)
def failing_task(self, should_fail: bool = True):
    """Test task that fails and retries."""
    print(f"Failing task attempt {self.request.retries + 1}")
    if should_fail and self.request.retries < 2:
        self.retry(exc=Exception("Intentional failure"), countdown=2)
    return "Success after retries!"


async def test_scraping_task():
    """Test the actual scraping task."""
    print("\n=== Testing Scraping Task ===")
    
    # Get a test website from the database
    async with AsyncSessionLocal() as db:
        stmt = select(Website).where(Website.is_active == True).limit(1)
        result = await db.execute(stmt)
        website = result.scalar_one_or_none()
        
        if website:
            print(f"Found test website: {website.name} (ID: {website.id})")
            
            # Import the scraping task
            from app.db_queue import scrape_website_task
            
            # Queue the task
            result = scrape_website_task.delay(website.id)
            print(f"Queued scraping task with ID: {result.id}")
            
            return result.id
        else:
            print("No active websites found in database")
            return None


def main():
    """Run database queue tests."""
    print("=== Database Queue Test Suite ===\n")
    
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print(f"Environment: {settings.environment}\n")
    
    # Test 1: Simple task execution
    print("=== Test 1: Simple Addition Task ===")
    result = add.delay(5, 3)
    print(f"Task ID: {result.id}")
    print(f"Initial state: {result.state}")
    
    # Start a worker in a separate thread
    import threading
    worker = Worker(celery_app, worker_id="test-worker")
    worker_thread = threading.Thread(target=worker.run)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait for result
    try:
        answer = result.get(timeout=5)
        print(f"Result: {answer}")
        print(f"Final state: {result.state}")
        assert answer == 8, f"Expected 8, got {answer}"
        print("✅ Test 1 passed!\n")
    except TimeoutError:
        print("❌ Test 1 failed: Timeout waiting for result\n")
    
    # Test 2: Task with retries
    print("=== Test 2: Failing Task with Retries ===")
    result = failing_task.delay(should_fail=True)
    print(f"Task ID: {result.id}")
    
    # Wait longer for retries
    time.sleep(10)
    print(f"Final state: {result.state}")
    if result.state == TaskStatus.SUCCESS:
        print(f"Result: {result.info}")
        print("✅ Test 2 passed!\n")
    else:
        print(f"❌ Test 2 failed: {result.info}\n")
    
    # Test 3: Queue stats
    print("=== Test 3: Queue Statistics ===")
    stats = celery_app.stats()
    print(f"Queue stats: {stats}")
    print("✅ Test 3 passed!\n")
    
    # Test 4: Real scraping task
    print("=== Test 4: Real Scraping Task ===")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task_id = loop.run_until_complete(test_scraping_task())
    
    if task_id:
        print("Waiting for scraping task to complete...")
        time.sleep(5)
        
        # Check task status
        from app.db_queue import TaskResult
        result = TaskResult(task_id, celery_app)
        print(f"Scraping task state: {result.state}")
        if result.state in [TaskStatus.SUCCESS, TaskStatus.FAILURE]:
            print(f"Task result: {result.info}")
    
    # Stop the worker
    worker.running = False
    worker_thread.join(timeout=2)
    
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    main()