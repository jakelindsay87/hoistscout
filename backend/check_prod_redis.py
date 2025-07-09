#!/usr/bin/env python3
"""
Script to check Redis queue contents for Celery tasks.
This helps diagnose issues with tasks not being processed in production.
"""

import os
import sys
import json
from datetime import datetime
from urllib.parse import urlparse
import redis
import argparse


def parse_redis_url(redis_url):
    """Parse Redis URL and return connection parameters."""
    parsed = urlparse(redis_url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 6379,
        'password': parsed.password,
        'db': int(parsed.path.lstrip('/')) if parsed.path else 0,
        'decode_responses': True
    }


def get_task_info(task_body):
    """Extract readable information from a Celery task."""
    try:
        task_data = json.loads(task_body)
        return {
            'task': task_data.get('task', 'Unknown'),
            'id': task_data.get('id', 'Unknown'),
            'args': task_data.get('args', []),
            'kwargs': task_data.get('kwargs', {}),
            'eta': task_data.get('eta'),
            'retries': task_data.get('retries', 0),
        }
    except:
        return {'raw': task_body}


def check_redis_queues(redis_url):
    """Check Redis for Celery queue contents."""
    print(f"\n🔍 Connecting to Redis...")
    print(f"   URL: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
    
    try:
        # Connect to Redis
        conn_params = parse_redis_url(redis_url)
        r = redis.Redis(**conn_params)
        
        # Test connection
        r.ping()
        print("✅ Successfully connected to Redis\n")
        
        # Get all keys
        print("📋 All Redis keys:")
        all_keys = r.keys('*')
        celery_keys = [k for k in all_keys if 'celery' in k.lower() or 'kombu' in k.lower()]
        
        if not all_keys:
            print("   ⚠️  No keys found in Redis")
        else:
            print(f"   Total keys: {len(all_keys)}")
            print(f"   Celery-related keys: {len(celery_keys)}")
            for key in celery_keys[:20]:  # Show first 20 celery keys
                print(f"   - {key}")
            if len(celery_keys) > 20:
                print(f"   ... and {len(celery_keys) - 20} more")
        
        print("\n" + "="*60 + "\n")
        
        # Check specific Celery queues
        queue_names = ['celery', 'default', 'high_priority', 'low_priority']
        
        for queue_name in queue_names:
            print(f"📦 Queue: {queue_name}")
            
            # Check different possible key patterns
            queue_keys = [
                f"_kombu.binding.{queue_name}",
                f"celery.{queue_name}",
                queue_name,
                f"{queue_name}.priority.0",
                f"{queue_name}.priority.1",
                f"{queue_name}.priority.2",
                f"{queue_name}.priority.3",
                f"{queue_name}.priority.4",
                f"{queue_name}.priority.5",
                f"{queue_name}.priority.6",
                f"{queue_name}.priority.7",
                f"{queue_name}.priority.8",
                f"{queue_name}.priority.9",
            ]
            
            total_tasks = 0
            for key in queue_keys:
                try:
                    # Try as a list
                    queue_length = r.llen(key)
                    if queue_length > 0:
                        print(f"   Found {queue_length} tasks in key: {key}")
                        total_tasks += queue_length
                        
                        # Show first few tasks
                        tasks = r.lrange(key, 0, 4)
                        for i, task in enumerate(tasks):
                            print(f"   Task {i+1}: {get_task_info(task)}")
                        
                        if queue_length > 5:
                            print(f"   ... and {queue_length - 5} more tasks")
                except:
                    # Try as a zset (sorted set)
                    try:
                        queue_length = r.zcard(key)
                        if queue_length > 0:
                            print(f"   Found {queue_length} tasks in sorted set: {key}")
                            total_tasks += queue_length
                            
                            # Show first few tasks
                            tasks = r.zrange(key, 0, 4)
                            for i, task in enumerate(tasks):
                                print(f"   Task {i+1}: {get_task_info(task)}")
                            
                            if queue_length > 5:
                                print(f"   ... and {queue_length - 5} more tasks")
                    except:
                        pass
            
            if total_tasks == 0:
                print(f"   ✅ No pending tasks in {queue_name} queue")
            else:
                print(f"   ⚠️  Total tasks in {queue_name}: {total_tasks}")
            
            print()
        
        # Check for unacknowledged tasks
        print("\n" + "="*60 + "\n")
        print("🔍 Checking for unacknowledged tasks...")
        unacked_keys = [k for k in all_keys if 'unacked' in k.lower()]
        
        if unacked_keys:
            print(f"   Found {len(unacked_keys)} unacked key(s):")
            for key in unacked_keys:
                try:
                    # Could be hash, zset, or set
                    size = r.hlen(key) or r.zcard(key) or r.scard(key)
                    if size > 0:
                        print(f"   - {key}: {size} unacked tasks")
                except:
                    print(f"   - {key}: (couldn't determine size)")
        else:
            print("   ✅ No unacknowledged task keys found")
        
        # Check Celery task results
        print("\n" + "="*60 + "\n")
        print("📊 Checking Celery task results...")
        result_keys = [k for k in all_keys if k.startswith('celery-task-meta-')]
        
        if result_keys:
            print(f"   Found {len(result_keys)} task result(s)")
            # Show a few recent results
            for key in result_keys[:5]:
                try:
                    result = r.get(key)
                    if result:
                        result_data = json.loads(result)
                        print(f"   - Task {result_data.get('task_id', 'Unknown')}:")
                        print(f"     Status: {result_data.get('status', 'Unknown')}")
                        print(f"     Task: {result_data.get('task', 'Unknown')}")
                        if result_data.get('traceback'):
                            print(f"     Error: {result_data.get('traceback', '')[:100]}...")
                except:
                    pass
            
            if len(result_keys) > 5:
                print(f"   ... and {len(result_keys) - 5} more results")
        else:
            print("   No task results found")
        
        # Show Redis info
        print("\n" + "="*60 + "\n")
        print("ℹ️  Redis Server Info:")
        info = r.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'Unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"   Total keys: {info.get('db0', {}).get('keys', 'Unknown')}")
        
    except redis.ConnectionError as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("\nMake sure:")
        print("1. The Redis URL is correct")
        print("2. Redis is running and accessible")
        print("3. Network/firewall allows the connection")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description='Check Redis queue contents for Celery tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable (recommended for production)
  export REDIS_URL="redis://:password@host:port/0"
  python check_prod_redis.py

  # Using command line argument
  python check_prod_redis.py "redis://:password@host:port/0"

  # Using local Redis
  python check_prod_redis.py "redis://localhost:6379/0"
        """
    )
    
    parser.add_argument(
        'redis_url',
        nargs='?',
        help='Redis URL (can also use REDIS_URL environment variable)'
    )
    
    args = parser.parse_args()
    
    # Get Redis URL from argument or environment
    redis_url = args.redis_url or os.environ.get('REDIS_URL')
    
    if not redis_url:
        print("❌ Error: No Redis URL provided")
        print("\nPlease provide Redis URL either:")
        print("1. As a command line argument:")
        print("   python check_prod_redis.py 'redis://...'")
        print("\n2. Or as an environment variable:")
        print("   export REDIS_URL='redis://...'")
        print("   python check_prod_redis.py")
        sys.exit(1)
    
    print(f"🚀 Redis Queue Inspector")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_redis_queues(redis_url)


if __name__ == '__main__':
    main()