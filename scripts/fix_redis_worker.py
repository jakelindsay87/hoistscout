#!/usr/bin/env python3
"""
Redis Worker Connection Diagnostic and Fix Script
This script diagnoses and fixes Redis connection issues for the Celery worker.
"""

import os
import sys
import json
import socket
import ssl
import time
import subprocess
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def print_status(message: str, status: str = "INFO"):
    """Print a status message with formatting."""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"
    }
    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    print(f"{color}[{status}]{reset} {message}")

def check_environment_variables() -> Dict[str, str]:
    """Check and display all Redis-related environment variables."""
    print_section("Environment Variables")
    
    env_vars = {
        "REDIS_URL": os.environ.get("REDIS_URL"),
        "REDIS_HOST": os.environ.get("REDIS_HOST"),
        "REDIS_PORT": os.environ.get("REDIS_PORT"),
        "REDIS_PASSWORD": os.environ.get("REDIS_PASSWORD"),
        "REDIS_TLS_URL": os.environ.get("REDIS_TLS_URL"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        "RENDER": os.environ.get("RENDER"),
        "RENDER_SERVICE_NAME": os.environ.get("RENDER_SERVICE_NAME"),
    }
    
    for key, value in env_vars.items():
        if value:
            # Mask sensitive data
            if "PASSWORD" in key or "URL" in key:
                if value and len(value) > 20:
                    masked = value[:10] + "..." + value[-10:]
                else:
                    masked = "***"
                print(f"  {key}: {masked}")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: Not set")
    
    return env_vars

def parse_redis_url(url: str) -> Dict[str, Any]:
    """Parse Redis URL and extract components."""
    print_section("Redis URL Analysis")
    
    try:
        parsed = urlparse(url)
        components = {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port or 6379,
            "password": parsed.password,
            "path": parsed.path,
            "is_ssl": parsed.scheme in ["rediss", "redis+ssl"],
            "full_url": url
        }
        
        print(f"  Scheme: {components['scheme']}")
        print(f"  Host: {components['hostname']}")
        print(f"  Port: {components['port']}")
        print(f"  SSL/TLS: {components['is_ssl']}")
        print(f"  Has password: {'Yes' if components['password'] else 'No'}")
        
        return components
    except Exception as e:
        print_status(f"Failed to parse Redis URL: {e}", "ERROR")
        return {}

def test_network_connectivity(host: str, port: int, use_ssl: bool = False) -> bool:
    """Test basic network connectivity to Redis host."""
    print_section("Network Connectivity Test")
    
    try:
        # DNS resolution
        print(f"  Resolving {host}...")
        ip_address = socket.gethostbyname(host)
        print_status(f"DNS resolved to: {ip_address}", "SUCCESS")
        
        # TCP connection
        print(f"  Connecting to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        if use_ssl:
            context = ssl.create_default_context()
            # For Redis cloud services, we might need to disable hostname verification
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=host)
        
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print_status("TCP connection successful", "SUCCESS")
            return True
        else:
            print_status(f"TCP connection failed with code: {result}", "ERROR")
            return False
            
    except socket.gaierror as e:
        print_status(f"DNS resolution failed: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Network test failed: {e}", "ERROR")
        return False

def test_redis_connection(url: str) -> Tuple[bool, Optional[str]]:
    """Test actual Redis connection using redis-py."""
    print_section("Redis Connection Test")
    
    try:
        import redis
        
        # Parse URL components
        components = parse_redis_url(url)
        
        # Create connection based on URL type
        if components.get("is_ssl"):
            print("  Using SSL/TLS connection...")
            # For Redis cloud services
            client = redis.from_url(
                url,
                ssl_cert_reqs=None,
                ssl_keyfile=None,
                ssl_certfile=None,
                ssl_ca_certs=None,
                decode_responses=True
            )
        else:
            print("  Using standard connection...")
            client = redis.from_url(url, decode_responses=True)
        
        # Test PING
        print("  Sending PING command...")
        response = client.ping()
        if response:
            print_status("PING successful", "SUCCESS")
            
            # Get Redis info
            info = client.info()
            print(f"  Redis version: {info.get('redis_version', 'Unknown')}")
            print(f"  Connected clients: {info.get('connected_clients', 'Unknown')}")
            
            return True, None
        else:
            return False, "PING returned False"
            
    except ImportError:
        return False, "redis package not installed"
    except redis.ConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except redis.AuthenticationError as e:
        return False, f"Authentication error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)} ({type(e).__name__})"

def test_celery_connection(redis_url: str) -> Tuple[bool, Optional[str]]:
    """Test Celery broker connection."""
    print_section("Celery Connection Test")
    
    try:
        from celery import Celery
        
        print("  Creating Celery app...")
        app = Celery('test', broker=redis_url, backend=redis_url)
        
        # Configure Celery
        app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )
        
        print("  Testing broker connection...")
        # This will raise an exception if connection fails
        conn = app.connection()
        conn.ensure_connection(max_retries=3)
        
        print_status("Celery broker connection successful", "SUCCESS")
        
        # Try to get registered tasks
        print("  Checking task registry...")
        tasks = list(app.tasks.keys())
        print(f"  Found {len(tasks)} registered tasks")
        
        return True, None
        
    except ImportError:
        return False, "celery package not installed"
    except Exception as e:
        return False, f"Celery connection failed: {str(e)}"

def generate_render_config(redis_url: str) -> Dict[str, Any]:
    """Generate proper Render configuration based on Redis URL."""
    print_section("Render Configuration Generator")
    
    components = parse_redis_url(redis_url)
    
    # Determine if this is a Render Redis instance
    is_render_redis = "oregon-postgres.render.com" in redis_url or "redis.render.com" in redis_url
    
    config = {
        "environment_variables": {
            "REDIS_URL": redis_url,
            "PYTHONUNBUFFERED": "1",
            "CELERY_BROKER_URL": redis_url,
            "CELERY_RESULT_BACKEND": redis_url,
        },
        "worker_dockerfile": None,
        "notes": []
    }
    
    # If using SSL/TLS Redis
    if components.get("is_ssl"):
        config["notes"].append("Using SSL/TLS Redis connection")
        config["environment_variables"]["REDIS_TLS_URL"] = redis_url
        
        # Generate updated worker Dockerfile for SSL
        worker_dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including SSL libraries
RUN apt-get update && apt-get install -y \\
    curl \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code
COPY ./app /app/app
COPY ./pyproject.toml /app/pyproject.toml
COPY ./requirements.txt /app/requirements.txt

# Set Python path
ENV PYTHONPATH=/app

# Install Python dependencies with SSL support
RUN pip install --no-cache-dir \\
    celery[redis]==5.3.0 \\
    redis[hiredis]==5.0.1 \\
    hiredis==2.3.2 \\
    sqlalchemy[asyncio]==2.0.23 \\
    asyncpg==0.29.0 \\
    pydantic==2.10.2 \\
    pydantic-settings==2.6.1 \\
    playwright==1.43.0 \\
    httpx==0.26.0 \\
    python-dotenv==1.0.1 \\
    loguru==0.7.2 \\
    tenacity==8.2.3 \\
    beautifulsoup4==4.12.0 \\
    lxml==5.1.0

# Install additional dependencies
RUN pip install --no-cache-dir \\
    langchain==0.3.0 \\
    langchain-core==0.3.0 \\
    langchain-community==0.3.0 \\
    langsmith==0.1.125 \\
    google-generativeai==0.8.3 \\
    anthropic==0.39.0 \\
    openai==1.50.2 \\
    scrapegraphai==1.60.0

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Run the worker with proper SSL configuration
CMD ["python", "-m", "celery", "-A", "app.worker", "worker", "--loglevel=info", "--pool=solo"]
"""
        config["worker_dockerfile"] = worker_dockerfile
    
    # Additional Render-specific configurations
    if is_render_redis:
        config["notes"].append("Detected Render Redis instance")
        config["notes"].append("Ensure Redis service is in the same region as worker")
    
    return config

def test_minimal_worker(redis_url: str) -> bool:
    """Create and test a minimal Celery worker."""
    print_section("Minimal Worker Test")
    
    test_code = f"""
import os
os.environ['REDIS_URL'] = '{redis_url}'

from celery import Celery
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create minimal Celery app
app = Celery('minimal_test', broker='{redis_url}', backend='{redis_url}')

@app.task
def test_task(x, y):
    return x + y

if __name__ == '__main__':
    # Try to start worker
    try:
        logger.info("Starting minimal worker...")
        app.worker_main(['worker', '--loglevel=debug', '--pool=solo', '--concurrency=1'])
    except Exception as e:
        logger.error(f"Worker failed: {{e}}")
        raise
"""
    
    # Write test file
    test_file = "/tmp/test_celery_worker.py"
    with open(test_file, "w") as f:
        f.write(test_code)
    
    try:
        print("  Starting minimal worker (will run for 5 seconds)...")
        # Run worker for 5 seconds
        proc = subprocess.Popen(
            [sys.executable, test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for 5 seconds
        time.sleep(5)
        
        # Terminate worker
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        
        # Check output
        if "celery@" in stdout or "ready" in stdout.lower():
            print_status("Worker started successfully", "SUCCESS")
            return True
        else:
            print_status("Worker failed to start properly", "ERROR")
            if stderr:
                print("  Error output:")
                print(stderr[:500])
            return False
            
    except Exception as e:
        print_status(f"Test failed: {e}", "ERROR")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)

def generate_fixes(env_vars: Dict[str, str], test_results: Dict[str, Any]) -> None:
    """Generate specific fixes based on test results."""
    print_section("Recommended Fixes")
    
    redis_url = env_vars.get("REDIS_URL", "")
    
    # Fix 1: Environment Variables
    print("\n1. Environment Variables to Set:")
    print("   Add these to your Render service environment:")
    
    if test_results.get("is_ssl"):
        print(f"   REDIS_URL={redis_url}")
        print(f"   REDIS_TLS_URL={redis_url}")
        print(f"   CELERY_BROKER_URL={redis_url}")
        print(f"   CELERY_RESULT_BACKEND={redis_url}")
    else:
        print(f"   REDIS_URL={redis_url}")
        print(f"   CELERY_BROKER_URL={redis_url}")
        print(f"   CELERY_RESULT_BACKEND={redis_url}")
    
    print("   PYTHONUNBUFFERED=1")
    
    # Fix 2: Dockerfile updates
    if test_results.get("is_ssl"):
        print("\n2. Update Dockerfile.worker:")
        print("   - Add SSL support for Redis")
        print("   - Install hiredis for better performance")
        print("   - See generated Dockerfile.worker.fixed in scripts/")
    
    # Fix 3: Worker configuration
    print("\n3. Worker Configuration:")
    print("   Update app/worker.py to handle SSL connections:")
    print("""
   # In celery_app configuration
   if 'rediss://' in settings.redis_url or 'redis+ssl://' in settings.redis_url:
       celery_app.conf.redis_backend_use_ssl = {
           'ssl_cert_reqs': None,
           'ssl_keyfile': None,
           'ssl_certfile': None,
           'ssl_ca_certs': None,
       }
""")
    
    # Fix 4: Connection string format
    if not test_results.get("network_success"):
        print("\n4. Connection Issues:")
        print("   - Verify Redis service is running and accessible")
        print("   - Check if Redis is in the same Render region")
        print("   - Ensure Redis service allows external connections")
    
    # Fix 5: Generate fixed files
    if test_results.get("render_config"):
        config = test_results["render_config"]
        
        # Save Dockerfile if needed
        if config.get("worker_dockerfile"):
            dockerfile_path = os.path.join(os.path.dirname(__file__), "Dockerfile.worker.fixed")
            with open(dockerfile_path, "w") as f:
                f.write(config["worker_dockerfile"])
            print(f"\n   Generated: {dockerfile_path}")
        
        # Save environment variables
        env_path = os.path.join(os.path.dirname(__file__), "render_env_vars.txt")
        with open(env_path, "w") as f:
            f.write("# Environment variables for Render\n")
            for key, value in config["environment_variables"].items():
                f.write(f"{key}={value}\n")
        print(f"   Generated: {env_path}")

def main():
    """Main diagnostic function."""
    print("\n" + "=" * 60)
    print("  HoistScout Redis Worker Diagnostic Tool")
    print("=" * 60)
    
    # Check environment
    env_vars = check_environment_variables()
    
    # Get Redis URL
    redis_url = env_vars.get("REDIS_URL")
    if not redis_url:
        print_status("REDIS_URL not set. Please set it and run again.", "ERROR")
        sys.exit(1)
    
    # Parse URL
    components = parse_redis_url(redis_url)
    if not components:
        print_status("Failed to parse Redis URL", "ERROR")
        sys.exit(1)
    
    # Test results
    test_results = {
        "is_ssl": components.get("is_ssl", False),
        "network_success": False,
        "redis_success": False,
        "celery_success": False,
        "worker_success": False,
    }
    
    # Network connectivity test
    if components.get("hostname") and components.get("port"):
        test_results["network_success"] = test_network_connectivity(
            components["hostname"], 
            components["port"], 
            components.get("is_ssl", False)
        )
    
    # Redis connection test
    redis_success, redis_error = test_redis_connection(redis_url)
    test_results["redis_success"] = redis_success
    test_results["redis_error"] = redis_error
    
    if redis_success:
        # Celery connection test
        celery_success, celery_error = test_celery_connection(redis_url)
        test_results["celery_success"] = celery_success
        test_results["celery_error"] = celery_error
        
        if celery_success:
            # Minimal worker test
            test_results["worker_success"] = test_minimal_worker(redis_url)
    
    # Generate Render configuration
    test_results["render_config"] = generate_render_config(redis_url)
    
    # Summary
    print_section("Test Summary")
    print(f"  Network connectivity: {'✓' if test_results['network_success'] else '✗'}")
    print(f"  Redis connection: {'✓' if test_results['redis_success'] else '✗'}")
    print(f"  Celery broker: {'✓' if test_results['celery_success'] else '✗'}")
    print(f"  Worker startup: {'✓' if test_results['worker_success'] else '✗'}")
    
    # Generate fixes
    generate_fixes(env_vars, test_results)
    
    # Final status
    print_section("Status")
    if all([test_results['network_success'], test_results['redis_success'], 
            test_results['celery_success'], test_results['worker_success']]):
        print_status("All tests passed! Worker should connect successfully.", "SUCCESS")
    else:
        print_status("Some tests failed. Apply the recommended fixes above.", "WARNING")
        
        # Show specific errors
        if test_results.get("redis_error"):
            print(f"\n  Redis Error: {test_results['redis_error']}")
        if test_results.get("celery_error"):
            print(f"  Celery Error: {test_results['celery_error']}")

if __name__ == "__main__":
    main()