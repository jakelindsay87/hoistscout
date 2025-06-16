#!/usr/bin/env python3
"""
Test script to verify UI integration is working correctly
"""
import requests
import sys

def test_backend_endpoints():
    """Test all backend endpoints are working"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend API Endpoints...")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats: {stats['total_sites']} sites, {stats['total_opportunities']} opportunities")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
        return False
    
    # Test websites endpoint
    try:
        response = requests.get(f"{base_url}/api/websites")
        if response.status_code == 200:
            sites = response.json()
            print(f"✅ Websites: {len(sites)} sites configured")
        else:
            print(f"❌ Websites endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Websites endpoint error: {e}")
        return False
    
    # Test opportunities endpoint
    try:
        response = requests.get(f"{base_url}/api/opportunities")
        if response.status_code == 200:
            opportunities = response.json()
            print(f"✅ Opportunities: {len(opportunities)} opportunities found")
            if opportunities:
                print(f"   First opportunity: {opportunities[0]['title']}")
        else:
            print(f"❌ Opportunities endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Opportunities endpoint error: {e}")
        return False
    
    # Test scrape-jobs endpoint
    try:
        response = requests.get(f"{base_url}/api/scrape-jobs")
        if response.status_code == 200:
            jobs = response.json()
            print(f"✅ Scrape Jobs: {len(jobs)} jobs found")
        else:
            print(f"❌ Scrape Jobs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Scrape Jobs endpoint error: {e}")
        return False
    
    return True

def test_frontend_accessibility():
    """Test frontend is accessible"""
    print("\n🌐 Testing Frontend Accessibility...")
    
    frontend_ports = [3000, 3001, 3002]
    
    for port in frontend_ports:
        try:
            response = requests.get(f"http://localhost:{port}/", timeout=5)
            if response.status_code == 200:
                print(f"✅ Frontend accessible on port {port}")
                return True
        except Exception:
            continue
    
    print("❌ Frontend not accessible on any expected port")
    return False

def main():
    """Run all tests"""
    print("🚀 HoistScraper UI Integration Test\n")
    
    backend_ok = test_backend_endpoints()
    frontend_ok = test_frontend_accessibility()
    
    print(f"\n📊 Test Results:")
    print(f"Backend API: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend:    {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 All tests passed! UI integration is working correctly.")
        print("\nNext steps:")
        print("1. Visit http://localhost:3002 to view the dashboard")
        print("2. Check the Opportunities page to see scraped grants")
        print("3. Use the Jobs page to create new scraping jobs")
        print("4. Manage the 244 Australian grant sites on the Sites page")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())