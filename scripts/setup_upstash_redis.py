#!/usr/bin/env python3
"""
Upstash Redis Setup Script for HoistScout

This script creates a new Upstash Redis database specifically for HoistScout production deployment.
It uses the Upstash REST API to provision a free-tier Redis instance.

Prerequisites:
    1. Create an Upstash account at https://console.upstash.com
    2. Get your API credentials from https://console.upstash.com/account/api
    3. Set environment variables:
       - UPSTASH_EMAIL: Your Upstash account email
       - UPSTASH_API_KEY: Your Upstash API key

Usage:
    python setup_upstash_redis.py
    python setup_upstash_redis.py --output-env > redis.env
    python setup_upstash_redis.py --json

Free Tier Includes:
    - 10,000 commands per day
    - 256MB storage
    - SSL/TLS encryption
    - Global edge caching
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import redis for testing
try:
    import redis
except ImportError:
    logger.warning("Redis package not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
    import redis


@dataclass
class UpstashCredentials:
    """Upstash Redis connection details"""
    database_id: str
    database_name: str
    endpoint: str
    port: int
    password: str
    rest_url: str
    rest_token: str
    redis_url: str
    region: str
    max_clients: int = 1000
    max_commands_per_second: int = 1000
    max_request_size: str = "1MB"
    max_memory: str = "256MB"
    daily_command_limit: int = 10000


class UpstashSetup:
    """Handle Upstash Redis database creation and configuration"""
    
    def __init__(self):
        self.api_key = os.environ.get('UPSTASH_API_KEY')
        self.email = os.environ.get('UPSTASH_EMAIL')
        self.base_url = "https://api.upstash.com/v2"
        self.database_name = "hoistscout-prod"
        
    def validate_credentials(self) -> bool:
        """Check if API credentials are available"""
        if not self.api_key or not self.email:
            logger.error("❌ Upstash credentials not found!")
            logger.info("\n📋 Setup Instructions:")
            logger.info("1. Create an Upstash account: https://console.upstash.com")
            logger.info("2. Go to Account -> API Keys: https://console.upstash.com/account/api")
            logger.info("3. Create a new API key")
            logger.info("4. Set environment variables:")
            logger.info("   export UPSTASH_EMAIL='your-email@example.com'")
            logger.info("   export UPSTASH_API_KEY='your-api-key'")
            return False
        return True
    
    def check_existing_database(self) -> Optional[str]:
        """Check if a database with the same name already exists"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/redis/databases",
                headers=headers
            )
            
            if response.status_code == 200:
                databases = response.json()
                for db in databases:
                    if db.get('database_name') == self.database_name:
                        logger.info(f"ℹ️  Found existing database: {self.database_name}")
                        return db.get('database_id')
            return None
        except Exception as e:
            logger.error(f"Error checking existing databases: {e}")
            return None
    
    def create_database(self) -> Optional[UpstashCredentials]:
        """Create a new Upstash Redis database"""
        if not self.validate_credentials():
            return None
        
        # Check for existing database
        existing_id = self.check_existing_database()
        if existing_id:
            logger.info("ℹ️  Using existing database instead of creating a new one")
            return self.get_database_details(existing_id)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Create database payload
        # Using us-east-1 for free tier and better global latency
        payload = {
            "name": self.database_name,
            "region": "us-east-1",
            "tls": True,  # Always use TLS for security
            "eviction": True  # Enable eviction for free tier
        }
        
        logger.info(f"🚀 Creating Upstash Redis database: {self.database_name}")
        
        try:
            response = requests.post(
                f"{self.base_url}/redis/database",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Database created successfully!")
                
                # Extract all credentials
                return UpstashCredentials(
                    database_id=data['database_id'],
                    database_name=data['database_name'],
                    endpoint=data['endpoint'],
                    port=data['port'],
                    password=data['password'],
                    rest_url=data['rest_url'],
                    rest_token=data['rest_token'],
                    redis_url=f"rediss://default:{data['password']}@{data['endpoint']}:{data['port']}",
                    region=data['region']
                )
            else:
                error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                logger.error(f"❌ Failed to create database: {error_msg}")
                
                # Check if it's a quota issue
                if response.status_code == 402:
                    logger.info("\n💡 Tip: You may have reached the free tier limit.")
                    logger.info("   - Free tier allows 1 database per account")
                    logger.info("   - Delete unused databases at: https://console.upstash.com")
                
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def get_database_details(self, database_id: str) -> Optional[UpstashCredentials]:
        """Get details of an existing database"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/redis/database/{database_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return UpstashCredentials(
                    database_id=data['database_id'],
                    database_name=data['database_name'],
                    endpoint=data['endpoint'],
                    port=data['port'],
                    password=data['password'],
                    rest_url=data['rest_url'],
                    rest_token=data['rest_token'],
                    redis_url=f"rediss://default:{data['password']}@{data['endpoint']}:{data['port']}",
                    region=data['region']
                )
            return None
        except Exception as e:
            logger.error(f"Error getting database details: {e}")
            return None
    
    def test_connection(self, credentials: UpstashCredentials) -> bool:
        """Test the Redis connection"""
        logger.info("\n🔍 Testing Redis connection...")
        
        try:
            # Test Redis protocol connection
            r = redis.from_url(credentials.redis_url, decode_responses=True, socket_timeout=5)
            r.ping()
            logger.info("✅ Redis protocol connection successful")
            
            # Test basic operations
            test_key = "hoistscout:test:connection"
            test_value = f"Connected at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # SET
            r.set(test_key, test_value, ex=60)  # Expire after 60 seconds
            logger.info("✅ SET operation successful")
            
            # GET
            result = r.get(test_key)
            if result == test_value:
                logger.info("✅ GET operation successful")
            
            # INFO to check server details
            info = r.info()
            logger.info(f"✅ Redis version: {info.get('redis_version', 'unknown')}")
            logger.info(f"✅ Used memory: {info.get('used_memory_human', 'unknown')}")
            
            # Clean up
            r.delete(test_key)
            
            return True
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Connection failed: {e}")
            logger.info("\n💡 Troubleshooting tips:")
            logger.info("   - Check if your IP is allowed (Upstash may have IP restrictions)")
            logger.info("   - Verify the database is active in Upstash console")
            logger.info("   - Try using the REST API instead of Redis protocol")
            return False
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    
    def test_rest_api(self, credentials: UpstashCredentials) -> bool:
        """Test the REST API connection"""
        logger.info("\n🔍 Testing REST API connection...")
        
        try:
            # Test REST API with a simple command
            headers = {
                "Authorization": f"Bearer {credentials.rest_token}"
            }
            
            # PING command via REST
            response = requests.post(
                f"{credentials.rest_url}/ping",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("✅ REST API connection successful")
                return True
            else:
                logger.error(f"❌ REST API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ REST API test failed: {e}")
            return False


def output_credentials(credentials: UpstashCredentials, format: str = "text"):
    """Output credentials in the requested format"""
    
    if format == "env":
        print("# Upstash Redis Configuration for HoistScout")
        print(f"# Database: {credentials.database_name}")
        print(f"# Region: {credentials.region}")
        print(f"# Created: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("# Redis Protocol URL (for Celery/Redis clients)")
        print(f"REDIS_URL={credentials.redis_url}")
        print()
        print("# REST API (for HTTP-based access)")
        print(f"UPSTASH_REDIS_REST_URL={credentials.rest_url}")
        print(f"UPSTASH_REDIS_REST_TOKEN={credentials.rest_token}")
        print()
        print("# Individual components (if needed)")
        print(f"REDIS_HOST={credentials.endpoint}")
        print(f"REDIS_PORT={credentials.port}")
        print(f"REDIS_PASSWORD={credentials.password}")
        print("REDIS_SSL=true")
        print()
        print("# Limits")
        print(f"REDIS_MAX_CLIENTS={credentials.max_clients}")
        print(f"REDIS_DAILY_COMMAND_LIMIT={credentials.daily_command_limit}")
        
    elif format == "json":
        data = {
            "database_id": credentials.database_id,
            "database_name": credentials.database_name,
            "redis_url": credentials.redis_url,
            "rest_api": {
                "url": credentials.rest_url,
                "token": credentials.rest_token
            },
            "connection": {
                "host": credentials.endpoint,
                "port": credentials.port,
                "password": credentials.password,
                "ssl": True
            },
            "region": credentials.region,
            "limits": {
                "max_clients": credentials.max_clients,
                "max_commands_per_second": credentials.max_commands_per_second,
                "max_request_size": credentials.max_request_size,
                "max_memory": credentials.max_memory,
                "daily_command_limit": credentials.daily_command_limit
            }
        }
        print(json.dumps(data, indent=2))
        
    else:  # text format
        print("\n" + "="*70)
        print("✅ Upstash Redis Database Ready for HoistScout!")
        print("="*70)
        print(f"Database Name: {credentials.database_name}")
        print(f"Database ID: {credentials.database_id}")
        print(f"Region: {credentials.region}")
        print()
        print("🔗 Connection URLs:")
        print("-" * 70)
        print("Redis Protocol URL (for Render/Celery):")
        print(f"  {credentials.redis_url}")
        print()
        print("REST API URL:")
        print(f"  {credentials.rest_url}")
        print()
        print("🔑 Authentication:")
        print("-" * 70)
        print(f"Password: {credentials.password}")
        print(f"REST Token: {credentials.rest_token}")
        print()
        print("📊 Free Tier Limits:")
        print("-" * 70)
        print(f"  • Daily Commands: {credentials.daily_command_limit:,}")
        print(f"  • Max Memory: {credentials.max_memory}")
        print(f"  • Max Clients: {credentials.max_clients:,}")
        print(f"  • Max Commands/sec: {credentials.max_commands_per_second:,}")
        print()
        print("🚀 Next Steps:")
        print("-" * 70)
        print("1. Copy the Redis URL above")
        print("2. Add it to your Render environment variables as REDIS_URL")
        print("3. Deploy your application!")
        print()
        print("📚 Documentation:")
        print("  • Upstash Docs: https://docs.upstash.com/redis")
        print("  • Console: https://console.upstash.com")
        print("="*70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Set up Upstash Redis for HoistScout production deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
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
    
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip connection testing"
    )
    
    args = parser.parse_args()
    
    # Determine output format
    output_format = "text"
    if args.output_env:
        output_format = "env"
    elif args.json:
        output_format = "json"
    
    # Create Upstash setup instance
    setup = UpstashSetup()
    
    # Create database
    credentials = setup.create_database()
    if not credentials:
        logger.error("\n❌ Failed to set up Upstash Redis database")
        sys.exit(1)
    
    # Test connections unless skipped
    if not args.skip_test:
        redis_ok = setup.test_connection(credentials)
        rest_ok = setup.test_rest_api(credentials)
        
        if not redis_ok and not rest_ok:
            logger.warning("\n⚠️  Connection tests failed, but database was created")
            logger.info("   You can still use the credentials, they might work from Render")
    
    # Output credentials
    output_credentials(credentials, output_format)
    
    return credentials


if __name__ == "__main__":
    main()