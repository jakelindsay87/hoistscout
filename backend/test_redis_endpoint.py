#!/usr/bin/env python3
"""Test the Redis health endpoint locally"""
import httpx
import json
import sys
import asyncio


async def test_redis_endpoint():
    """Test the /api/health/redis endpoint"""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/health/redis"
    
    print(f"Testing Redis health endpoint: {endpoint}")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, timeout=30.0)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
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
                else:
                    print(f"Error: {data['connection']['error']}")
                
                return data
            else:
                print(f"Error: {response.text}")
                return None
                
    except Exception as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    result = asyncio.run(test_redis_endpoint())
    
    # Exit with proper code
    if result and result.get('healthy'):
        sys.exit(0)
    else:
        sys.exit(1)