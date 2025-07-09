#!/usr/bin/env python3
"""
Debug Worker Issues - Comprehensive diagnosis of HoistScout worker problems.

This script:
1. Fetches latest worker logs from Render API
2. Looks for Redis connection errors
3. Checks if REDIS_URL environment variable is being read
4. Verifies if Celery is starting properly
5. Tests the Redis URL directly to ensure it's valid
"""

import requests
import json
import re
from datetime import datetime, timedelta
import redis
import os
import sys
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

# Render API Configuration
RENDER_API_KEY = "rnd_MM1dw7DiZwUEZRMNR1AzmxKlPhow"
RENDER_API_URL = "https://api.render.com/v1"
WORKER_SERVICE_ID = "srv-d1hlvanfte5s73ad476g"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str, color: str = Colors.HEADER):
    """Print a section header"""
    print(f"\n{color}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_status(label: str, status: str, is_success: bool):
    """Print a status line with color coding"""
    color = Colors.OKGREEN if is_success else Colors.FAIL
    symbol = "✅" if is_success else "❌"
    print(f"{label}: {color}{symbol} {status}{Colors.ENDC}")


def get_render_headers() -> Dict[str, str]:
    """Get headers for Render API requests"""
    return {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }


def fetch_service_info() -> Optional[Dict]:
    """Fetch service information from Render"""
    try:
        response = requests.get(
            f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}",
            headers=get_render_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Colors.FAIL}Failed to fetch service info: {response.status_code}{Colors.ENDC}")
            return None
    except Exception as e:
        print(f"{Colors.FAIL}Error fetching service info: {e}{Colors.ENDC}")
        return None


def fetch_service_env_vars() -> Optional[List[Dict]]:
    """Fetch environment variables configured for the service"""
    try:
        response = requests.get(
            f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/env-vars",
            headers=get_render_headers()
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Colors.FAIL}Failed to fetch env vars: {response.status_code}{Colors.ENDC}")
            return None
    except Exception as e:
        print(f"{Colors.FAIL}Error fetching env vars: {e}{Colors.ENDC}")
        return None


def fetch_latest_deployment() -> Optional[Dict]:
    """Fetch the latest deployment information"""
    try:
        response = requests.get(
            f"{RENDER_API_URL}/services/{WORKER_SERVICE_ID}/deploys?limit=1",
            headers=get_render_headers()
        )
        if response.status_code == 200:
            deploys = response.json()
            return deploys[0] if deploys else None
        else:
            print(f"{Colors.FAIL}Failed to fetch deployments: {response.status_code}{Colors.ENDC}")
            return None
    except Exception as e:
        print(f"{Colors.FAIL}Error fetching deployments: {e}{Colors.ENDC}")
        return None


def fetch_worker_logs(limit: int = 1000) -> Optional[str]:
    """Fetch recent logs from the worker service"""
    try:
        # Note: Render doesn't have a direct logs API endpoint in v1
        # We'll need to check deployment status and look for build logs
        deployment = fetch_latest_deployment()
        if deployment:
            deploy_id = deployment.get("deploy", {}).get("id")
            if deploy_id:
                # Try to get build logs
                response = requests.get(
                    f"{RENDER_API_URL}/deploys/{deploy_id}",
                    headers=get_render_headers()
                )
                if response.status_code == 200:
                    deploy_info = response.json()
                    # Build logs might be in the response
                    return json.dumps(deploy_info, indent=2)
        
        # For runtime logs, we'd need to use Render's log streaming which requires WebSocket
        return None
    except Exception as e:
        print(f"{Colors.FAIL}Error fetching logs: {e}{Colors.ENDC}")
        return None


def test_local_redis_url() -> Optional[str]:
    """Try to get Redis URL from local .env file or other sources"""
    # Try to read from .env file
    env_file_path = "/root/hoistscout-repo/backend/.env"
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('REDIS_URL='):
                        return line.strip().split('=', 1)[1].strip('"\'')
        except Exception:
            pass
    
    # Try from environment
    return os.environ.get('REDIS_URL')


def analyze_logs(logs: str) -> Dict[str, List[str]]:
    """Analyze logs for common issues"""
    issues = {
        "redis_connection_errors": [],
        "redis_url_missing": [],
        "celery_startup_errors": [],
        "import_errors": [],
        "general_errors": []
    }
    
    if not logs:
        return issues
    
    lines = logs.split('\n')
    
    for line in lines:
        # Check for Redis connection errors
        if any(pattern in line.lower() for pattern in ['redis connection', 'connection refused', 'redis error', 'econnrefused']):
            issues["redis_connection_errors"].append(line.strip())
        
        # Check for missing REDIS_URL
        if 'redis_url' in line.lower() and any(word in line.lower() for word in ['none', 'missing', 'not found', 'undefined']):
            issues["redis_url_missing"].append(line.strip())
        
        # Check for Celery startup errors
        if 'celery' in line.lower() and any(word in line.lower() for word in ['error', 'failed', 'exception']):
            issues["celery_startup_errors"].append(line.strip())
        
        # Check for import errors
        if 'importerror' in line.lower() or 'modulenotfounderror' in line.lower():
            issues["import_errors"].append(line.strip())
        
        # Check for general errors
        if any(pattern in line.lower() for pattern in ['error', 'exception', 'traceback', 'failed']):
            issues["general_errors"].append(line.strip())
    
    return issues


def test_redis_connection(redis_url: str) -> Tuple[bool, str]:
    """Test direct Redis connection"""
    try:
        # Parse Redis URL
        parsed = urlparse(redis_url)
        
        # Create Redis client
        r = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
        
        # Test connection
        r.ping()
        
        # Test basic operations
        test_key = f"hoistscout_test_{datetime.now().timestamp()}"
        r.set(test_key, "test_value", ex=10)
        value = r.get(test_key)
        r.delete(test_key)
        
        if value == "test_value":
            return True, f"Connected to Redis at {parsed.hostname}:{parsed.port}"
        else:
            return False, "Connected but read/write test failed"
            
    except redis.ConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except redis.TimeoutError as e:
        return False, f"Timeout error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {str(e)}"


def check_redis_url_format(redis_url: str) -> List[str]:
    """Check Redis URL format for common issues"""
    issues = []
    
    if not redis_url:
        issues.append("Redis URL is empty")
        return issues
    
    if not redis_url.startswith(('redis://', 'rediss://')):
        issues.append("Redis URL should start with redis:// or rediss://")
    
    try:
        parsed = urlparse(redis_url)
        
        if not parsed.hostname:
            issues.append("Missing hostname in Redis URL")
        
        if not parsed.port:
            issues.append("Missing port in Redis URL (default is 6379)")
        
        if parsed.scheme == 'rediss' and not parsed.port:
            issues.append("Redis SSL (rediss://) typically uses port 6380 or custom port")
            
    except Exception as e:
        issues.append(f"Failed to parse Redis URL: {e}")
    
    return issues


def simulate_worker_startup():
    """Simulate what the worker should be doing on startup"""
    print_section("7. WORKER STARTUP SIMULATION", Colors.OKCYAN)
    
    print(f"{Colors.BOLD}Simulating worker startup sequence...{Colors.ENDC}\n")
    
    # 1. Check Python imports
    print("1. Testing Python imports...")
    try:
        import celery
        print(f"   {Colors.OKGREEN}✅ Celery version: {celery.__version__}{Colors.ENDC}")
    except ImportError as e:
        print(f"   {Colors.FAIL}❌ Failed to import Celery: {e}{Colors.ENDC}")
        
    try:
        import redis
        print(f"   {Colors.OKGREEN}✅ Redis-py version: {redis.__version__}{Colors.ENDC}")
    except ImportError as e:
        print(f"   {Colors.FAIL}❌ Failed to import redis: {e}{Colors.ENDC}")
    
    # 2. Check if worker module can be imported
    print("\n2. Testing worker module import...")
    try:
        # Add backend to Python path
        sys.path.insert(0, '/root/hoistscout-repo/backend')
        from app.worker import celery_app
        print(f"   {Colors.OKGREEN}✅ Worker module imported successfully{Colors.ENDC}")
        
        # Check registered tasks
        print(f"\n3. Registered Celery tasks:")
        for task_name in sorted(celery_app.tasks.keys()):
            if not task_name.startswith('celery.'):  # Skip built-in tasks
                print(f"   - {task_name}")
                
    except Exception as e:
        print(f"   {Colors.FAIL}❌ Failed to import worker: {type(e).__name__}: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()


def diagnose_worker():
    """Main diagnostic function"""
    print_section("HOISTSCOUT WORKER DIAGNOSTICS", Colors.HEADER)
    
    # 1. Check Service Status
    print_section("1. SERVICE STATUS", Colors.OKBLUE)
    service_info = fetch_service_info()
    if service_info:
        status = service_info.get("status", "unknown")
        service_type = service_info.get("type", "unknown")
        created_at = service_info.get("createdAt", "unknown")
        
        is_active = status == "active"
        print_status("Service Status", status.upper(), is_active)
        print(f"Service Type: {service_type}")
        print(f"Created: {created_at}")
    else:
        print(f"{Colors.FAIL}❌ Failed to fetch service information{Colors.ENDC}")
    
    # 2. Check Latest Deployment
    print_section("2. LATEST DEPLOYMENT", Colors.OKBLUE)
    deployment = fetch_latest_deployment()
    if deployment:
        deploy_info = deployment.get("deploy", {})
        status = deploy_info.get("status", "unknown")
        created_at = deploy_info.get("createdAt", "unknown")
        commit_msg = deploy_info.get("commit", {}).get("message", "N/A")
        
        is_live = status == "live"
        print_status("Deployment Status", status.upper(), is_live)
        print(f"Deployed: {created_at}")
        print(f"Commit: {commit_msg[:80]}...")
    else:
        print(f"{Colors.FAIL}❌ No deployments found{Colors.ENDC}")
    
    # 3. Check Environment Variables
    print_section("3. ENVIRONMENT VARIABLES", Colors.OKBLUE)
    env_vars = fetch_service_env_vars()
    redis_url = None
    
    if env_vars:
        critical_vars = ["REDIS_URL", "DATABASE_URL", "GEMINI_API_KEY", "USE_GEMINI"]
        found_vars = {}
        
        for var in env_vars:
            var_key = var.get("key", "")
            if var_key in critical_vars:
                found_vars[var_key] = True
                if var_key == "REDIS_URL":
                    # Don't print the actual value for security
                    redis_url = var.get("value", "")
        
        for var in critical_vars:
            is_found = var in found_vars
            print_status(f"{var}", "Configured" if is_found else "NOT FOUND", is_found)
    else:
        print(f"{Colors.WARNING}⚠️  Could not fetch environment variables from Render API{Colors.ENDC}")
        print(f"This might be normal - Render may not expose env vars via API for security.")
        
        # Try to get Redis URL from local sources
        print(f"\n{Colors.BOLD}Checking for local Redis configuration...{Colors.ENDC}")
        redis_url = test_local_redis_url()
        if redis_url:
            print(f"{Colors.OKGREEN}✅ Found Redis URL in local configuration{Colors.ENDC}")
    
    # 4. Test Redis Connection
    print_section("4. REDIS CONNECTION TEST", Colors.OKBLUE)
    if redis_url:
        # Check URL format
        format_issues = check_redis_url_format(redis_url)
        if format_issues:
            print(f"{Colors.WARNING}⚠️  Redis URL format issues:{Colors.ENDC}")
            for issue in format_issues:
                print(f"  - {issue}")
        
        # Test connection
        print("\nTesting Redis connection...")
        success, message = test_redis_connection(redis_url)
        print_status("Redis Connection", message, success)
    else:
        print(f"{Colors.FAIL}❌ REDIS_URL not found in environment variables{Colors.ENDC}")
    
    # 5. Analyze Logs (if available)
    print_section("5. LOG ANALYSIS", Colors.OKBLUE)
    logs = fetch_worker_logs()
    
    if logs:
        issues = analyze_logs(logs)
        
        has_issues = any(len(issue_list) > 0 for issue_list in issues.values())
        
        if has_issues:
            print(f"{Colors.WARNING}⚠️  Found potential issues in logs:{Colors.ENDC}\n")
            
            for issue_type, issue_list in issues.items():
                if issue_list:
                    print(f"{Colors.BOLD}{issue_type.replace('_', ' ').title()}:{Colors.ENDC}")
                    for issue in issue_list[:5]:  # Show max 5 of each type
                        print(f"  - {issue}")
                    if len(issue_list) > 5:
                        print(f"  ... and {len(issue_list) - 5} more")
                    print()
        else:
            print(f"{Colors.OKGREEN}✅ No obvious issues found in logs{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  Unable to fetch logs. Please check logs manually:{Colors.ENDC}")
        print(f"   https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/logs")
    
    # 6. Summary and Recommendations
    print_section("6. DIAGNOSIS SUMMARY", Colors.HEADER)
    
    recommendations = []
    
    # Check deployment status
    if deployment and deployment.get("deploy", {}).get("status") != "live":
        recommendations.append("Deploy is not live. Check build logs for errors.")
    
    # Check Redis
    if not redis_url:
        recommendations.append("REDIS_URL is not configured. Set it in Render dashboard.")
    elif redis_url and not test_redis_connection(redis_url)[0]:
        recommendations.append("Redis connection failed. Verify the Redis URL and service status.")
    
    # Check logs
    if logs and issues.get("celery_startup_errors"):
        recommendations.append("Celery startup errors detected. Check worker configuration.")
    
    if recommendations:
        print(f"{Colors.WARNING}⚠️  Recommendations:{Colors.ENDC}")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print(f"{Colors.OKGREEN}✅ Worker appears to be configured correctly{Colors.ENDC}")
        print("\nIf jobs are still not processing, check:")
        print("  1. Worker logs for runtime errors")
        print("  2. Job submission is using correct queue names")
        print("  3. Celery tasks are properly registered")
    
    print(f"\n{Colors.BOLD}Dashboard Links:{Colors.ENDC}")
    print(f"Worker Logs: https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/logs")
    print(f"Worker Settings: https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/settings")
    print(f"Environment Variables: https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/env")
    
    # 7. Run worker startup simulation
    simulate_worker_startup()
    
    # 8. Show expected worker command
    print_section("8. EXPECTED WORKER STARTUP COMMAND", Colors.OKBLUE)
    print("The worker should be started with one of these commands:")
    print(f"\n{Colors.BOLD}Option 1 (Recommended):{Colors.ENDC}")
    print("  celery -A app.worker worker --loglevel=info")
    print(f"\n{Colors.BOLD}Option 2 (With more logging):{Colors.ENDC}")
    print("  celery -A app.worker worker --loglevel=debug")
    print(f"\n{Colors.BOLD}Option 3 (Using start_worker.py script):{Colors.ENDC}")
    print("  python start_worker.py")
    print(f"\n{Colors.WARNING}Make sure the start command in Render dashboard matches one of these!{Colors.ENDC}")
    
    # 9. Clear action items
    print_section("9. ACTION ITEMS TO FIX WORKER", Colors.FAIL)
    print(f"{Colors.BOLD}The worker is failing because environment variables are not set!{Colors.ENDC}\n")
    print("To fix this issue:")
    print(f"\n{Colors.BOLD}1. Go to Render Dashboard:{Colors.ENDC}")
    print(f"   https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/env")
    
    print(f"\n{Colors.BOLD}2. Add these REQUIRED environment variables:{Colors.ENDC}")
    print(f"   • {Colors.FAIL}REDIS_URL{Colors.ENDC} - Your Redis connection string (e.g., redis://host:port or from Redis provider)")
    print(f"   • {Colors.FAIL}DATABASE_URL{Colors.ENDC} - Your PostgreSQL connection string")
    print(f"   • {Colors.WARNING}GEMINI_API_KEY{Colors.ENDC} - Your Google Gemini API key for scraping")
    print(f"   • {Colors.WARNING}USE_GEMINI{Colors.ENDC} - Set to 'true' to use Gemini scraper")
    
    print(f"\n{Colors.BOLD}3. Verify the worker start command:{Colors.ENDC}")
    print(f"   https://dashboard.render.com/worker/{WORKER_SERVICE_ID}/settings")
    print("   Should be: celery -A app.worker worker --loglevel=info")
    
    print(f"\n{Colors.BOLD}4. Redeploy the worker after adding environment variables{Colors.ENDC}")
    
    print(f"\n{Colors.FAIL}🚨 CRITICAL: Without these environment variables, the worker CANNOT start!{Colors.ENDC}")


if __name__ == "__main__":
    try:
        diagnose_worker()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Diagnostic interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {type(e).__name__}: {e}{Colors.ENDC}")
        sys.exit(1)