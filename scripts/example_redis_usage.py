#!/usr/bin/env python3
"""
Example Redis Usage Script

This script demonstrates how to use the Redis URL obtained from setup_upstash_redis.py
with HoistScout's backend services.

Usage:
    python example_redis_usage.py <REDIS_URL>
"""

import os
import sys
import redis
import json
from datetime import datetime


def test_redis_connection(redis_url: str):
    """Test basic Redis operations"""
    print(f"🔍 Testing Redis connection...")
    
    try:
        # Create Redis client
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        print("✅ Connected to Redis successfully!")
        
        # Get server info
        info = r.info()
        print(f"\n📊 Redis Server Info:")
        print(f"  • Version: {info.get('redis_version', 'N/A')}")
        print(f"  • Memory Used: {info.get('used_memory_human', 'N/A')}")
        print(f"  • Connected Clients: {info.get('connected_clients', 'N/A')}")
        
        return r
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def demonstrate_hoistscout_usage(r: redis.Redis):
    """Demonstrate HoistScout-specific Redis usage patterns"""
    print("\n🚀 HoistScout Redis Usage Examples:")
    print("-" * 50)
    
    # 1. Job Queue Example
    print("\n1️⃣ Job Queue Pattern:")
    job_id = f"job_{datetime.now().timestamp()}"
    job_data = {
        "id": job_id,
        "website_url": "https://example.com",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    # Store job
    r.hset(f"hoistscout:job:{job_id}", mapping=job_data)
    r.lpush("hoistscout:job:queue", job_id)
    print(f"  ✅ Created job: {job_id}")
    
    # Retrieve job
    stored_job = r.hgetall(f"hoistscout:job:{job_id}")
    print(f"  ✅ Retrieved job: {stored_job}")
    
    # 2. Caching Example
    print("\n2️⃣ Caching Pattern:")
    cache_key = "hoistscout:cache:website:example.com"
    cache_data = {
        "title": "Example Domain",
        "scraped_at": datetime.now().isoformat()
    }
    
    # Cache with expiration
    r.setex(cache_key, 3600, json.dumps(cache_data))  # 1 hour TTL
    print(f"  ✅ Cached website data with 1-hour TTL")
    
    # Retrieve from cache
    cached = r.get(cache_key)
    if cached:
        print(f"  ✅ Retrieved from cache: {json.loads(cached)}")
    
    # 3. Rate Limiting Example
    print("\n3️⃣ Rate Limiting Pattern:")
    rate_limit_key = "hoistscout:ratelimit:api:user123"
    
    # Increment counter
    current = r.incr(rate_limit_key)
    if current == 1:
        r.expire(rate_limit_key, 60)  # Reset every minute
    
    print(f"  ✅ API calls this minute: {current}")
    
    # 4. Session Storage Example
    print("\n4️⃣ Session Storage Pattern:")
    session_id = "sess_abc123"
    session_data = {
        "user_id": "user123",
        "login_time": datetime.now().isoformat()
    }
    
    # Store session
    r.hset(f"hoistscout:session:{session_id}", mapping=session_data)
    r.expire(f"hoistscout:session:{session_id}", 86400)  # 24 hours
    print(f"  ✅ Created session with 24-hour TTL")
    
    # 5. Pub/Sub Example (for real-time updates)
    print("\n5️⃣ Pub/Sub Pattern:")
    channel = "hoistscout:updates"
    message = {"event": "job_completed", "job_id": job_id}
    
    # Publish message
    subscribers = r.publish(channel, json.dumps(message))
    print(f"  ✅ Published update to {subscribers} subscribers")
    
    # Cleanup demo data
    print("\n🧹 Cleaning up demo data...")
    r.delete(
        f"hoistscout:job:{job_id}",
        cache_key,
        rate_limit_key,
        f"hoistscout:session:{session_id}"
    )
    r.lrem("hoistscout:job:queue", 1, job_id)
    print("  ✅ Demo data cleaned up")


def show_celery_config(redis_url: str):
    """Show how to configure Celery with the Redis URL"""
    print("\n📝 Celery Configuration Example:")
    print("-" * 50)
    print("```python")
    print("# In your Celery configuration:")
    print(f"CELERY_BROKER_URL = '{redis_url}'")
    print(f"CELERY_RESULT_BACKEND = '{redis_url}'")
    print("")
    print("# Additional recommended settings:")
    print("CELERY_ACCEPT_CONTENT = ['json']")
    print("CELERY_TASK_SERIALIZER = 'json'")
    print("CELERY_RESULT_SERIALIZER = 'json'")
    print("CELERY_TIMEZONE = 'UTC'")
    print("```")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # Try to get from environment
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            print("❌ Error: Please provide REDIS_URL as argument or set REDIS_URL environment variable")
            print("Usage: python example_redis_usage.py <REDIS_URL>")
            sys.exit(1)
    else:
        redis_url = sys.argv[1]
    
    print("🚀 HoistScout Redis Usage Examples")
    print("="*50)
    
    # Test connection
    r = test_redis_connection(redis_url)
    if not r:
        sys.exit(1)
    
    # Demonstrate usage patterns
    demonstrate_hoistscout_usage(r)
    
    # Show Celery configuration
    show_celery_config(redis_url)
    
    print("\n✅ All examples completed successfully!")
    print("\n💡 Next steps:")
    print("  1. Use the Redis URL in your Render environment variables")
    print("  2. Configure Celery to use Redis as broker and backend")
    print("  3. Implement caching and session management patterns")


if __name__ == "__main__":
    main()