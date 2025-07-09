#!/usr/bin/env python3
"""
HoistScout Job Monitoring Dashboard (Simple Version)

A lightweight monitoring tool for tracking job processing status without external dependencies.

Usage:
    python monitor_jobs_simple.py                # Basic monitoring
    python monitor_jobs_simple.py --interval 3   # Update every 3 seconds
"""

import os
import sys
import time
import json
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.parse

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class SimpleJobMonitor:
    """Simple job monitor without external dependencies"""
    
    def __init__(self, api_url: str = "http://localhost:8000", redis_url: str = None):
        self.api_url = api_url.rstrip('/')
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.auth_token = None
        self.start_time = datetime.utcnow()
    
    def authenticate(self, username: str = "demo", password: str = "demo123"):
        """Authenticate with the API"""
        try:
            data = urllib.parse.urlencode({
                "username": username,
                "password": password
            }).encode()
            
            req = urllib.request.Request(
                f"{self.api_url}/api/auth/login",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode())
                self.auth_token = result.get("access_token")
                return True
        except Exception as e:
            print(f"Authentication failed: {e}")
        return False
    
    def get_api_data(self, endpoint: str) -> Optional[Dict]:
        """Get data from API endpoint"""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            req = urllib.request.Request(
                f"{self.api_url}{endpoint}",
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        health_data = self.get_api_data("/api/health")
        if health_data and not health_data.get("error"):
            return {
                "api_healthy": True,
                "redis_connected": health_data.get("redis", {}).get("connected", False),
                "redis_latency": health_data.get("redis", {}).get("ping_latency_ms"),
                "celery_connected": health_data.get("celery", {}).get("connected", False),
                "celery_queues": health_data.get("celery", {}).get("queue_count", 0)
            }
        return {
            "api_healthy": False,
            "redis_connected": False,
            "error": health_data.get("error", "Unknown error")
        }
    
    def get_redis_status(self) -> Dict[str, Any]:
        """Get Redis queue status"""
        redis_data = self.get_api_data("/api/health/redis")
        if redis_data and not redis_data.get("error"):
            return {
                "connected": redis_data.get("connection", {}).get("status") == "connected",
                "latency_ms": redis_data.get("connection", {}).get("latency_ms"),
                "queues": redis_data.get("celery", {}).get("queues", {}),
                "total_tasks": redis_data.get("celery", {}).get("total_tasks", 0),
                "unacked_tasks": redis_data.get("celery", {}).get("unacked_tasks", 0),
                "memory_usage": redis_data.get("redis_info", {}).get("used_memory_human", "N/A")
            }
        return {"connected": False, "error": redis_data.get("error", "Unknown error")}
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
        jobs_data = self.get_api_data("/api/scraping/jobs?limit=100")
        
        if isinstance(jobs_data, list):
            stats = {
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "recent_jobs": [],
                "total": len(jobs_data)
            }
            
            for job in jobs_data:
                status = job.get("status", "unknown")
                if status in stats:
                    stats[status] += 1
            
            stats["recent_jobs"] = jobs_data[:10]
            return stats
        
        return {"error": "Failed to fetch jobs"}
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get overall dashboard statistics"""
        stats_data = self.get_api_data("/api/stats")
        if stats_data and not stats_data.get("error"):
            return stats_data
        return {}
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds/3600)
            minutes = int((seconds%3600)/60)
            return f"{hours}h {minutes}m"
    
    def print_dashboard(self):
        """Print dashboard to console"""
        self.clear_screen()
        
        # Header
        print("=" * 80)
        print("HoistScout Job Monitoring Dashboard".center(80))
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
        print("=" * 80)
        
        # Get all data
        health = self.get_health_status()
        redis = self.get_redis_status()
        jobs = self.get_job_stats()
        stats = self.get_dashboard_stats()
        
        # System Health
        print("\nSYSTEM HEALTH")
        print("-" * 40)
        print(f"API Status:      {'✅ Online' if health.get('api_healthy') else '❌ Offline'}")
        print(f"Redis Status:    {'✅ Connected' if redis.get('connected') else '❌ Disconnected'}")
        if redis.get('latency_ms'):
            print(f"Redis Latency:   {redis['latency_ms']}ms")
        print(f"Workers:         {'✅ Active' if health.get('celery_connected') else '❌ Inactive'}")
        if redis.get('memory_usage'):
            print(f"Memory Usage:    {redis['memory_usage']}")
        
        # Queue Status
        print("\nQUEUE STATUS")
        print("-" * 40)
        if redis.get('queues'):
            for queue_name, queue_info in redis['queues'].items():
                if isinstance(queue_info, dict):
                    length = queue_info.get('length', 0)
                else:
                    length = queue_info
                print(f"{queue_name:20} {length:5} tasks")
        print(f"{'Total Tasks:':20} {redis.get('total_tasks', 0):5} tasks")
        print(f"{'Unacked Tasks:':20} {redis.get('unacked_tasks', 0):5} tasks")
        
        # Job Statistics
        print("\nJOB STATISTICS")
        print("-" * 40)
        if not jobs.get("error"):
            total_jobs = jobs.get("total", 0)
            print(f"⏳ Pending:      {jobs.get('pending', 0):5} ({jobs.get('pending', 0)/max(total_jobs,1)*100:5.1f}%)")
            print(f"🏃 Running:      {jobs.get('running', 0):5} ({jobs.get('running', 0)/max(total_jobs,1)*100:5.1f}%)")
            print(f"✅ Completed:    {jobs.get('completed', 0):5} ({jobs.get('completed', 0)/max(total_jobs,1)*100:5.1f}%)")
            print(f"❌ Failed:       {jobs.get('failed', 0):5} ({jobs.get('failed', 0)/max(total_jobs,1)*100:5.1f}%)")
            print(f"🚫 Cancelled:    {jobs.get('cancelled', 0):5} ({jobs.get('cancelled', 0)/max(total_jobs,1)*100:5.1f}%)")
            print(f"{'Total Jobs:':17} {total_jobs:5}")
        else:
            print(f"Error: {jobs.get('error')}")
        
        # Dashboard Stats
        if stats:
            print("\nOVERALL STATISTICS")
            print("-" * 40)
            print(f"Total Sites:     {stats.get('total_sites', 0)}")
            print(f"Total Jobs:      {stats.get('total_jobs', 0)}")
            print(f"Opportunities:   {stats.get('total_opportunities', 0)}")
            print(f"Jobs This Week:  {stats.get('jobs_this_week', 0)}")
            if stats.get('last_scrape'):
                last_scrape = datetime.fromisoformat(stats['last_scrape'].replace('Z', '+00:00'))
                time_ago = datetime.utcnow() - last_scrape.replace(tzinfo=None)
                print(f"Last Scrape:     {self.format_duration(time_ago.total_seconds())} ago")
        
        # Recent Jobs
        print("\nRECENT JOBS (Last 10)")
        print("-" * 80)
        print(f"{'ID':>6} {'Website':>8} {'Status':^12} {'Created':^20} {'Duration':>10}")
        print("-" * 80)
        
        recent_jobs = jobs.get("recent_jobs", [])
        for job in recent_jobs[:10]:
            job_id = str(job.get("id", "N/A"))[:6]
            website_id = str(job.get("website_id", "N/A"))[:8]
            status = job.get("status", "unknown")
            
            # Status emoji
            status_emoji = {
                "pending": "⏳",
                "running": "🏃",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(status, "❓")
            
            # Format created time
            created_at = job.get("created_at", "")
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_str = created_time.strftime("%m/%d %H:%M:%S")
                    
                    # Calculate duration
                    if job.get("completed_at"):
                        completed_time = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
                        duration = (completed_time - created_time).total_seconds()
                        duration_str = self.format_duration(duration)
                    elif status == "running":
                        duration = (datetime.utcnow() - created_time.replace(tzinfo=None)).total_seconds()
                        duration_str = f"{self.format_duration(duration)} ⏱️"
                    else:
                        duration_str = "-"
                except:
                    created_str = created_at[:16]
                    duration_str = "-"
            else:
                created_str = "-"
                duration_str = "-"
            
            print(f"{job_id:>6} {website_id:>8} {status_emoji} {status:^10} {created_str:^20} {duration_str:>10}")
        
        # Alerts
        alerts = []
        
        # Check for stuck jobs
        if recent_jobs:
            for job in recent_jobs:
                if job.get("status") == "pending":
                    try:
                        created_time = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
                        if (datetime.utcnow() - created_time.replace(tzinfo=None)) > timedelta(minutes=10):
                            alerts.append(f"Job {job['id']} stuck in pending for >10 minutes")
                    except:
                        pass
        
        if not redis.get("connected"):
            alerts.append("Redis is not connected")
        
        if not health.get("celery_connected"):
            alerts.append("No workers available")
        
        if alerts:
            print("\nALERTS")
            print("-" * 40)
            for alert in alerts:
                print(f"⚠️  {alert}")
        
        # Footer
        print("\n" + "=" * 80)
        print("Press Ctrl+C to exit".center(80))
        print("=" * 80)
    
    def run(self, update_interval: int = 5):
        """Run the monitoring dashboard"""
        print("Starting HoistScout Job Monitor...")
        print(f"Update interval: {update_interval} seconds")
        print("Authenticating...")
        
        if not self.authenticate():
            print("Warning: Failed to authenticate. Running with limited functionality.")
            time.sleep(2)
        
        try:
            while True:
                self.print_dashboard()
                time.sleep(update_interval)
        except KeyboardInterrupt:
            print("\n\nDashboard stopped.")


def main():
    parser = argparse.ArgumentParser(description='HoistScout Job Monitoring Dashboard (Simple Version)')
    parser.add_argument('--interval', type=int, default=5,
                        help='Update interval in seconds (default: 5)')
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='API URL (default: http://localhost:8000)')
    parser.add_argument('--username', default='demo',
                        help='API username (default: demo)')
    parser.add_argument('--password', default='demo123',
                        help='API password (default: demo123)')
    
    args = parser.parse_args()
    
    # Check for production environment
    if os.getenv('ENVIRONMENT') == 'production' or 'render.com' in args.api_url:
        args.api_url = 'https://hoistscout-api.onrender.com'
    
    monitor = SimpleJobMonitor(api_url=args.api_url)
    monitor.run(update_interval=args.interval)


if __name__ == "__main__":
    main()