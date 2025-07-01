#!/usr/bin/env python3
"""Worker validation script for HoistScraper."""
import sys
import time
import requests
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class WorkerValidator:
    def __init__(self, base_url="https://hoistscraper.onrender.com"):
        self.base_url = base_url
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "issues": [],
            "worker_health": "unknown"
        }
    
    def check_worker_process(self) -> bool:
        """Check if worker process is running (local only)."""
        try:
            # This only works locally, not in production
            result = subprocess.run(
                ["pgrep", "-f", "rq worker"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                self.validation_results["checks"].append({
                    "name": "Worker Process",
                    "status": "running",
                    "details": f"Found {len(pids)} worker process(es)"
                })
                return True
            else:
                self.validation_results["checks"].append({
                    "name": "Worker Process",
                    "status": "not found",
                    "details": "No worker processes detected"
                })
                return False
                
        except Exception as e:
            self.validation_results["checks"].append({
                "name": "Worker Process",
                "status": "error",
                "details": str(e)
            })
            return False
    
    def check_job_queue_health(self) -> Dict[str, any]:
        """Check job queue status via API."""
        print("Checking job queue health...")
        
        try:
            # Get recent jobs
            response = requests.get(f"{self.base_url}/api/scrape-jobs", timeout=10)
            
            if response.status_code == 200:
                jobs = response.json()
                
                # Analyze job statuses
                status_counts = {
                    "pending": 0,
                    "running": 0,
                    "completed": 0,
                    "failed": 0
                }
                
                recent_jobs = []
                stuck_jobs = []
                
                for job in jobs[:50]:  # Check last 50 jobs
                    status = job.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Check for stuck jobs
                    if status == "running":
                        started_at = job.get("started_at")
                        if started_at:
                            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                            runtime = datetime.now() - start_time
                            
                            if runtime > timedelta(minutes=30):
                                stuck_jobs.append({
                                    "id": job["id"],
                                    "runtime": str(runtime)
                                })
                    
                    # Track recent jobs
                    if len(recent_jobs) < 5:
                        recent_jobs.append({
                            "id": job["id"],
                            "status": status,
                            "created": job.get("created_at")
                        })
                
                queue_health = {
                    "total_jobs": len(jobs),
                    "status_distribution": status_counts,
                    "stuck_jobs": stuck_jobs,
                    "recent_jobs": recent_jobs
                }
                
                self.validation_results["checks"].append({
                    "name": "Job Queue",
                    "status": "healthy" if not stuck_jobs else "degraded",
                    "details": queue_health
                })
                
                return queue_health
                
            else:
                self.validation_results["issues"].append({
                    "check": "Job Queue",
                    "issue": f"API returned status {response.status_code}"
                })
                return {}
                
        except Exception as e:
            self.validation_results["issues"].append({
                "check": "Job Queue",
                "issue": str(e)
            })
            return {}
    
    def test_job_processing(self) -> bool:
        """Test actual job processing capability."""
        print("\nTesting job processing...")
        
        try:
            # Create a test website
            test_website = {
                "name": f"Worker Test Site {int(datetime.now().timestamp())}",
                "url": "https://example.com",
                "active": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/websites",
                json=test_website,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.validation_results["issues"].append({
                    "check": "Job Processing",
                    "issue": f"Failed to create test website: {response.status_code}"
                })
                return False
            
            website = response.json()
            
            # Create a scrape job
            job_data = {"website_id": website["id"]}
            
            response = requests.post(
                f"{self.base_url}/api/scrape-jobs",
                json=job_data,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.validation_results["issues"].append({
                    "check": "Job Processing",
                    "issue": f"Failed to create job: {response.status_code}"
                })
                return False
            
            job = response.json()
            job_id = job["id"]
            
            print(f"Created test job {job_id}, monitoring progress...")
            
            # Monitor job for up to 60 seconds
            start_time = time.time()
            max_wait = 60
            job_processed = False
            
            while time.time() - start_time < max_wait:
                response = requests.get(
                    f"{self.base_url}/api/scrape-jobs/{job_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    job_status = response.json()
                    status = job_status.get("status")
                    
                    print(f"  Job status: {status}")
                    
                    if status == "completed":
                        processing_time = time.time() - start_time
                        self.validation_results["checks"].append({
                            "name": "Job Processing",
                            "status": "working",
                            "details": f"Job completed in {processing_time:.1f}s"
                        })
                        job_processed = True
                        break
                        
                    elif status == "failed":
                        self.validation_results["issues"].append({
                            "check": "Job Processing",
                            "issue": f"Job failed: {job_status.get('error_message')}"
                        })
                        break
                
                time.sleep(5)
            
            if not job_processed and status != "failed":
                self.validation_results["issues"].append({
                    "check": "Job Processing",
                    "issue": f"Job did not complete within {max_wait}s (status: {status})"
                })
            
            # Cleanup
            try:
                requests.delete(f"{self.base_url}/api/websites/{website['id']}", timeout=10)
            except:
                pass
            
            return job_processed
            
        except Exception as e:
            self.validation_results["issues"].append({
                "check": "Job Processing",
                "issue": str(e)
            })
            return False
    
    def check_worker_configuration(self) -> Dict[str, any]:
        """Check worker configuration via health endpoint."""
        print("\nChecking worker configuration...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health = response.json()
                
                # Extract worker-related info if available
                checks = health.get("checks", {})
                worker_info = {}
                
                if "worker_queue" in checks:
                    worker_info["queue_status"] = checks["worker_queue"]
                
                if "redis" in checks:
                    worker_info["redis_status"] = checks["redis"]
                
                self.validation_results["checks"].append({
                    "name": "Worker Configuration",
                    "status": "configured",
                    "details": worker_info
                })
                
                return worker_info
                
            else:
                self.validation_results["issues"].append({
                    "check": "Worker Configuration",
                    "issue": f"Health endpoint returned {response.status_code}"
                })
                return {}
                
        except Exception as e:
            self.validation_results["issues"].append({
                "check": "Worker Configuration",
                "issue": str(e)
            })
            return {}
    
    def analyze_job_throughput(self) -> Dict[str, any]:
        """Analyze job processing throughput."""
        print("\nAnalyzing job throughput...")
        
        try:
            response = requests.get(f"{self.base_url}/api/scrape-jobs", timeout=10)
            
            if response.status_code == 200:
                jobs = response.json()
                
                # Calculate throughput for last hour
                one_hour_ago = datetime.now() - timedelta(hours=1)
                recent_completed = []
                
                for job in jobs:
                    if job.get("status") == "completed":
                        completed_at = job.get("completed_at")
                        if completed_at:
                            completion_time = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                            if completion_time > one_hour_ago:
                                recent_completed.append(job)
                
                throughput = {
                    "jobs_per_hour": len(recent_completed),
                    "avg_processing_time": None
                }
                
                # Calculate average processing time
                if recent_completed:
                    processing_times = []
                    for job in recent_completed:
                        started = job.get("started_at")
                        completed = job.get("completed_at")
                        
                        if started and completed:
                            start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
                            end_time = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                            duration = (end_time - start_time).total_seconds()
                            processing_times.append(duration)
                    
                    if processing_times:
                        throughput["avg_processing_time"] = sum(processing_times) / len(processing_times)
                
                self.validation_results["checks"].append({
                    "name": "Job Throughput",
                    "status": "measured",
                    "details": throughput
                })
                
                return throughput
                
            else:
                return {}
                
        except Exception as e:
            self.validation_results["issues"].append({
                "check": "Job Throughput",
                "issue": str(e)
            })
            return {}
    
    def generate_report(self):
        """Generate worker validation report."""
        print("\n" + "="*50)
        print("WORKER VALIDATION REPORT")
        print("="*50)
        
        # Determine overall worker health
        if len(self.validation_results["issues"]) == 0:
            self.validation_results["worker_health"] = "healthy"
            print("\n✅ Worker Status: HEALTHY")
        elif len(self.validation_results["issues"]) < 3:
            self.validation_results["worker_health"] = "degraded"
            print("\n⚠️  Worker Status: DEGRADED")
        else:
            self.validation_results["worker_health"] = "unhealthy"
            print("\n❌ Worker Status: UNHEALTHY")
        
        # Print checks
        print("\n📋 Validation Checks:")
        for check in self.validation_results["checks"]:
            status_icon = "✅" if check["status"] in ["healthy", "working", "running"] else "⚠️"
            print(f"  {status_icon} {check['name']}: {check['status']}")
            
            if isinstance(check.get("details"), dict):
                for key, value in check["details"].items():
                    print(f"      {key}: {value}")
        
        # Print issues
        if self.validation_results["issues"]:
            print(f"\n❌ Issues Found ({len(self.validation_results['issues'])}):")
            for issue in self.validation_results["issues"]:
                print(f"  - {issue['check']}: {issue['issue']}")
        
        # Recommendations
        print("\n💡 Recommendations:")
        
        if self.validation_results["worker_health"] == "unhealthy":
            print("  1. Check worker logs for errors")
            print("  2. Verify database connectivity")
            print("  3. Ensure worker container is running")
            print("  4. Check Redis/queue configuration")
        elif self.validation_results["worker_health"] == "degraded":
            print("  1. Monitor worker performance")
            print("  2. Check for stuck jobs")
            print("  3. Review error logs")
        else:
            print("  - Worker is functioning properly")
            print("  - Continue monitoring for issues")
        
        # Save report
        with open("worker_validation_report.json", "w") as f:
            json.dump(self.validation_results, f, indent=2)
        
        print("\n📄 Detailed report saved to worker_validation_report.json")
    
    def run_validation(self):
        """Run complete worker validation."""
        print("Starting Worker Validation...")
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now()}")
        print("-" * 50)
        
        # Run all checks
        self.check_worker_configuration()
        queue_health = self.check_job_queue_health()
        job_processed = self.test_job_processing()
        throughput = self.analyze_job_throughput()
        
        # Generate report
        self.generate_report()
        
        # Return status
        return self.validation_results["worker_health"]


def main():
    """Main entry point."""
    # Get target URL from command line or use default
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://hoistscraper.onrender.com"
    
    # Run validation
    validator = WorkerValidator(base_url)
    health_status = validator.run_validation()
    
    # Exit with appropriate code
    if health_status == "healthy":
        sys.exit(0)
    elif health_status == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()