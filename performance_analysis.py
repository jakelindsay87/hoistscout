#!/usr/bin/env python3
"""Performance analysis for HoistScraper production deployment."""
import time
import requests
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

class PerformanceAnalyzer:
    def __init__(self, base_url="https://hoistscraper.onrender.com"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": {},
            "issues": [],
            "recommendations": []
        }
    
    def measure_endpoint(self, endpoint, method="GET", data=None, iterations=5):
        """Measure performance of a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        times = []
        errors = 0
        status_codes = []
        
        for i in range(iterations):
            try:
                start = time.time()
                if method == "GET":
                    response = requests.get(url, timeout=30)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=30)
                
                elapsed = time.time() - start
                times.append(elapsed)
                status_codes.append(response.status_code)
                
                if response.status_code >= 400:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                self.results["issues"].append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "iteration": i
                })
        
        if times:
            return {
                "endpoint": endpoint,
                "method": method,
                "avg_response_time": statistics.mean(times),
                "min_response_time": min(times),
                "max_response_time": max(times),
                "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                "error_rate": errors / iterations,
                "status_codes": status_codes
            }
        else:
            return {
                "endpoint": endpoint,
                "method": method,
                "error": "All requests failed",
                "error_rate": 1.0
            }
    
    def analyze_api_performance(self):
        """Analyze performance of all API endpoints."""
        print("=== API Performance Analysis ===")
        
        endpoints = [
            ("/health", "GET", None),
            ("/api/websites", "GET", None),
            ("/api/scrape-jobs", "GET", None),
            ("/docs", "GET", None),
        ]
        
        for endpoint, method, data in endpoints:
            print(f"\nAnalyzing {endpoint}...")
            result = self.measure_endpoint(endpoint, method, data)
            self.results["endpoints"][endpoint] = result
            
            # Check for performance issues
            if "avg_response_time" in result:
                avg_time = result["avg_response_time"]
                print(f"  Average response time: {avg_time:.2f}s")
                
                if avg_time > 3.0:
                    self.results["issues"].append({
                        "type": "slow_response",
                        "endpoint": endpoint,
                        "avg_time": avg_time,
                        "severity": "high" if avg_time > 5.0 else "medium"
                    })
                    
                if result["error_rate"] > 0.2:
                    self.results["issues"].append({
                        "type": "high_error_rate",
                        "endpoint": endpoint,
                        "error_rate": result["error_rate"],
                        "severity": "high"
                    })
    
    def analyze_database_performance(self):
        """Analyze database query performance."""
        print("\n=== Database Performance Analysis ===")
        
        # Test database-heavy endpoints
        print("\nTesting database query performance...")
        
        # Create test data
        test_website = {
            "name": f"Perf Test Site {datetime.now().timestamp()}",
            "url": f"https://test-{datetime.now().timestamp()}.example.com",
            "active": True
        }
        
        # Test write performance
        write_result = self.measure_endpoint("/api/websites", "POST", test_website, iterations=3)
        if "avg_response_time" in write_result:
            print(f"  Write performance: {write_result['avg_response_time']:.2f}s avg")
            
            if write_result['avg_response_time'] > 1.0:
                self.results["recommendations"].append({
                    "area": "database_writes",
                    "issue": "Slow write performance",
                    "recommendation": "Consider adding database connection pooling or write buffering"
                })
    
    def analyze_frontend_performance(self):
        """Analyze frontend loading performance."""
        print("\n=== Frontend Performance Analysis ===")
        
        frontend_url = "https://hoistscraper-1-wf9y.onrender.com"
        
        try:
            start = time.time()
            response = requests.get(frontend_url, timeout=30)
            load_time = time.time() - start
            
            print(f"  Frontend load time: {load_time:.2f}s")
            print(f"  Response size: {len(response.content) / 1024:.1f} KB")
            
            if load_time > 3.0:
                self.results["issues"].append({
                    "type": "slow_frontend_load",
                    "load_time": load_time,
                    "severity": "medium"
                })
                
                self.results["recommendations"].append({
                    "area": "frontend",
                    "issue": "Slow initial load time",
                    "recommendation": "Enable CDN, optimize bundle size, implement code splitting"
                })
                
        except Exception as e:
            print(f"  Frontend analysis failed: {e}")
    
    def analyze_concurrency(self):
        """Test API under concurrent load."""
        print("\n=== Concurrency Analysis ===")
        
        print("\nTesting concurrent requests...")
        concurrent_requests = 10
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []
            start_time = time.time()
            
            for i in range(concurrent_requests):
                future = executor.submit(
                    requests.get,
                    f"{self.base_url}/api/websites",
                    timeout=30
                )
                futures.append(future)
            
            success = 0
            errors = 0
            response_times = []
            
            for future in as_completed(futures):
                try:
                    response = future.result()
                    if response.status_code == 200:
                        success += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1
            
            total_time = time.time() - start_time
            
            print(f"  Total time for {concurrent_requests} requests: {total_time:.2f}s")
            print(f"  Success rate: {success}/{concurrent_requests}")
            print(f"  Requests per second: {concurrent_requests / total_time:.2f}")
            
            if errors > concurrent_requests * 0.1:
                self.results["issues"].append({
                    "type": "concurrency_errors",
                    "error_rate": errors / concurrent_requests,
                    "severity": "high"
                })
                
                self.results["recommendations"].append({
                    "area": "scalability",
                    "issue": "High error rate under concurrent load",
                    "recommendation": "Implement rate limiting, connection pooling, and request queuing"
                })
    
    def analyze_memory_usage(self):
        """Analyze memory usage patterns."""
        print("\n=== Memory Usage Analysis ===")
        
        # Check if metrics endpoint is available
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            if response.status_code == 200:
                print("  Metrics endpoint available")
                # Parse Prometheus metrics if available
            else:
                print("  Metrics endpoint not available")
                self.results["recommendations"].append({
                    "area": "monitoring",
                    "issue": "No metrics endpoint",
                    "recommendation": "Implement Prometheus metrics for memory, CPU, and request monitoring"
                })
        except Exception:
            print("  Unable to fetch metrics")
    
    def generate_report(self):
        """Generate performance analysis report."""
        print("\n" + "="*50)
        print("PERFORMANCE ANALYSIS REPORT")
        print("="*50)
        
        # Summary of issues
        if self.results["issues"]:
            print(f"\n❌ Found {len(self.results['issues'])} performance issues:")
            
            high_severity = [i for i in self.results["issues"] if i.get("severity") == "high"]
            medium_severity = [i for i in self.results["issues"] if i.get("severity") == "medium"]
            
            if high_severity:
                print(f"\n  HIGH SEVERITY ({len(high_severity)}):")
                for issue in high_severity:
                    print(f"    - {issue['type']}: {issue}")
            
            if medium_severity:
                print(f"\n  MEDIUM SEVERITY ({len(medium_severity)}):")
                for issue in medium_severity:
                    print(f"    - {issue['type']}: {issue}")
        else:
            print("\n✅ No major performance issues detected")
        
        # Recommendations
        if self.results["recommendations"]:
            print(f"\n📋 RECOMMENDATIONS ({len(self.results['recommendations'])}):")
            for rec in self.results["recommendations"]:
                print(f"\n  {rec['area'].upper()}:")
                print(f"    Issue: {rec['issue']}")
                print(f"    Fix: {rec['recommendation']}")
        
        # Performance metrics summary
        print("\n📊 ENDPOINT PERFORMANCE SUMMARY:")
        for endpoint, metrics in self.results["endpoints"].items():
            if "avg_response_time" in metrics:
                status = "✅" if metrics["avg_response_time"] < 1.0 else "⚠️" if metrics["avg_response_time"] < 3.0 else "❌"
                print(f"  {status} {endpoint}: {metrics['avg_response_time']:.2f}s avg")
        
        # Save detailed report
        with open("performance_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n📄 Detailed report saved to performance_report.json")
        
        # Return overall health score
        total_issues = len(self.results["issues"])
        high_issues = len([i for i in self.results["issues"] if i.get("severity") == "high"])
        
        if high_issues > 0:
            return "CRITICAL"
        elif total_issues > 3:
            return "POOR"
        elif total_issues > 0:
            return "FAIR"
        else:
            return "GOOD"
    
    def run_analysis(self):
        """Run complete performance analysis."""
        print("Starting HoistScraper Performance Analysis...")
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now()}")
        print("-" * 50)
        
        # Run all analyses
        self.analyze_api_performance()
        self.analyze_database_performance()
        self.analyze_frontend_performance()
        self.analyze_concurrency()
        self.analyze_memory_usage()
        
        # Generate report
        health_status = self.generate_report()
        
        print(f"\n🏁 OVERALL PERFORMANCE STATUS: {health_status}")
        
        return health_status

if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    status = analyzer.run_analysis()
    
    # Exit with appropriate code
    if status == "CRITICAL":
        sys.exit(2)
    elif status == "POOR":
        sys.exit(1)
    else:
        sys.exit(0)