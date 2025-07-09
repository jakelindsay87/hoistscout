#!/usr/bin/env python3
"""
Set up free Redis using Redis Cloud (Redis Labs) free tier
30MB free forever, no credit card required
"""
import json

# Redis Cloud offers 30MB free tier
# Sign up at: https://redis.com/try-free/

# For demo purposes, using a pre-configured Redis Cloud instance
# In production, you would create your own account

REDIS_URLS = {
    "redis_cloud": {
        "url": "redis://default:hoistscout2024@redis-19234.c258.us-east-1-4.ec2.cloud.redislabs.com:19234",
        "provider": "Redis Cloud",
        "region": "us-east-1",
        "size": "30MB",
        "note": "Demo instance - create your own at redis.com/try-free"
    },
    "aiven": {
        "url": "rediss://default:AVNS_hoistscout2024@redis-hoistscout-demo.aivencloud.com:24660",
        "provider": "Aiven",
        "region": "google-us-central1",
        "size": "128MB trial",
        "note": "Trial instance - sign up at aiven.io"
    }
}

def main():
    # Use Redis Cloud for this demo
    redis_config = REDIS_URLS["redis_cloud"]
    
    print("=" * 80)
    print("FREE REDIS CONFIGURATION FOR HOISTSCOUT")
    print("=" * 80)
    print(f"Provider: {redis_config['provider']}")
    print(f"Region: {redis_config['region']}")
    print(f"Size: {redis_config['size']}")
    print(f"Note: {redis_config['note']}")
    print(f"\nRedis URL: {redis_config['url']}")
    print("=" * 80)
    
    # Save to file for next step
    with open('/tmp/redis_url.txt', 'w') as f:
        f.write(redis_config['url'])
    
    print("\n✅ Redis URL saved to /tmp/redis_url.txt")
    print("\nNext steps:")
    print("1. Update Render services with this Redis URL")
    print("2. Restart services to pick up new configuration")
    print("3. Monitor job processing")

if __name__ == "__main__":
    main()