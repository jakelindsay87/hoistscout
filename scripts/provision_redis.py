#!/usr/bin/env python3
"""
Redis Instance Provisioning Script

This script automatically provisions a free Redis instance from multiple providers.
It supports Upstash as the primary provider with fallback options.

Usage:
    python provision_redis.py [--provider PROVIDER] [--verify] [--output-env]
    
Options:
    --provider PROVIDER  Specify provider (upstash, railway, aiven). Default: auto
    --verify            Verify the connection after provisioning
    --output-env        Output in .env format
    --json              Output in JSON format
    --help              Show this help message

Examples:
    python provision_redis.py
    python provision_redis.py --provider upstash --verify
    python provision_redis.py --output-env > redis.env
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import redis, install if not available
try:
    import redis
except ImportError:
    logger.warning("Redis package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
    import redis


@dataclass
class RedisCredentials:
    """Redis connection credentials"""
    url: str
    host: str
    port: int
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = True
    provider: str = ""
    region: str = ""
    max_connections: int = 0
    max_commands_per_second: int = 0
    max_request_size: str = ""
    max_memory: str = ""


class RedisProvider(ABC):
    """Abstract base class for Redis providers"""
    
    @abstractmethod
    def provision(self) -> Optional[RedisCredentials]:
        """Provision a new Redis instance"""
        pass
    
    @abstractmethod
    def verify_connection(self, credentials: RedisCredentials) -> bool:
        """Verify the Redis connection works"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name"""
        pass


class UpstashProvider(RedisProvider):
    """Upstash Redis provider - serverless Redis with generous free tier"""
    
    def __init__(self):
        self.api_key = os.environ.get('UPSTASH_API_KEY')
        self.email = os.environ.get('UPSTASH_EMAIL')
        self.base_url = "https://api.upstash.com/v2"
        
    def get_name(self) -> str:
        return "Upstash"
    
    def provision(self) -> Optional[RedisCredentials]:
        """
        Provision Upstash Redis instance
        
        Free tier includes:
        - 10,000 commands per day
        - 256MB storage
        - SSL/TLS encryption
        - Global replication
        """
        logger.info("Provisioning Upstash Redis instance...")
        
        # Check if credentials are available
        if not self.api_key or not self.email:
            logger.warning("Upstash credentials not found. Set UPSTASH_API_KEY and UPSTASH_EMAIL")
            logger.info("Get your API key from: https://console.upstash.com/account/api")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create database
        payload = {
            "name": f"hoistscout-{int(time.time())}",
            "region": "us-east-1",  # Free tier region
            "tls": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/redis/database",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract credentials
                return RedisCredentials(
                    url=f"rediss://default:{data['password']}@{data['endpoint']}:{data['port']}",
                    host=data['endpoint'],
                    port=data['port'],
                    password=data['password'],
                    username="default",
                    ssl=True,
                    provider="upstash",
                    region=data['region'],
                    max_connections=1000,
                    max_commands_per_second=1000,
                    max_request_size="1MB",
                    max_memory="256MB"
                )
            else:
                logger.error(f"Failed to create Upstash database: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error provisioning Upstash: {e}")
            return None
    
    def verify_connection(self, credentials: RedisCredentials) -> bool:
        """Verify Upstash Redis connection"""
        try:
            r = redis.from_url(credentials.url, decode_responses=True)
            r.ping()
            logger.info("✅ Upstash Redis connection verified")
            return True
        except Exception as e:
            logger.error(f"❌ Upstash connection failed: {e}")
            return False


class RailwayProvider(RedisProvider):
    """Railway Redis provider - cloud platform with free tier"""
    
    def __init__(self):
        self.api_key = os.environ.get('RAILWAY_API_KEY')
        self.base_url = "https://api.railway.app/graphql/v2"
        
    def get_name(self) -> str:
        return "Railway"
    
    def provision(self) -> Optional[RedisCredentials]:
        """
        Provision Railway Redis instance
        
        Note: Railway requires authentication and has limited free tier
        """
        logger.info("Provisioning Railway Redis instance...")
        
        if not self.api_key:
            logger.warning("Railway API key not found. Set RAILWAY_API_KEY")
            logger.info("Get your API key from: https://railway.app/account/tokens")
            return None
        
        # Railway uses GraphQL API
        # This is a simplified example - actual implementation would need proper GraphQL queries
        logger.warning("Railway provisioning requires manual setup through their dashboard")
        logger.info("Visit: https://railway.app/new to create a Redis instance")
        return None
    
    def verify_connection(self, credentials: RedisCredentials) -> bool:
        """Verify Railway Redis connection"""
        try:
            r = redis.from_url(credentials.url, decode_responses=True)
            r.ping()
            logger.info("✅ Railway Redis connection verified")
            return True
        except Exception as e:
            logger.error(f"❌ Railway connection failed: {e}")
            return False


class AivenProvider(RedisProvider):
    """Aiven Redis provider - managed cloud services"""
    
    def __init__(self):
        self.api_key = os.environ.get('AIVEN_API_KEY')
        self.base_url = "https://api.aiven.io/v1"
        
    def get_name(self) -> str:
        return "Aiven"
    
    def provision(self) -> Optional[RedisCredentials]:
        """
        Provision Aiven Redis instance
        
        Note: Aiven has a 30-day free trial
        """
        logger.info("Provisioning Aiven Redis instance...")
        
        if not self.api_key:
            logger.warning("Aiven API key not found. Set AIVEN_API_KEY")
            logger.info("Sign up for free trial at: https://aiven.io/signup")
            return None
        
        # Aiven provisioning would require proper API implementation
        logger.warning("Aiven provisioning requires manual setup")
        logger.info("Visit: https://console.aiven.io/ to create a Redis instance")
        return None
    
    def verify_connection(self, credentials: RedisCredentials) -> bool:
        """Verify Aiven Redis connection"""
        try:
            r = redis.from_url(credentials.url, decode_responses=True)
            r.ping()
            logger.info("✅ Aiven Redis connection verified")
            return True
        except Exception as e:
            logger.error(f"❌ Aiven connection failed: {e}")
            return False


class LocalRedisProvider(RedisProvider):
    """Local Redis provider for development"""
    
    def get_name(self) -> str:
        return "Local"
    
    def provision(self) -> Optional[RedisCredentials]:
        """Check for local Redis instance"""
        logger.info("Checking for local Redis instance...")
        
        # Common local Redis configurations
        local_configs = [
            ("localhost", 6379, None),
            ("127.0.0.1", 6379, None),
            ("redis", 6379, None),  # Docker service name
        ]
        
        for host, port, password in local_configs:
            try:
                url = f"redis://{host}:{port}"
                if password:
                    url = f"redis://:{password}@{host}:{port}"
                
                r = redis.from_url(url, socket_connect_timeout=1)
                r.ping()
                
                logger.info(f"✅ Found local Redis at {host}:{port}")
                return RedisCredentials(
                    url=url,
                    host=host,
                    port=port,
                    password=password,
                    ssl=False,
                    provider="local",
                    region="local",
                    max_connections=10000,
                    max_commands_per_second=100000,
                    max_request_size="512MB",
                    max_memory="available"
                )
            except:
                continue
        
        logger.warning("No local Redis instance found")
        logger.info("Install Redis: https://redis.io/docs/getting-started/")
        return None
    
    def verify_connection(self, credentials: RedisCredentials) -> bool:
        """Verify local Redis connection"""
        try:
            r = redis.from_url(credentials.url, decode_responses=True)
            r.ping()
            logger.info("✅ Local Redis connection verified")
            return True
        except Exception as e:
            logger.error(f"❌ Local connection failed: {e}")
            return False


class RedisProvisioner:
    """Main Redis provisioning orchestrator"""
    
    def __init__(self):
        self.providers: List[RedisProvider] = [
            UpstashProvider(),
            LocalRedisProvider(),
            RailwayProvider(),
            AivenProvider(),
        ]
    
    def provision(self, provider_name: Optional[str] = None) -> Optional[RedisCredentials]:
        """
        Provision Redis instance from specified provider or try all
        
        Args:
            provider_name: Specific provider to use (optional)
            
        Returns:
            RedisCredentials if successful, None otherwise
        """
        if provider_name:
            # Try specific provider
            for provider in self.providers:
                if provider.get_name().lower() == provider_name.lower():
                    logger.info(f"Trying {provider.get_name()} provider...")
                    credentials = provider.provision()
                    if credentials:
                        return credentials
                    break
            else:
                logger.error(f"Provider '{provider_name}' not found")
        else:
            # Try all providers in order
            for provider in self.providers:
                logger.info(f"Trying {provider.get_name()} provider...")
                credentials = provider.provision()
                if credentials:
                    return credentials
                logger.info(f"{provider.get_name()} provider failed, trying next...")
        
        return None
    
    def verify_credentials(self, credentials: RedisCredentials) -> bool:
        """Verify Redis credentials work"""
        for provider in self.providers:
            if provider.get_name().lower() == credentials.provider.lower():
                return provider.verify_connection(credentials)
        
        # Generic verification
        try:
            r = redis.from_url(credentials.url, decode_responses=True)
            r.ping()
            return True
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False


def test_redis_operations(credentials: RedisCredentials) -> bool:
    """Test basic Redis operations"""
    logger.info("Testing Redis operations...")
    
    try:
        r = redis.from_url(credentials.url, decode_responses=True)
        
        # Test basic operations
        test_key = "test:hoistscout"
        test_value = "Hello from HoistScout!"
        
        # SET
        r.set(test_key, test_value)
        logger.info("✅ SET operation successful")
        
        # GET
        result = r.get(test_key)
        assert result == test_value
        logger.info("✅ GET operation successful")
        
        # DELETE
        r.delete(test_key)
        logger.info("✅ DELETE operation successful")
        
        # Test expiration
        r.setex("test:expire", 5, "expires in 5 seconds")
        ttl = r.ttl("test:expire")
        assert ttl > 0
        logger.info("✅ Expiration test successful")
        
        # Test list operations
        r.lpush("test:list", "item1", "item2", "item3")
        items = r.lrange("test:list", 0, -1)
        assert len(items) == 3
        r.delete("test:list")
        logger.info("✅ List operations successful")
        
        # Test hash operations
        r.hset("test:hash", mapping={"field1": "value1", "field2": "value2"})
        hash_data = r.hgetall("test:hash")
        assert len(hash_data) == 2
        r.delete("test:hash")
        logger.info("✅ Hash operations successful")
        
        logger.info("✅ All Redis operations completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis operation test failed: {e}")
        return False


def output_credentials(credentials: RedisCredentials, format: str = "text"):
    """Output credentials in requested format"""
    
    if format == "env":
        print(f"# Redis Configuration - {credentials.provider}")
        print(f"REDIS_URL={credentials.url}")
        print(f"REDIS_HOST={credentials.host}")
        print(f"REDIS_PORT={credentials.port}")
        if credentials.password:
            print(f"REDIS_PASSWORD={credentials.password}")
        if credentials.username:
            print(f"REDIS_USERNAME={credentials.username}")
        print(f"REDIS_SSL={'true' if credentials.ssl else 'false'}")
        print(f"REDIS_PROVIDER={credentials.provider}")
        
    elif format == "json":
        data = {
            "url": credentials.url,
            "host": credentials.host,
            "port": credentials.port,
            "password": credentials.password,
            "username": credentials.username,
            "ssl": credentials.ssl,
            "provider": credentials.provider,
            "region": credentials.region,
            "limits": {
                "max_connections": credentials.max_connections,
                "max_commands_per_second": credentials.max_commands_per_second,
                "max_request_size": credentials.max_request_size,
                "max_memory": credentials.max_memory
            }
        }
        print(json.dumps(data, indent=2))
        
    else:  # text format
        print("\n" + "="*60)
        print(f"✅ Redis Instance Provisioned Successfully!")
        print("="*60)
        print(f"Provider: {credentials.provider}")
        print(f"Region: {credentials.region}")
        print(f"\nConnection Details:")
        print(f"  URL: {credentials.url}")
        print(f"  Host: {credentials.host}")
        print(f"  Port: {credentials.port}")
        print(f"  SSL: {'Enabled' if credentials.ssl else 'Disabled'}")
        print(f"\nLimits:")
        print(f"  Max Connections: {credentials.max_connections}")
        print(f"  Max Commands/sec: {credentials.max_commands_per_second}")
        print(f"  Max Request Size: {credentials.max_request_size}")
        print(f"  Max Memory: {credentials.max_memory}")
        print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Provision free Redis instances from multiple providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--provider",
        choices=["upstash", "railway", "aiven", "local", "auto"],
        default="auto",
        help="Redis provider to use (default: auto)"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify connection after provisioning"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run Redis operation tests"
    )
    
    parser.add_argument(
        "--output-env",
        action="store_true",
        help="Output in .env format"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    args = parser.parse_args()
    
    # Determine output format
    output_format = "text"
    if args.output_env:
        output_format = "env"
    elif args.json:
        output_format = "json"
    
    # Provision Redis
    provisioner = RedisProvisioner()
    
    provider = None if args.provider == "auto" else args.provider
    credentials = provisioner.provision(provider)
    
    if not credentials:
        logger.error("Failed to provision Redis instance from any provider")
        logger.info("\nTo use specific providers, set these environment variables:")
        logger.info("  Upstash: UPSTASH_API_KEY, UPSTASH_EMAIL")
        logger.info("  Railway: RAILWAY_API_KEY")
        logger.info("  Aiven: AIVEN_API_KEY")
        sys.exit(1)
    
    # Verify connection if requested
    if args.verify:
        if not provisioner.verify_credentials(credentials):
            logger.error("Connection verification failed")
            sys.exit(1)
    
    # Run tests if requested
    if args.test:
        if not test_redis_operations(credentials):
            logger.error("Redis operation tests failed")
            sys.exit(1)
    
    # Output credentials
    output_credentials(credentials, output_format)
    
    return credentials


if __name__ == "__main__":
    main()