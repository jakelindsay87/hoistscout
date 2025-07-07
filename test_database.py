#!/usr/bin/env python3
"""
Test database connection and migrations for HoistScout
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/hoistscout'
os.environ['REDIS_URL'] = 'redis://localhost:6379'

async def test_database():
    """Test database connection and schema"""
    print("Testing database connection and schema...\n")
    
    try:
        from app.database import init_db, close_db, AsyncSessionLocal
        from app.models import User, Website, Opportunity, ScrapeJob
        from app.config import get_settings
        
        settings = get_settings()
        print(f"✅ Imports successful")
        print(f"   Database URL: {settings.database_url.split('@')[1]}")  # Hide password
        
        # Initialize database
        print("\n📊 Initializing database...")
        await init_db()
        print("✅ Database initialized")
        
        # Test database connection
        print("\n🔌 Testing database connection...")
        async with AsyncSessionLocal() as session:
            # Test simple query
            result = await session.execute("SELECT 1")
            print("✅ Database connection successful")
            
            # Check tables exist
            print("\n📋 Checking tables...")
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            result = await session.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['users', 'websites', 'opportunities', 'scraping_jobs', 'audit_logs']
            
            for table in expected_tables:
                if table in tables:
                    print(f"   ✅ Table '{table}' exists")
                else:
                    print(f"   ❌ Table '{table}' missing")
            
            # Check if demo user exists
            print("\n👤 Checking demo user...")
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == "demo@hoistscout.com")
            )
            demo_user = result.scalar_one_or_none()
            
            if demo_user:
                print("✅ Demo user exists")
                print(f"   Email: {demo_user.email}")
                print(f"   Role: {demo_user.role}")
                print(f"   Active: {demo_user.is_active}")
            else:
                print("⚠️  Demo user not found (will be created on startup)")
            
            # Test creating a website
            print("\n🌐 Testing website creation...")
            from app.models.website import Website
            
            test_website = Website(
                name="Test Government Grants",
                url="https://www.grants.gov",
                description="US Federal grants portal",
                category="federal",
                is_active=True
            )
            
            session.add(test_website)
            await session.commit()
            print("✅ Successfully created test website")
            
            # Clean up
            await session.delete(test_website)
            await session.commit()
            print("✅ Cleaned up test data")
            
        await close_db()
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_redis():
    """Test Redis connection"""
    print("\n\n🔴 Testing Redis connection...")
    
    try:
        import redis.asyncio as redis
        from app.config import get_settings
        
        settings = get_settings()
        
        # Parse Redis URL
        r = redis.from_url(settings.redis_url)
        
        # Test connection
        await r.ping()
        print("✅ Redis connection successful")
        
        # Test set/get
        await r.set("test_key", "test_value")
        value = await r.get("test_key")
        
        if value == b"test_value":
            print("✅ Redis set/get working")
        else:
            print("❌ Redis set/get failed")
        
        # Clean up
        await r.delete("test_key")
        await r.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("="*60)
    print("HoistScout Database & Redis Tests")
    print("="*60)
    
    # Test database
    db_success = await test_database()
    
    # Test Redis
    redis_success = await test_redis()
    
    print("\n" + "="*60)
    if db_success and redis_success:
        print("✅ All tests passed!")
        print("\nDatabase and Redis are properly configured.")
        print("The application should be able to:")
        print("- Store user accounts and authentication")
        print("- Manage websites for scraping")
        print("- Queue and process scraping jobs")
        print("- Store scraped opportunities")
    else:
        print("❌ Some tests failed")
        print("\nPlease check:")
        print("1. PostgreSQL is running on port 5432")
        print("2. Redis is running on port 6379")
        print("3. Database credentials are correct")
        print("4. Database 'hoistscout' exists")
    
    return 0 if (db_success and redis_success) else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))