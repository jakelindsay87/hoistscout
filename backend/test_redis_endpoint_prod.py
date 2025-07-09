#!/usr/bin/env python3
"""Test the Redis health endpoint in production"""
import httpx
import json
import sys
import asyncio
import os


async def test_redis_endpoint(base_url):
    """Test the /api/health/redis endpoint"""
    endpoint = f"{base_url}/api/health/redis"
    
    print(f"Testing Redis health endpoint: {endpoint}")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, timeout=30.0)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("\nResponse (formatted):")
                print(json.dumps(data, indent=2))
                
                # Summary
                print("\n" + "=" * 60)
                print("SUMMARY:")
                print(f"Redis Connection: {data['connection']['status']}")
                print(f"Overall Health: {'✅ HEALTHY' if data['healthy'] else '❌ UNHEALTHY'}")
                
                if data['connection']['status'] == 'connected':
                    print(f"Latency: {data['connection']['latency_ms']}ms")
                    print(f"Redis Version: {data['redis_info'].get('redis_version', 'unknown')}")
                    print(f"Total Celery Tasks: {data['celery']['total_tasks']}")
                    
                    # Show queue details
                    if data['celery']['queues']:
                        print("\nCelery Queues:")
                        for queue_name, queue_info in data['celery']['queues'].items():
                            print(f"  {queue_name}: {queue_info['length']} tasks")
                            if queue_info['tasks']:
                                for task in queue_info['tasks'][:2]:
                                    if 'error' not in task:
                                        print(f"    - {task['name']} (ID: {task['id'][:8]}...)")
                else:
                    print(f"Error: {data['connection']['error']}")
                    if 'traceback' in data['connection']:
                        print("\nTraceback:")
                        print(data['connection']['traceback'])
                
                return data
            else:
                print(f"Error Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"Request failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Get production URL from command line or environment
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = os.environ.get('HOISTSCOUT_API_URL', 'https://hoistscout-backend.onrender.com')
    
    print(f"Using API URL: {base_url}")
    
    result = asyncio.run(test_redis_endpoint(base_url))
    
    # Exit with proper code
    if result and result.get('healthy'):
        sys.exit(0)
    else:
        sys.exit(1)