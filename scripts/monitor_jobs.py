#!/usr/bin/env python3
"""
HoistScout Job Monitoring Dashboard

A comprehensive monitoring tool for tracking job processing status,
Redis queue health, and worker status with real-time updates.

Usage:
    python monitor_jobs.py                # CLI mode (default)
    python monitor_jobs.py --mode web     # Web dashboard mode
    python monitor_jobs.py --interval 3   # Update every 3 seconds
"""

import os
import sys
import time
import json
import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
import statistics

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import redis.asyncio as redis
import requests
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

# For web mode
try:
    from flask import Flask, render_template_string, jsonify
    import threading
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class JobMonitor:
    """Monitor job processing and system health"""
    
    def __init__(self, api_url: str = "http://localhost:8000", redis_url: str = None):
        self.api_url = api_url.rstrip('/')
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.console = Console()
        self.auth_token = None
        self.metrics_history = deque(maxlen=100)  # Keep last 100 data points
        self.start_time = datetime.utcnow()
        
        # Try to get Redis URL from environment or config
        if not self.redis_url:
            try:
                from app.config import get_settings
                settings = get_settings()
                self.redis_url = settings.redis_url
            except:
                pass
    
    async def authenticate(self, username: str = "demo", password: str = "demo123"):
        """Authenticate with the API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/login",
                data={"username": username, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                return True
        except Exception as e:
            self.console.print(f"[red]Authentication failed: {e}[/red]")
        return False
    
    async def get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis connection and queue statistics"""
        stats = {
            "connected": False,
            "error": None,
            "queues": {},
            "total_tasks": 0,
            "memory_usage": "N/A",
            "clients_connected": 0,
            "uptime_days": 0,
            "ping_latency_ms": None
        }
        
        r = None
        try:
            start_time = datetime.utcnow()
            r = redis.from_url(self.redis_url, decode_responses=True)
            await r.ping()
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            stats["connected"] = True
            stats["ping_latency_ms"] = round(latency, 2)
            
            # Get Redis server info
            info = await r.info()
            stats["memory_usage"] = info.get("used_memory_human", "N/A")
            stats["clients_connected"] = info.get("connected_clients", 0)
            stats["uptime_days"] = info.get("uptime_in_days", 0)
            
            # Check Celery queues
            celery_queues = ["celery", "celery.priority.high", "celery.priority.low"]
            for queue_name in celery_queues:
                try:
                    queue_length = await r.llen(queue_name)
                    if queue_length > 0:
                        stats["queues"][queue_name] = queue_length
                        stats["total_tasks"] += queue_length
                except:
                    pass
            
            # Check for unacknowledged tasks
            try:
                unacked_count = await r.hlen("unacked")
                stats["unacked_tasks"] = unacked_count
            except:
                stats["unacked_tasks"] = 0
                
        except Exception as e:
            stats["error"] = str(e)
        finally:
            if r:
                await r.close()
        
        return stats
    
    async def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics from the API"""
        stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "recent_jobs": [],
            "processing_rate": 0,
            "error": None
        }
        
        if not self.auth_token:
            stats["error"] = "Not authenticated"
            return stats
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Get job list
            response = requests.get(
                f"{self.api_url}/api/scraping/jobs?limit=100",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                jobs = response.json()
                
                # Count by status
                for job in jobs:
                    status = job.get("status", "unknown")
                    if status in stats:
                        stats[status] += 1
                
                # Get recent jobs (last 10)
                stats["recent_jobs"] = jobs[:10]
                
                # Calculate processing rate (jobs per hour)
                if len(self.metrics_history) > 1:
                    completed_count = sum(1 for m in self.metrics_history if m.get("jobs", {}).get("completed", 0) > 0)
                    time_span_hours = len(self.metrics_history) * 5 / 3600  # 5 seconds per data point
                    if time_span_hours > 0:
                        stats["processing_rate"] = round(completed_count / time_span_hours, 2)
                        
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
    
    async def get_worker_health(self) -> Dict[str, Any]:
        """Check worker health status"""
        health = {
            "api_healthy": False,
            "redis_healthy": False,
            "workers_available": False,
            "last_job_time": None,
            "alerts": []
        }
        
        try:
            # Check API health
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                health["api_healthy"] = True
                data = response.json()
                health["redis_healthy"] = data.get("redis", {}).get("connected", False)
                health["workers_available"] = data.get("celery", {}).get("connected", False)
        except:
            health["alerts"].append("API is not responding")
        
        # Check for stuck jobs
        if hasattr(self, '_last_job_stats'):
            last_stats = self._last_job_stats
            current_time = datetime.utcnow()
            
            # Alert if jobs are stuck in pending for too long
            if last_stats.get("pending", 0) > 0:
                oldest_pending = min(
                    (job for job in last_stats.get("recent_jobs", []) if job.get("status") == "pending"),
                    key=lambda x: x.get("created_at", ""),
                    default=None
                )
                if oldest_pending:
                    created_at = datetime.fromisoformat(oldest_pending["created_at"].replace("Z", "+00:00"))
                    if (current_time - created_at.replace(tzinfo=None)) > timedelta(minutes=10):
                        health["alerts"].append(f"Job {oldest_pending['id']} stuck in pending for >10 minutes")
        
        return health
    
    async def collect_metrics(self):
        """Collect all metrics"""
        redis_stats = await self.get_redis_stats()
        job_stats = await self.get_job_stats()
        worker_health = await self.get_worker_health()
        
        # Store for history
        self._last_job_stats = job_stats
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "redis": redis_stats,
            "jobs": job_stats,
            "health": worker_health,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def create_dashboard_layout(self, metrics: Dict[str, Any]) -> Layout:
        """Create Rich layout for CLI dashboard"""
        layout = Layout()
        
        # Header
        header = Panel(
            Align.center(
                Text("HoistScout Job Monitoring Dashboard", style="bold magenta"),
                vertical="middle"
            ),
            height=3
        )
        
        # Main layout
        layout.split(
            Layout(header, size=3),
            Layout(name="body")
        )
        
        # Body sections
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        
        # Left column - System Health
        redis_stats = metrics["redis"]
        health = metrics["health"]
        
        health_status = "✅ Healthy" if redis_stats["connected"] else "❌ Disconnected"
        latency_text = f"{redis_stats['ping_latency_ms']}ms" if redis_stats["ping_latency_ms"] else "N/A"
        
        system_table = Table(title="System Health", expand=True)
        system_table.add_column("Component", style="cyan")
        system_table.add_column("Status", style="green")
        
        system_table.add_row("Redis", health_status)
        system_table.add_row("API", "✅ Online" if health["api_healthy"] else "❌ Offline")
        system_table.add_row("Workers", "✅ Active" if health["workers_available"] else "❌ Inactive")
        system_table.add_row("Latency", latency_text)
        system_table.add_row("Memory", str(redis_stats["memory_usage"]))
        system_table.add_row("Clients", str(redis_stats["clients_connected"]))
        system_table.add_row("Uptime", f"{redis_stats['uptime_days']} days")
        
        # Queue Status
        queue_table = Table(title="Queue Status", expand=True)
        queue_table.add_column("Queue", style="cyan")
        queue_table.add_column("Length", style="yellow")
        
        for queue_name, length in redis_stats["queues"].items():
            queue_table.add_row(queue_name, str(length))
        
        queue_table.add_row("Total Tasks", str(redis_stats["total_tasks"]), style="bold")
        queue_table.add_row("Unacked", str(redis_stats.get("unacked_tasks", 0)))
        
        layout["left"].split(
            Layout(system_table),
            Layout(queue_table)
        )
        
        # Right column - Job Statistics
        job_stats = metrics["jobs"]
        
        # Job status summary
        status_table = Table(title="Job Statistics", expand=True)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="yellow")
        status_table.add_column("Visual", style="white")
        
        total_jobs = sum(job_stats.get(s, 0) for s in ["pending", "running", "completed", "failed", "cancelled"])
        
        for status, emoji in [
            ("pending", "⏳"),
            ("running", "🏃"),
            ("completed", "✅"),
            ("failed", "❌"),
            ("cancelled", "🚫")
        ]:
            count = job_stats.get(status, 0)
            bar_length = int((count / max(total_jobs, 1)) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            status_table.add_row(f"{emoji} {status.capitalize()}", str(count), bar)
        
        # Recent jobs
        recent_table = Table(title="Recent Jobs (Last 10)", expand=True)
        recent_table.add_column("ID", style="cyan", width=8)
        recent_table.add_column("Website", style="white", width=10)
        recent_table.add_column("Status", style="yellow", width=10)
        recent_table.add_column("Created", style="green", width=20)
        recent_table.add_column("Duration", style="magenta", width=10)
        
        for job in job_stats.get("recent_jobs", [])[:10]:
            job_id = str(job.get("id", "N/A"))
            website_id = str(job.get("website_id", "N/A"))
            status = job.get("status", "unknown")
            
            # Status emoji
            status_emoji = {
                "pending": "⏳",
                "running": "🏃",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫"
            }.get(status, "❓")
            
            # Calculate duration
            created_at = job.get("created_at", "")
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    if job.get("completed_at"):
                        completed_time = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
                        duration = (completed_time - created_time).total_seconds()
                        duration_str = f"{int(duration)}s"
                    elif status == "running":
                        duration = (datetime.utcnow() - created_time.replace(tzinfo=None)).total_seconds()
                        duration_str = f"{int(duration)}s ⏱️"
                    else:
                        duration_str = "-"
                except:
                    created_str = created_at[:19]
                    duration_str = "-"
            else:
                created_str = "-"
                duration_str = "-"
            
            recent_table.add_row(
                job_id,
                website_id,
                f"{status_emoji} {status}",
                created_str,
                duration_str
            )
        
        # Alerts
        alerts = health.get("alerts", [])
        if alerts:
            alert_text = "\n".join(f"⚠️ {alert}" for alert in alerts)
            alert_panel = Panel(alert_text, title="Alerts", style="red")
        else:
            alert_panel = Panel("✅ No alerts", title="Alerts", style="green")
        
        # Metrics
        metrics_text = f"""
Processing Rate: {job_stats.get('processing_rate', 0)} jobs/hour
Uptime: {int(metrics['uptime_seconds'] / 60)} minutes
Last Update: {datetime.utcnow().strftime('%H:%M:%S')}
        """
        metrics_panel = Panel(metrics_text.strip(), title="Metrics")
        
        layout["right"].split(
            Layout(status_table, size=8),
            Layout(recent_table, size=15),
            Layout(alert_panel, size=4),
            Layout(metrics_panel, size=4)
        )
        
        return layout
    
    async def run_cli_dashboard(self, update_interval: int = 5):
        """Run the CLI dashboard with live updates"""
        # Authenticate first
        if not await self.authenticate():
            self.console.print("[red]Failed to authenticate. Using limited functionality.[/red]")
        
        self.console.print("[green]Starting HoistScout Job Monitor...[/green]")
        self.console.print(f"[yellow]Update interval: {update_interval} seconds[/yellow]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        
        with Live(console=self.console, refresh_per_second=1) as live:
            while True:
                try:
                    metrics = await self.collect_metrics()
                    layout = self.create_dashboard_layout(metrics)
                    live.update(layout)
                    await asyncio.sleep(update_interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(update_interval)
        
        self.console.print("\n[yellow]Dashboard stopped.[/yellow]")
    
    def get_web_dashboard_data(self) -> Dict[str, Any]:
        """Get data for web dashboard"""
        if not self.metrics_history:
            return {"error": "No data available"}
        
        latest = self.metrics_history[-1]
        
        # Prepare time series data
        timestamps = []
        pending_series = []
        running_series = []
        completed_series = []
        queue_series = []
        
        for metric in list(self.metrics_history)[-20:]:  # Last 20 data points
            timestamp = metric["timestamp"]
            timestamps.append(timestamp)
            pending_series.append(metric["jobs"]["pending"])
            running_series.append(metric["jobs"]["running"])
            completed_series.append(metric["jobs"]["completed"])
            queue_series.append(metric["redis"]["total_tasks"])
        
        return {
            "current": latest,
            "timeseries": {
                "timestamps": timestamps,
                "pending": pending_series,
                "running": running_series,
                "completed": completed_series,
                "queue": queue_series
            }
        }
    
    async def run_web_dashboard(self, port: int = 5555, update_interval: int = 5):
        """Run the web dashboard"""
        if not FLASK_AVAILABLE:
            self.console.print("[red]Flask is not installed. Install with: pip install flask[/red]")
            return
        
        app = Flask(__name__)
        
        # HTML template for web dashboard
        dashboard_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HoistScout Job Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #bb86fc;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .card h2 {
            margin-top: 0;
            color: #03dac6;
            font-size: 1.2em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
        }
        .metric-value {
            font-weight: bold;
            color: #ffb86c;
        }
        .status-ok { color: #50fa7b; }
        .status-error { color: #ff5555; }
        .chart-container {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .recent-jobs {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid #444;
        }
        th {
            color: #03dac6;
        }
        .alert {
            background: #ff5555;
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .refresh-info {
            text-align: center;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HoistScout Job Monitoring Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>System Health</h2>
                <div id="system-health"></div>
            </div>
            
            <div class="card">
                <h2>Job Statistics</h2>
                <div id="job-stats"></div>
            </div>
            
            <div class="card">
                <h2>Queue Status</h2>
                <div id="queue-status"></div>
            </div>
        </div>
        
        <div id="alerts"></div>
        
        <div class="chart-container">
            <h2>Job Processing Trends</h2>
            <canvas id="jobChart"></canvas>
        </div>
        
        <div class="recent-jobs">
            <h2>Recent Jobs</h2>
            <div id="recent-jobs-table"></div>
        </div>
        
        <div class="refresh-info">
            Auto-refreshing every 5 seconds | <span id="last-update"></span>
        </div>
    </div>
    
    <script>
        let chart = null;
        
        function updateDashboard() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }
                    
                    // Update system health
                    const health = data.current.health;
                    const redis = data.current.redis;
                    document.getElementById('system-health').innerHTML = `
                        <div class="metric">
                            <span>Redis</span>
                            <span class="metric-value ${redis.connected ? 'status-ok' : 'status-error'}">
                                ${redis.connected ? '✅ Connected' : '❌ Disconnected'}
                            </span>
                        </div>
                        <div class="metric">
                            <span>API</span>
                            <span class="metric-value ${health.api_healthy ? 'status-ok' : 'status-error'}">
                                ${health.api_healthy ? '✅ Online' : '❌ Offline'}
                            </span>
                        </div>
                        <div class="metric">
                            <span>Workers</span>
                            <span class="metric-value ${health.workers_available ? 'status-ok' : 'status-error'}">
                                ${health.workers_available ? '✅ Active' : '❌ Inactive'}
                            </span>
                        </div>
                        <div class="metric">
                            <span>Latency</span>
                            <span class="metric-value">${redis.ping_latency_ms || 'N/A'}ms</span>
                        </div>
                        <div class="metric">
                            <span>Memory</span>
                            <span class="metric-value">${redis.memory_usage}</span>
                        </div>
                    `;
                    
                    // Update job stats
                    const jobs = data.current.jobs;
                    document.getElementById('job-stats').innerHTML = `
                        <div class="metric">
                            <span>⏳ Pending</span>
                            <span class="metric-value">${jobs.pending}</span>
                        </div>
                        <div class="metric">
                            <span>🏃 Running</span>
                            <span class="metric-value">${jobs.running}</span>
                        </div>
                        <div class="metric">
                            <span>✅ Completed</span>
                            <span class="metric-value">${jobs.completed}</span>
                        </div>
                        <div class="metric">
                            <span>❌ Failed</span>
                            <span class="metric-value">${jobs.failed}</span>
                        </div>
                        <div class="metric">
                            <span>📊 Processing Rate</span>
                            <span class="metric-value">${jobs.processing_rate} jobs/hour</span>
                        </div>
                    `;
                    
                    // Update queue status
                    const queues = redis.queues;
                    let queueHtml = '';
                    for (const [name, length] of Object.entries(queues)) {
                        queueHtml += `
                            <div class="metric">
                                <span>${name}</span>
                                <span class="metric-value">${length}</span>
                            </div>
                        `;
                    }
                    queueHtml += `
                        <div class="metric">
                            <span><strong>Total Tasks</strong></span>
                            <span class="metric-value"><strong>${redis.total_tasks}</strong></span>
                        </div>
                        <div class="metric">
                            <span>Unacked</span>
                            <span class="metric-value">${redis.unacked_tasks || 0}</span>
                        </div>
                    `;
                    document.getElementById('queue-status').innerHTML = queueHtml;
                    
                    // Update alerts
                    const alerts = health.alerts || [];
                    if (alerts.length > 0) {
                        document.getElementById('alerts').innerHTML = alerts
                            .map(alert => `<div class="alert">⚠️ ${alert}</div>`)
                            .join('');
                    } else {
                        document.getElementById('alerts').innerHTML = '';
                    }
                    
                    // Update recent jobs
                    const recentJobs = jobs.recent_jobs || [];
                    if (recentJobs.length > 0) {
                        let tableHtml = '<table><tr><th>ID</th><th>Website</th><th>Status</th><th>Created</th></tr>';
                        for (const job of recentJobs.slice(0, 10)) {
                            const statusEmoji = {
                                'pending': '⏳',
                                'running': '🏃',
                                'completed': '✅',
                                'failed': '❌',
                                'cancelled': '🚫'
                            }[job.status] || '❓';
                            
                            tableHtml += `
                                <tr>
                                    <td>${job.id}</td>
                                    <td>${job.website_id}</td>
                                    <td>${statusEmoji} ${job.status}</td>
                                    <td>${new Date(job.created_at).toLocaleString()}</td>
                                </tr>
                            `;
                        }
                        tableHtml += '</table>';
                        document.getElementById('recent-jobs-table').innerHTML = tableHtml;
                    }
                    
                    // Update chart
                    updateChart(data.timeseries);
                    
                    // Update last update time
                    document.getElementById('last-update').textContent = 
                        'Last update: ' + new Date().toLocaleTimeString();
                })
                .catch(error => console.error('Error fetching metrics:', error));
        }
        
        function updateChart(timeseries) {
            const ctx = document.getElementById('jobChart').getContext('2d');
            
            if (!chart) {
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            {
                                label: 'Pending',
                                data: [],
                                borderColor: '#ffb86c',
                                backgroundColor: 'rgba(255, 184, 108, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Running',
                                data: [],
                                borderColor: '#8be9fd',
                                backgroundColor: 'rgba(139, 233, 253, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Completed',
                                data: [],
                                borderColor: '#50fa7b',
                                backgroundColor: 'rgba(80, 250, 123, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Queue Length',
                                data: [],
                                borderColor: '#bd93f9',
                                backgroundColor: 'rgba(189, 147, 249, 0.1)',
                                tension: 0.4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                ticks: { color: '#e0e0e0' },
                                grid: { color: '#444' }
                            },
                            y: {
                                ticks: { color: '#e0e0e0' },
                                grid: { color: '#444' }
                            }
                        },
                        plugins: {
                            legend: {
                                labels: { color: '#e0e0e0' }
                            }
                        }
                    }
                });
            }
            
            // Update chart data
            chart.data.labels = timeseries.timestamps.map(ts => 
                new Date(ts).toLocaleTimeString()
            );
            chart.data.datasets[0].data = timeseries.pending;
            chart.data.datasets[1].data = timeseries.running;
            chart.data.datasets[2].data = timeseries.completed;
            chart.data.datasets[3].data = timeseries.queue;
            chart.update();
        }
        
        // Initial load and set interval
        updateDashboard();
        setInterval(updateDashboard, 5000);
    </script>
</body>
</html>
        '''
        
        @app.route('/')
        def index():
            return render_template_string(dashboard_html)
        
        @app.route('/api/metrics')
        def metrics():
            return jsonify(self.get_web_dashboard_data())
        
        # Start background metric collection
        async def collect_metrics_loop():
            if not await self.authenticate():
                self.console.print("[yellow]Running with limited functionality (no auth)[/yellow]")
            
            while True:
                try:
                    await self.collect_metrics()
                except Exception as e:
                    self.console.print(f"[red]Metric collection error: {e}[/red]")
                await asyncio.sleep(update_interval)
        
        # Run metric collection in background
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(collect_metrics_loop())
        
        thread = threading.Thread(target=run_async_loop, daemon=True)
        thread.start()
        
        self.console.print(f"[green]Starting web dashboard on http://localhost:{port}[/green]")
        self.console.print("[dim]Press Ctrl+C to exit[/dim]\n")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=port, debug=False)


async def main():
    parser = argparse.ArgumentParser(description='HoistScout Job Monitoring Dashboard')
    parser.add_argument('--mode', choices=['cli', 'web'], default='cli',
                        help='Dashboard mode (default: cli)')
    parser.add_argument('--interval', type=int, default=5,
                        help='Update interval in seconds (default: 5)')
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='API URL (default: http://localhost:8000)')
    parser.add_argument('--redis-url', default=None,
                        help='Redis URL (default: from environment or config)')
    parser.add_argument('--port', type=int, default=5555,
                        help='Web dashboard port (default: 5555)')
    parser.add_argument('--username', default='demo',
                        help='API username (default: demo)')
    parser.add_argument('--password', default='demo123',
                        help='API password (default: demo123)')
    
    args = parser.parse_args()
    
    # Check for production environment
    if os.getenv('ENVIRONMENT') == 'production' or 'render.com' in args.api_url:
        args.api_url = 'https://hoistscout-api.onrender.com'
    
    monitor = JobMonitor(api_url=args.api_url, redis_url=args.redis_url)
    
    try:
        if args.mode == 'web':
            await monitor.run_web_dashboard(port=args.port, update_interval=args.interval)
        else:
            await monitor.run_cli_dashboard(update_interval=args.interval)
    except KeyboardInterrupt:
        print("\nShutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())