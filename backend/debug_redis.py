#!/usr/bin/env python3
"""Debug Redis to see what's actually happening"""
import os
import redis
import json

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

print("Redis Debugging Tool")
print("=" * 60)
print(f"Connecting to: {REDIS_URL}")

try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis")
    
    # Check all keys
    print("\nAll Redis keys:")
    all_keys = r.keys('*')
    for key in sorted(all_keys):
        key_type = r.type(key)
        print(f"  {key} ({key_type})")
    
    # Check Celery-specific keys
    print("\nCelery queues:")
    celery_queues = [k for k in all_keys if 'celery' in k.lower()]
    for queue in celery_queues:
        if r.type(queue) == 'list':
            length = r.llen(queue)
            print(f"  {queue}: {length} tasks")
            if length > 0:
                # Show first task
                task_data = r.lindex(queue, 0)
                try:
                    task = json.loads(task_data)
                    print(f"    First task ID: {task.get('headers', {}).get('id', 'Unknown')}")
                    print(f"    Task name: {task.get('headers', {}).get('task', 'Unknown')}")
                except:
                    print(f"    Raw task: {task_data[:100]}...")
    
    # Check specific queue
    print("\nChecking 'celery' queue specifically:")
    queue_length = r.llen('celery')
    print(f"  Length: {queue_length}")
    
    if queue_length > 0:
        print("\n  Tasks in queue:")
        for i in range(min(5, queue_length)):
            task_data = r.lindex('celery', i)
            try:
                task = json.loads(task_data)
                task_id = task.get('headers', {}).get('id', 'Unknown')
                task_name = task.get('headers', {}).get('task', 'Unknown')
                args = task.get('body', {}).get('args', [])
                print(f"    Task {i+1}: ID={task_id}, Name={task_name}, Args={args}")
            except:
                print(f"    Task {i+1}: Could not parse")
    
    # Check for any unacked tasks
    print("\nChecking unacknowledged tasks:")
    unacked = r.hgetall('unacked')
    if unacked:
        print(f"  Found {len(unacked)} unacked tasks")
        for key, value in list(unacked.items())[:5]:
            print(f"    {key}: {value[:100]}...")
    else:
        print("  No unacknowledged tasks")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()