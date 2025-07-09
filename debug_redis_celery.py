#!/usr/bin/env python3
"""
Comprehensive debug script for Redis and Celery connections.
Tests the external Redis connection and Celery worker functionality.
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# External Redis URL from Render
REDIS_URL = "rediss://red-d1hljoruibrs73fe7vkg:GVMeswpIbCXw0hrpegTULbgosBs53wSL@oregon-keyvalue.render.com:6379"

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def test_redis_connection():
    """Test basic Redis connection."""
    print_section("1. Testing Redis Connection")
    
    try:
        import redis
        from redis import Redis
        
        # Parse the Redis URL
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        
        # Test basic operations
        test_key = f"test:connection:{datetime.utcnow().isoformat()}"
        test_value = "Hello from debug script!"
        
        # SET operation
        client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        print(f"✅ SET operation successful: {test_key}")
        
        # GET operation
        retrieved = client.get(test_key)
        print(f"✅ GET operation successful: {retrieved}")
        
        # PING
        pong = client.ping()
        print(f"✅ PING successful: {pong}")
        
        # Get server info
        info = client.info()
        print(f"\n📊 Redis Server Info:")
        print(f"   - Version: {info.get('redis_version', 'Unknown')}")
        print(f"   - Connected clients: {info.get('connected_clients', 'Unknown')}")
        print(f"   - Used memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"   - Uptime: {info.get('uptime_in_days', 'Unknown')} days")
        
        # Clean up
        client.delete(test_key)
        client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        logger.exception("Redis connection error")
        return False


def check_celery_queues():
    """Check Celery queues in Redis."""
    print_section("2. Checking Celery Queues")
    
    try:
        import redis
        from redis import Redis
        
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        
        # Common Celery queue patterns
        queue_patterns = [
            "celery",
            "_kombu.binding.celery",
            "celery.pidbox",
            "_kombu.binding.celeryev",
            "_kombu.binding.celery.pidbox"
        ]
        
        print("🔍 Searching for Celery-related keys...\n")
        
        all_keys = []
        for pattern in queue_patterns:
            keys = client.keys(f"*{pattern}*")
            if keys:
                all_keys.extend(keys)
                print(f"Found keys matching '{pattern}':")
                for key in keys[:5]:  # Show first 5
                    print(f"   - {key}")
                if len(keys) > 5:
                    print(f"   ... and {len(keys) - 5} more")
        
        if not all_keys:
            print("⚠️  No Celery-related keys found in Redis")
        
        # Check specific queue lengths
        print("\n📊 Queue Lengths:")
        for queue_name in ["celery", "default", "high", "low"]:
            try:
                length = client.llen(queue_name)
                if length > 0:
                    print(f"   - {queue_name}: {length} messages")
            except:
                pass
        
        # Check for any tasks
        print("\n📋 Recent Task Keys:")
        task_keys = client.keys("celery-task-meta-*")[:10]
        for key in task_keys:
            try:
                task_data = client.get(key)
                if task_data:
                    data = json.loads(task_data)
                    print(f"   - Task ID: {key.split('-')[-1][:8]}...")
                    print(f"     Status: {data.get('status', 'Unknown')}")
                    print(f"     Task: {data.get('task', 'Unknown')}")
            except:
                pass
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to check Celery queues: {str(e)}")
        logger.exception("Celery queue check error")
        return False


def test_celery_worker():
    """Test starting a Celery worker with the production Redis URL."""
    print_section("3. Testing Celery Worker Connection")
    
    try:
        # Set environment variable for Redis URL
        os.environ['REDIS_URL'] = REDIS_URL
        
        # Add backend directory to Python path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        from celery import Celery
        
        # Create a test Celery app
        app = Celery(
            'hoistscout_debug',
            broker=REDIS_URL,
            backend=REDIS_URL
        )
        
        # Configure the app
        app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            broker_connection_retry_on_startup=True,
            broker_connection_retry=True,
            broker_connection_max_retries=3,
        )
        
        print("🔧 Celery app configured")
        print(f"   - Broker: {REDIS_URL[:50]}...")
        print(f"   - Backend: {REDIS_URL[:50]}...")
        
        # Test connection
        print("\n🔌 Testing broker connection...")
        conn = app.connection()
        conn.ensure_connection(max_retries=3)
        print("✅ Broker connection successful!")
        
        # Get worker stats
        print("\n📊 Active Workers:")
        inspect = app.control.inspect()
        active = inspect.active()
        
        if active:
            for worker_name, tasks in active.items():
                print(f"   - Worker: {worker_name}")
                print(f"     Active tasks: {len(tasks)}")
        else:
            print("   ⚠️  No active workers found")
        
        # Check registered tasks
        print("\n📋 Registered Tasks:")
        registered = inspect.registered()
        if registered:
            for worker_name, tasks in registered.items():
                print(f"   - Worker: {worker_name}")
                for task in tasks[:5]:
                    print(f"     • {task}")
                if len(tasks) > 5:
                    print(f"     ... and {len(tasks) - 5} more")
        else:
            print("   ⚠️  No registered tasks found")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery worker test failed: {str(e)}")
        logger.exception("Celery worker test error")
        return False


def send_test_task():
    """Send a test task to Celery."""
    print_section("4. Sending Test Task")
    
    try:
        os.environ['REDIS_URL'] = REDIS_URL
        
        from celery import Celery
        
        app = Celery(
            'hoistscout_debug',
            broker=REDIS_URL,
            backend=REDIS_URL
        )
        
        # Define a simple test task
        @app.task(name='debug.test_task')
        def test_task(x, y):
            return x + y
        
        print("📤 Sending test task (2 + 3)...")
        result = test_task.delay(2, 3)
        print(f"✅ Task sent! Task ID: {result.id}")
        
        # Try to get result (will timeout if no worker is processing)
        print("\n⏳ Waiting for result (5 seconds)...")
        try:
            value = result.get(timeout=5)
            print(f"✅ Task completed! Result: {value}")
        except Exception as timeout_error:
            print(f"⏱️  Task not processed (no worker running?): {timeout_error}")
            print("\n💡 To process this task, start a worker with:")
            print("   celery -A app.worker worker --loglevel=info")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test task: {str(e)}")
        logger.exception("Test task error")
        return False


def check_hoistscout_tasks():
    """Check for HoistScout-specific tasks in the queue."""
    print_section("5. Checking HoistScout Tasks")
    
    try:
        import redis
        from redis import Redis
        
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        
        # Look for HoistScout-specific patterns
        patterns = [
            "*scrape*",
            "*website*",
            "*opportunity*",
            "*hoistscout*",
            "*pdf*"
        ]
        
        print("🔍 Searching for HoistScout-related tasks...\n")
        
        found_tasks = False
        for pattern in patterns:
            keys = client.keys(f"*{pattern}*")
            if keys:
                found_tasks = True
                print(f"📋 Found keys matching '{pattern}':")
                for key in keys[:3]:
                    print(f"   - {key}")
                    try:
                        # Try to get value if it's a string
                        value = client.get(key)
                        if value and len(value) < 200:
                            print(f"     Value: {value[:100]}...")
                    except:
                        # Might be a different data type
                        pass
                if len(keys) > 3:
                    print(f"   ... and {len(keys) - 3} more")
        
        if not found_tasks:
            print("ℹ️  No HoistScout-specific tasks found in queue")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to check HoistScout tasks: {str(e)}")
        logger.exception("HoistScout task check error")
        return False


def main():
    """Run all debug tests."""
    print("\n🚀 HoistScout Redis/Celery Debug Script")
    print(f"📅 {datetime.utcnow().isoformat()}")
    print(f"🔗 Redis URL: {REDIS_URL[:50]}...")
    
    results = []
    
    # Run all tests
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Celery Queues", check_celery_queues()))
    results.append(("Celery Worker", test_celery_worker()))
    results.append(("Test Task", send_test_task()))
    results.append(("HoistScout Tasks", check_hoistscout_tasks()))
    
    # Summary
    print_section("Summary")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Recommendations
    print_section("Recommendations")
    
    if not results[0][1]:  # Redis connection failed
        print("🔧 Fix Redis connection:")
        print("   1. Check if Redis URL is correct")
        print("   2. Verify Redis server is running")
        print("   3. Check network connectivity")
    
    if results[0][1] and not results[2][1]:  # Redis OK but Celery failed
        print("🔧 Start Celery worker:")
        print("   1. cd backend")
        print("   2. export REDIS_URL='" + REDIS_URL + "'")
        print("   3. celery -A app.worker worker --loglevel=info")
    
    if not any(r[1] for r in results[3:]):  # No tasks found
        print("📝 No tasks in queue. To create tasks:")
        print("   1. Start the FastAPI application")
        print("   2. Trigger a website scraping job")
        print("   3. Or run: python -c 'from app.worker import scrape_website_task; scrape_website_task.delay(1)'")
    
    print("\n✨ Debug script completed!")


if __name__ == "__main__":
    main()