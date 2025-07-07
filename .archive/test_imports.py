#!/usr/bin/env python3
"""Test all imports to ensure no missing dependencies before deployment."""

import sys

def test_imports():
    """Test all critical imports."""
    failed_imports = []
    
    # Core packages
    packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "sqlmodel",
        "asyncpg",
        "psycopg2",
        "alembic",
        "pydantic",
        "pydantic_settings",
        "redis",
        "rq",
        "celery",
        "httpx",
        "dotenv",
        "loguru",
        "pandas",
        "chardet",
        "fakeredis",
        "bs4",
        "playwright",
        "playwright_stealth",
        "tenacity",
        "prometheus_client",
        "sentry_sdk",
        "starlette",
        "jose",
        "cryptography"
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            failed_imports.append(f"{package}: {e}")
            print(f"❌ {package}: {e}")
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} imports failed!")
        return False
    else:
        print(f"\n✅ All {len(packages)} imports successful!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)