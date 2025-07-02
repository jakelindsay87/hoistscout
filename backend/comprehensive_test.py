#!/usr/bin/env python3
"""
Comprehensive test suite for HoistScout API
Tests all endpoints, error handling, and edge cases
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import logging

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "https://hoistscout-api.onrender.com"
LOCAL_API_URL = "http://localhost:8001"
TIMEOUT = 30.0

class APITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": []
        }
        self.auth_token = None
        
    async def close(self):
        await self.client.aclose()
        
    async def test_endpoint(self, method: str, path: str, **kwargs) -> Tuple[bool, Dict]:
        """Test a single endpoint and return success status and response data"""
        self.results["total_tests"] += 1
        url = f"{self.base_url}{path}"
        
        try:
            # Add auth header if we have a token
            if self.auth_token and 'headers' not in kwargs:
                kwargs['headers'] = {}
            if self.auth_token:
                kwargs.setdefault('headers', {})['Authorization'] = f"Bearer {self.auth_token}"
                
            response = await self.client.request(method, url, **kwargs)
            
            # Check if response is successful
            if response.status_code >= 200 and response.status_code < 300:
                self.results["passed"] += 1
                logger.info(f"✓ {method} {path} - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {"text": response.text}
            else:
                self.results["failed"] += 1
                error_msg = f"✗ {method} {path} - Status: {response.status_code}"
                if response.text:
                    error_msg += f" - Response: {response.text[:200]}"
                logger.error(error_msg)
                self.results["errors"].append({
                    "endpoint": f"{method} {path}",
                    "status": response.status_code,
                    "response": response.text[:500] if response.text else None
                })
                return False, {}
                
        except Exception as e:
            self.results["failed"] += 1
            error_msg = f"✗ {method} {path} - Exception: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append({
                "endpoint": f"{method} {path}",
                "exception": str(e)
            })
            return False, {}
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info(f"Starting comprehensive API tests against {self.base_url}")
        logger.info("=" * 80)
        
        # Test 1: Health endpoints
        await self.test_health_endpoints()
        
        # Test 2: Auth endpoints
        await self.test_auth_endpoints()
        
        # Test 3: Website endpoints
        await self.test_website_endpoints()
        
        # Test 4: Opportunity endpoints
        await self.test_opportunity_endpoints()
        
        # Test 5: Job endpoints
        await self.test_job_endpoints()
        
        # Test 6: Stats endpoint
        await self.test_stats_endpoint()
        
        # Test 7: Error handling
        await self.test_error_handling()
        
        # Test 8: Edge cases
        await self.test_edge_cases()
        
        # Print results
        self.print_results()
        
    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        logger.info("\n📋 Testing Health Endpoints")
        logger.info("-" * 40)
        
        # Basic health check
        await self.test_endpoint("GET", "/api/health")
        
        # Detailed health check
        await self.test_endpoint("GET", "/api/health/ready")
        
        # Liveness check
        await self.test_endpoint("GET", "/api/health/live")
        
        # Diagnostic check
        await self.test_endpoint("GET", "/api/health/diagnostic")
        
    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        logger.info("\n🔐 Testing Authentication Endpoints")
        logger.info("-" * 40)
        
        # Test registration
        test_user = {
            "email": f"test_{datetime.now().timestamp()}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        success, data = await self.test_endpoint("POST", "/api/auth/register", json=test_user)
        
        if success:
            # Test login with correct credentials
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"]
            }
            success, token_data = await self.test_endpoint(
                "POST", 
                "/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if success and "access_token" in token_data:
                self.auth_token = token_data["access_token"]
                logger.info(f"🔑 Got auth token: {self.auth_token[:20]}...")
                
                # Test getting current user
                await self.test_endpoint("GET", "/api/auth/me")
            
            # Test login with wrong password
            login_data["password"] = "WrongPassword"
            await self.test_endpoint(
                "POST",
                "/api/auth/login", 
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        # Test registration with invalid email
        invalid_user = {
            "email": "not-an-email",
            "password": "TestPassword123!",
            "full_name": "Invalid User"
        }
        await self.test_endpoint("POST", "/api/auth/register", json=invalid_user)
        
    async def test_website_endpoints(self):
        """Test website CRUD endpoints"""
        logger.info("\n🌐 Testing Website Endpoints")
        logger.info("-" * 40)
        
        if not self.auth_token:
            logger.warning("⚠️  No auth token, skipping authenticated endpoints")
            return
            
        # Create a website
        website_data = {
            "name": "Test Grant Site",
            "url": "https://example-grants.com",
            "category": "government",
            "auth_type": "none",
            "scraping_config": {
                "selectors": {
                    "title": "h1.grant-title",
                    "description": "div.grant-description"
                }
            },
            "is_active": True
        }
        
        success, created_website = await self.test_endpoint("POST", "/api/websites", json=website_data)
        
        if success and "id" in created_website:
            website_id = created_website["id"]
            
            # Get website by ID
            await self.test_endpoint("GET", f"/api/websites/{website_id}")
            
            # Update website
            update_data = {
                "name": "Updated Grant Site",
                "is_active": False
            }
            await self.test_endpoint("PUT", f"/api/websites/{website_id}", json=update_data)
            
            # Test website scraping
            await self.test_endpoint("POST", f"/api/websites/{website_id}/test")
            
            # List all websites
            await self.test_endpoint("GET", "/api/websites")
            
            # Delete website
            await self.test_endpoint("DELETE", f"/api/websites/{website_id}")
        
        # Test creating duplicate website
        await self.test_endpoint("POST", "/api/websites", json=website_data)
        
        # Test invalid website data
        invalid_website = {
            "name": "",  # Empty name
            "url": "not-a-url",  # Invalid URL
            "category": "invalid-category"
        }
        await self.test_endpoint("POST", "/api/websites", json=invalid_website)
        
    async def test_opportunity_endpoints(self):
        """Test opportunity endpoints"""
        logger.info("\n💰 Testing Opportunity Endpoints")
        logger.info("-" * 40)
        
        # List opportunities
        await self.test_endpoint("GET", "/api/opportunities")
        
        # List with filters
        await self.test_endpoint("GET", "/api/opportunities?category=technology&min_value=10000")
        
        # Search opportunities
        await self.test_endpoint("GET", "/api/opportunities/search?query=innovation")
        
        # Get non-existent opportunity
        await self.test_endpoint("GET", "/api/opportunities/99999")
        
    async def test_job_endpoints(self):
        """Test scraping job endpoints"""
        logger.info("\n⚙️ Testing Job Endpoints")
        logger.info("-" * 40)
        
        if not self.auth_token:
            logger.warning("⚠️  No auth token, skipping authenticated endpoints")
            return
            
        # First create a website to scrape
        website_data = {
            "name": "Job Test Site",
            "url": "https://test-jobs.example.com",
            "category": "technology",
            "auth_type": "none",
            "is_active": True
        }
        
        success, website = await self.test_endpoint("POST", "/api/websites", json=website_data)
        
        if success and "id" in website:
            website_id = website["id"]
            
            # Create a scraping job
            job_data = {
                "website_id": website_id,
                "job_type": "full_scrape",
                "priority": "medium"
            }
            
            success, job = await self.test_endpoint("POST", "/api/scraping/jobs", json=job_data)
            
            if success and "id" in job:
                job_id = job["id"]
                
                # Get job details
                await self.test_endpoint("GET", f"/api/scraping/jobs/{job_id}")
                
                # Get job logs
                await self.test_endpoint("GET", f"/api/scraping/jobs/{job_id}/logs")
                
                # Cancel job
                await self.test_endpoint("POST", f"/api/scraping/jobs/{job_id}/cancel")
            
            # List all jobs
            await self.test_endpoint("GET", "/api/scraping/jobs")
            
            # List jobs with filters
            await self.test_endpoint("GET", f"/api/scraping/jobs?website_id={website_id}&status=pending")
            
            # Clean up
            await self.test_endpoint("DELETE", f"/api/websites/{website_id}")
        
    async def test_stats_endpoint(self):
        """Test the stats endpoint"""
        logger.info("\n📊 Testing Stats Endpoint")
        logger.info("-" * 40)
        
        success, stats = await self.test_endpoint("GET", "/api/stats")
        
        if success:
            # Verify stats structure
            expected_fields = ["total_sites", "total_jobs", "total_opportunities", "jobs_this_week", "last_scrape"]
            missing_fields = [field for field in expected_fields if field not in stats]
            
            if missing_fields:
                self.results["warnings"].append(f"Stats endpoint missing fields: {missing_fields}")
                logger.warning(f"⚠️  Stats endpoint missing fields: {missing_fields}")
            else:
                logger.info(f"📈 Stats: Sites={stats['total_sites']}, Jobs={stats['total_jobs']}, Opportunities={stats['total_opportunities']}")
                
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        logger.info("\n🚨 Testing Error Handling")
        logger.info("-" * 40)
        
        # Test 404 endpoints
        await self.test_endpoint("GET", "/api/nonexistent")
        await self.test_endpoint("GET", "/api/websites/99999")
        
        # Test method not allowed
        await self.test_endpoint("POST", "/api/health")
        
        # Test missing auth
        self.auth_token = None
        await self.test_endpoint("POST", "/api/websites", json={"name": "Unauthorized"})
        
        # Test malformed JSON
        await self.test_endpoint(
            "POST",
            "/api/auth/register",
            content=b"{'invalid': json}",
            headers={"Content-Type": "application/json"}
        )
        
    async def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        logger.info("\n🔍 Testing Edge Cases")
        logger.info("-" * 40)
        
        # Test large pagination
        await self.test_endpoint("GET", "/api/opportunities?limit=10000&offset=0")
        
        # Test negative values
        await self.test_endpoint("GET", "/api/opportunities?limit=-1")
        
        # Test SQL injection attempt (should be safe)
        await self.test_endpoint("GET", "/api/opportunities/search?query='; DROP TABLE opportunities; --")
        
        # Test XSS attempt in website creation
        if self.auth_token:
            xss_website = {
                "name": "<script>alert('XSS')</script>",
                "url": "https://example.com",
                "category": "other"
            }
            await self.test_endpoint("POST", "/api/websites", json=xss_website)
        
    def print_results(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📋 TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        success_rate = (self.results["passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        logger.info(f"Total Tests: {self.results['total_tests']}")
        logger.info(f"✅ Passed: {self.results['passed']}")
        logger.info(f"❌ Failed: {self.results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.results["errors"]:
            logger.error(f"\n❌ ERRORS ({len(self.results['errors'])})")
            logger.error("-" * 40)
            for error in self.results["errors"][:10]:  # Show first 10 errors
                logger.error(f"• {error}")
                
        if self.results["warnings"]:
            logger.warning(f"\n⚠️  WARNINGS ({len(self.results['warnings'])})")
            logger.warning("-" * 40)
            for warning in self.results["warnings"]:
                logger.warning(f"• {warning}")
                
        # Write detailed results to file
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"\n📄 Detailed results saved to test_results.json")
        
        # Exit with appropriate code
        if self.results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


async def main():
    """Run comprehensive API tests"""
    # Test production API
    logger.info("🚀 Testing Production API")
    tester = APITester(API_BASE_URL)
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()
        
    # Optionally test local API if running
    # logger.info("\n\n🏠 Testing Local API")
    # local_tester = APITester(LOCAL_API_URL)
    # try:
    #     await local_tester.run_all_tests()
    # finally:
    #     await local_tester.close()


if __name__ == "__main__":
    asyncio.run(main())