#!/usr/bin/env python3
"""Comprehensive integration tests for HoistScraper."""
import sys
import time
import requests
import json
import threading
from datetime import datetime
from typing import List, Dict, Any

class IntegrationTestSuite:
    def __init__(self, base_url="https://hoistscraper.onrender.com"):
        self.base_url = base_url
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        self.test_data = {
            "websites": [],
            "jobs": []
        }
    
    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        result = {
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["tests"].append(result)
        
        if passed:
            self.test_results["passed"] += 1
            print(f"✅ {name}")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {name}: {details}")
    
    def test_api_health(self) -> bool:
        """Test API health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            return False
    
    def test_website_crud(self) -> bool:
        """Test website CRUD operations."""
        # Test CREATE
        test_website = {
            "name": f"Integration Test Site {datetime.now().timestamp()}",
            "url": f"https://test-{int(datetime.now().timestamp())}.example.com",
            "active": True,
            "region": "Test Region",
            "government_level": "Federal",
            "grant_type": "Research"
        }
        
        try:
            # Create website
            response = requests.post(
                f"{self.base_url}/api/websites",
                json=test_website,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                website = response.json()
                self.test_data["websites"].append(website)
                self.log_test("Create Website", True, f"ID: {website['id']}")
                
                # Test READ
                response = requests.get(
                    f"{self.base_url}/api/websites/{website['id']}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test("Read Website", True)
                else:
                    self.log_test("Read Website", False, f"Status: {response.status_code}")
                
                # Test UPDATE
                update_data = test_website.copy()
                update_data["name"] = "Updated Test Site"
                
                response = requests.put(
                    f"{self.base_url}/api/websites/{website['id']}",
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test("Update Website", True)
                else:
                    self.log_test("Update Website", False, f"Status: {response.status_code}")
                
                # Test DELETE
                response = requests.delete(
                    f"{self.base_url}/api/websites/{website['id']}",
                    timeout=10
                )
                
                if response.status_code in [200, 204]:
                    self.log_test("Delete Website", True)
                else:
                    self.log_test("Delete Website", False, f"Status: {response.status_code}")
                
                return True
                
            else:
                self.log_test("Create Website", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Website CRUD", False, str(e))
            return False
    
    def test_scraping_workflow(self) -> bool:
        """Test complete scraping workflow."""
        try:
            # First, create a website to scrape
            test_website = {
                "name": "Scrape Test Site",
                "url": "https://www.grants.gov",
                "active": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/websites",
                json=test_website,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.log_test("Scraping Workflow - Create Site", False, f"Status: {response.status_code}")
                return False
            
            website = response.json()
            self.test_data["websites"].append(website)
            
            # Create scrape job
            job_data = {"website_id": website["id"]}
            
            response = requests.post(
                f"{self.base_url}/api/scrape-jobs",
                json=job_data,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.log_test("Create Scrape Job", False, f"Status: {response.status_code}")
                return False
            
            job = response.json()
            self.test_data["jobs"].append(job)
            self.log_test("Create Scrape Job", True, f"Job ID: {job['id']}")
            
            # Monitor job progress
            max_wait = 60  # 60 seconds
            start_time = time.time()
            job_completed = False
            
            while time.time() - start_time < max_wait:
                response = requests.get(
                    f"{self.base_url}/api/scrape-jobs/{job['id']}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    job_status = response.json()
                    status = job_status.get("status", "unknown")
                    
                    if status == "completed":
                        self.log_test("Job Completion", True, f"Job completed in {time.time() - start_time:.1f}s")
                        job_completed = True
                        break
                    elif status == "failed":
                        self.log_test("Job Completion", False, f"Job failed: {job_status.get('error_message')}")
                        break
                    
                time.sleep(5)
            
            if not job_completed:
                self.log_test("Job Completion", False, "Job did not complete within timeout")
            
            return job_completed
            
        except Exception as e:
            self.log_test("Scraping Workflow", False, str(e))
            return False
    
    def test_concurrent_operations(self) -> bool:
        """Test system under concurrent load."""
        def make_request(endpoint: str, results: List):
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                results.append({
                    "status": response.status_code,
                    "time": response.elapsed.total_seconds()
                })
            except Exception as e:
                results.append({"error": str(e)})
        
        # Test concurrent reads
        threads = []
        results = []
        
        for i in range(10):
            thread = threading.Thread(
                target=make_request,
                args=("/api/websites", results)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Analyze results
        success_count = sum(1 for r in results if r.get("status") == 200)
        avg_time = sum(r.get("time", 0) for r in results) / len(results) if results else 0
        
        if success_count >= 8:  # 80% success rate
            self.log_test(
                "Concurrent Operations",
                True,
                f"Success: {success_count}/10, Avg time: {avg_time:.2f}s"
            )
            return True
        else:
            self.log_test(
                "Concurrent Operations",
                False,
                f"Only {success_count}/10 succeeded"
            )
            return False
    
    def test_error_handling(self) -> bool:
        """Test API error handling."""
        tests_passed = True
        
        # Test 404 handling
        response = requests.get(f"{self.base_url}/api/websites/99999", timeout=10)
        if response.status_code == 404:
            self.log_test("404 Error Handling", True)
        else:
            self.log_test("404 Error Handling", False, f"Expected 404, got {response.status_code}")
            tests_passed = False
        
        # Test invalid data handling
        invalid_website = {
            "name": "",  # Empty name should fail validation
            "url": "not-a-valid-url"
        }
        
        response = requests.post(
            f"{self.base_url}/api/websites",
            json=invalid_website,
            timeout=10
        )
        
        if response.status_code in [400, 422]:
            self.log_test("Validation Error Handling", True)
        else:
            self.log_test("Validation Error Handling", False, f"Expected 400/422, got {response.status_code}")
            tests_passed = False
        
        return tests_passed
    
    def test_pagination(self) -> bool:
        """Test pagination functionality."""
        try:
            # Test with pagination parameters
            response = requests.get(
                f"{self.base_url}/api/websites?page=1&per_page=5",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) <= 5:
                    self.log_test("Pagination", True)
                    return True
                else:
                    self.log_test("Pagination", False, "Invalid response format or size")
                    return False
            else:
                self.log_test("Pagination", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Pagination", False, str(e))
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during tests."""
        print("\nCleaning up test data...")
        
        # Delete test websites
        for website in self.test_data["websites"]:
            try:
                requests.delete(
                    f"{self.base_url}/api/websites/{website['id']}",
                    timeout=10
                )
            except:
                pass
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("="*50)
        print("HOISTSCRAPER INTEGRATION TEST SUITE")
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now()}")
        print("="*50)
        
        # Run tests in order
        test_methods = [
            ("API Health", self.test_api_health),
            ("Website CRUD", self.test_website_crud),
            ("Scraping Workflow", self.test_scraping_workflow),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Error Handling", self.test_error_handling),
            ("Pagination", self.test_pagination)
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n📋 Testing {test_name}...")
            try:
                test_method()
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {e}")
        
        # Cleanup
        self.cleanup_test_data()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*50)
        print("TEST RESULTS SUMMARY")
        print("="*50)
        
        total = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (self.test_results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.test_results['passed']} ✅")
        print(f"Failed: {self.test_results['failed']} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results["failed"] > 0:
            print("\nFailed Tests:")
            for test in self.test_results["tests"]:
                if not test["passed"]:
                    print(f"  - {test['name']}: {test['details']}")
        
        # Save detailed report
        with open("integration_test_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print("\n📄 Detailed report saved to integration_test_report.json")
        
        # Return exit code
        return 0 if self.test_results["failed"] == 0 else 1


def main():
    """Run integration tests."""
    # Check command line arguments
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://hoistscraper.onrender.com"
    
    # Run tests
    suite = IntegrationTestSuite(base_url)
    suite.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if suite.test_results["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()