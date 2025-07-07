#!/usr/bin/env python3
"""Check deployment status and configuration."""
import requests
import json

API_BASE = "https://hoistscraper.onrender.com"

def check_health_detailed():
    """Get detailed health status."""
    print("Checking detailed health status...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"\nHealth Status: {health.get('status', 'unknown')}")
            print(f"Timestamp: {health.get('timestamp', 'N/A')}")
            print(f"Service: {health.get('service', 'N/A')}")
            
            # Check individual components if available
            checks = health.get('checks', {})
            if checks:
                print("\nComponent Status:")
                for component, status in checks.items():
                    print(f"  - {component}: {status}")
            
            return health
        else:
            print(f"Health check returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"Health check failed: {e}")
        return None

def check_metrics():
    """Check metrics endpoint if available."""
    print("\nChecking metrics...")
    
    try:
        response = requests.get(f"{API_BASE}/metrics", timeout=10)
        if response.status_code == 200:
            print("✓ Metrics endpoint is accessible")
            # Don't print full metrics as they might be verbose
            return True
        else:
            print(f"✗ Metrics endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Metrics check failed: {e}")
        return False

def test_database_endpoint():
    """Test if we can reach database-dependent endpoints."""
    print("\nTesting database connectivity via API...")
    
    # Try to get websites (requires database)
    try:
        response = requests.get(f"{API_BASE}/api/websites", timeout=10)
        if response.status_code == 200:
            websites = response.json()
            print(f"✓ Database is accessible - found {len(websites)} websites")
            return True
        elif response.status_code == 500:
            print("✗ Database error - backend cannot connect to database")
            try:
                error_detail = response.json()
                print(f"  Error: {error_detail.get('detail', 'Unknown')}")
                print(f"  Message: {error_detail.get('error', 'No details')}")
            except:
                print(f"  Raw response: {response.text[:200]}")
            return False
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

def check_api_docs():
    """Check if API documentation is available."""
    print("\nChecking API documentation...")
    
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=10)
        if response.status_code == 200:
            print("✓ API documentation is accessible at /docs")
            return True
        else:
            print(f"✗ API docs returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API docs check failed: {e}")
        return False

def main():
    """Run all deployment checks."""
    print("=== HoistScraper Deployment Check ===")
    print(f"API URL: {API_BASE}")
    print("=" * 40)
    
    # Run checks
    health = check_health_detailed()
    metrics_ok = check_metrics()
    db_ok = test_database_endpoint()
    docs_ok = check_api_docs()
    
    # Summary
    print("\n=== Summary ===")
    if health and health.get('status') == 'healthy':
        print("✅ API is healthy")
    else:
        print("❌ API health check failed")
    
    if db_ok:
        print("✅ Database connectivity is working")
    else:
        print("❌ Database connectivity is broken")
        print("\nPossible causes:")
        print("  1. Database service not running")
        print("  2. DATABASE_URL environment variable not set correctly")
        print("  3. Network connectivity issues between services")
        print("  4. Database migrations not run")
    
    if docs_ok:
        print("✅ API documentation is available")
    else:
        print("❌ API documentation is not accessible")

if __name__ == "__main__":
    main()