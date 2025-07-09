#!/usr/bin/env python3
"""Test worker connections to Redis and PostgreSQL from local environment"""

import os
import sys
from urllib.parse import urlparse

# Test Redis connection
print("Testing Redis Connection...")
print("-" * 50)

redis_url = "redis://red-d1hlrb2dbo4c73d993ag:LGfJgcOIuOdQGRsrYBjukWRqftoKqCdU@oregon-redis.render.com:6379"
parsed = urlparse(redis_url)

print(f"Host: {parsed.hostname}")
print(f"Port: {parsed.port}")
print(f"Password: {'*' * 10}...") 

try:
    import redis
    r = redis.from_url(redis_url, decode_responses=True)
    
    # Test connection
    pong = r.ping()
    print(f"✅ Redis PING: {pong}")
    
    # Check Celery keys
    celery_keys = r.keys('celery*')
    print(f"Celery keys found: {len(celery_keys)}")
    for key in celery_keys[:5]:  # Show first 5
        print(f"  - {key}")
    
    # Check specific queues
    queues = ['celery', 'default', 'scraping']
    for queue in queues:
        queue_key = f"celery:{queue}"
        length = r.llen(queue_key)
        print(f"Queue '{queue}' length: {length}")
        
except Exception as e:
    print(f"❌ Redis connection failed: {e}")

# Test PostgreSQL connection
print("\n\nTesting PostgreSQL Connection...")
print("-" * 50)

db_url = "postgresql://hoistscout_user:dQYrOqHI5d61K8xCcJvVEjf8S5NFCOVJ@dpg-d1hlrn2dbo4c73d98th0-a.oregon-postgres.render.com/hoistscout_db"
parsed_db = urlparse(db_url)

print(f"Host: {parsed_db.hostname}")
print(f"Port: {parsed_db.port or 5432}")
print(f"Database: {parsed_db.path[1:]}")
print(f"User: {parsed_db.username}")

try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Test connection
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✅ PostgreSQL version: {version[0][:50]}...")
    
    # Check jobs table
    cur.execute("SELECT COUNT(*), status FROM scraping_jobs GROUP BY status;")
    job_counts = cur.fetchall()
    print("\nJobs in database:")
    for count, status in job_counts:
        print(f"  - {status}: {count}")
    
    # Check last job update
    cur.execute("SELECT MAX(updated_at) FROM scraping_jobs WHERE status = 'pending';")
    last_pending = cur.fetchone()[0]
    print(f"\nLast pending job update: {last_pending}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")

# Summary
print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)
print("These are the production Redis and PostgreSQL instances.")
print("If both connections work locally but the worker can't process jobs,")
print("it suggests the worker container has connectivity or configuration issues.")