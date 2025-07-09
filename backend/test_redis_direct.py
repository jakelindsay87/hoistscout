#!/usr/bin/env python3
"""
Test Redis connection directly without Celery.
"""

import os
import sys
import redis
from urllib.parse import urlparse

print("=" * 80)
print("DIRECT REDIS CONNECTION TEST")
print("=" * 80)

# Get Redis URL
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
print(f"Redis URL: {redis_url}")

try:
    # Parse Redis URL
    parsed = urlparse(redis_url)
    print(f"\nParsed connection details:")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port or 6379}")
    print(f"  DB: {parsed.path.lstrip('/') or '0'}")
    print(f"  Password: {'***' if parsed.password else 'None'}")
    
    # Create Redis client
    print("\nCreating Redis client...")
    client = redis.from_url(redis_url)
    
    # Test connection
    print("Testing connection...")
    response = client.ping()
    print(f"✓ PING response: {response}")
    
    # Test basic operations
    print("\nTesting basic operations...")
    
    # SET
    key = "celery:test:key"
    value = "test_value"
    client.set(key, value)
    print(f"✓ SET {key} = {value}")
    
    # GET
    retrieved = client.get(key).decode('utf-8')
    print(f"✓ GET {key} = {retrieved}")
    
    # DELETE
    client.delete(key)
    print(f"✓ DELETE {key}")
    
    # List all keys (be careful in production!)
    print("\nListing Celery-related keys...")
    keys = client.keys("celery*")
    print(f"Found {len(keys)} Celery-related keys")
    if keys:
        for key in keys[:10]:  # Show first 10
            print(f"  - {key.decode('utf-8')}")
        if len(keys) > 10:
            print(f"  ... and {len(keys) - 10} more")
    
    print("\n✅ Redis connection is working properly!")
    
except redis.ConnectionError as e:
    print(f"\n❌ Redis connection failed: {e}")
    print("\nPossible issues:")
    print("1. Redis server is not running")
    print("2. Wrong host/port in REDIS_URL")
    print("3. Firewall blocking the connection")
    print("4. Authentication required but not provided")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)