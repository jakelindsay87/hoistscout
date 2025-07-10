#!/usr/bin/env python3
"""
Worker with health check endpoint for Render deployment.
This runs both the Celery worker and a simple HTTP server for health checks.
"""
import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import signal


class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Worker is healthy")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress request logs
        pass


def run_health_server(port=8080):
    """Run health check HTTP server."""
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()


def run_celery_worker():
    """Run the Celery worker."""
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.worker",
        "worker",
        "--loglevel=info",
        "--pool=solo",
    ]

    process = subprocess.Popen(cmd)

    def signal_handler(signum, frame):
        print("Shutting down worker...")
        process.terminate()
        process.wait()
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    process.wait()


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8080))

    # Start health check server in a thread
    health_thread = threading.Thread(target=run_health_server, args=(port,))
    health_thread.daemon = True
    health_thread.start()

    # Give health server time to start
    time.sleep(2)

    # Run Celery worker in main thread
    run_celery_worker()
