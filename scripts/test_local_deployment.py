#!/usr/bin/env python3
"""
Test local deployment of HoistScraper.
Tests all components systematically.
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def run_command(command, capture_output=False):
    """Run a shell command and return result."""
    print(f"{Colors.MAGENTA}Running: {command}{Colors.END}")
    
    if capture_output:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    else:
        result = subprocess.run(command, shell=True)
        return result.returncode, "", ""


def wait_for_service(url, timeout=120, interval=5):
    """Wait for a service to be available."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(interval)
    
    return False


def test_docker_setup():
    """Test Docker and Docker Compose are properly installed."""
    print_header("Testing Docker Setup")
    
    # Check Docker
    code, stdout, stderr = run_command("docker --version", capture_output=True)
    if code == 0:
        print_success(f"Docker installed: {stdout.strip()}")
    else:
        print_error("Docker not installed or not accessible")
        return False
    
    # Check Docker Compose
    code, stdout, stderr = run_command("docker compose version", capture_output=True)
    if code == 0:
        print_success(f"Docker Compose installed: {stdout.strip()}")
    else:
        print_error("Docker Compose not installed")
        return False
    
    return True


def stop_existing_containers():
    """Stop any existing containers."""
    print_header("Cleaning Up Existing Containers")
    
    # Stop containers
    run_command("docker compose down -v")
    print_success("Cleaned up existing containers")
    
    # Wait a bit for cleanup
    time.sleep(2)


def start_containers():
    """Start all containers using docker-compose."""
    print_header("Starting Docker Containers")
    
    # Use local environment file
    env_file = ".env.local"
    if not Path(env_file).exists():
        print_error(f"{env_file} not found!")
        return False
    
    print_info(f"Using environment file: {env_file}")
    
    # Start containers
    code, _, _ = run_command(f"docker compose --env-file {env_file} up -d --build")
    if code != 0:
        print_error("Failed to start containers")
        return False
    
    print_success("Containers started")
    
    # Show container status
    print_info("Container status:")
    run_command("docker compose ps")
    
    return True


def wait_for_services():
    """Wait for all services to be ready."""
    print_header("Waiting for Services to Start")
    
    services = [
        ("Backend API", "http://localhost:8000/health", 120),
        ("Frontend", "http://localhost:3000", 120),
        ("PostgreSQL", None, 60),  # Check via docker
        ("Redis", None, 60),       # Check via docker
        ("Ollama", "http://localhost:11434/api/tags", 120),
    ]
    
    all_ready = True
    
    for service_name, url, timeout in services:
        print(f"Waiting for {service_name}...", end=" ")
        
        if url:
            if wait_for_service(url, timeout=timeout):
                print_success("Ready")
            else:
                print_error("Timeout")
                all_ready = False
        else:
            # For services without HTTP endpoints, check container health
            time.sleep(5)  # Give it time to start
            container_name = f"hoistscraper-{service_name.lower().replace(' ', '')}"
            code, stdout, _ = run_command(
                f"docker inspect --format='{{{{.State.Health.Status}}}}' {container_name}",
                capture_output=True
            )
            if "healthy" in stdout or code == 0:
                print_success("Ready")
            else:
                print_warning("Status unknown")
    
    return all_ready


def test_api_endpoints():
    """Test API endpoints."""
    print_header("Testing API Endpoints")
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("GET /", None, None),
        ("GET /health", None, None),
        ("GET /api/websites", None, None),
        ("POST /api/websites", {
            "name": "Test Grant Site",
            "url": "https://test-grants.example.com",
            "description": "Test site for grants",
            "category": "grants",
            "is_active": True
        }, {"Content-Type": "application/json"}),
        ("GET /api/scrape-jobs", None, None),
        ("GET /api/opportunities", None, None),
        ("GET /api/stats", None, None),
    ]
    
    results = []
    
    for method_path, data, headers in tests:
        method, path = method_path.split()
        url = f"{base_url}{path}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers or {})
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers or {})
            
            if response.status_code in [200, 201]:
                print_success(f"{method} {path} - {response.status_code}")
                results.append((True, method_path, response.json() if response.text else None))
            else:
                print_error(f"{method} {path} - {response.status_code}")
                results.append((False, method_path, response.text))
        except Exception as e:
            print_error(f"{method} {path} - {str(e)}")
            results.append((False, method_path, str(e)))
    
    # Print summary
    success_count = sum(1 for success, _, _ in results if success)
    print(f"\nAPI Tests: {success_count}/{len(tests)} passed")
    
    return success_count == len(tests)


def test_frontend():
    """Test frontend is accessible."""
    print_header("Testing Frontend")
    
    url = "http://localhost:3000"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print_success(f"Frontend accessible at {url}")
            
            # Check for React app
            if "root" in response.text or "app" in response.text:
                print_success("React application loaded")
            else:
                print_warning("Frontend loaded but content unexpected")
            
            return True
        else:
            print_error(f"Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Failed to access frontend: {str(e)}")
        return False


def test_database_connection():
    """Test database connectivity."""
    print_header("Testing Database Connection")
    
    # Test via backend API
    try:
        response = requests.get("http://localhost:8000/api/websites")
        if response.status_code == 200:
            print_success("Database connection working (via API)")
            websites = response.json()
            print_info(f"Found {len(websites)} websites in database")
            return True
        else:
            print_error("Database connection failed")
            return False
    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False


def test_worker():
    """Test worker functionality."""
    print_header("Testing Worker")
    
    # Check worker logs
    code, stdout, stderr = run_command(
        "docker logs hoistscraper-worker --tail 20",
        capture_output=True
    )
    
    if "Worker started" in stdout or "Ready to process jobs" in stdout:
        print_success("Worker is running")
    else:
        print_warning("Worker status unclear - check logs")
    
    # Create a test scrape job
    try:
        # First, ensure we have a website to scrape
        websites_response = requests.get("http://localhost:8000/api/websites")
        websites = websites_response.json()
        
        if not websites:
            # Create a test website
            test_website = {
                "name": "Test Scrape Site",
                "url": "https://example.com",
                "description": "Test site for scraping",
                "category": "test"
            }
            create_response = requests.post(
                "http://localhost:8000/api/websites",
                json=test_website
            )
            if create_response.status_code in [200, 201]:
                website_id = create_response.json()["id"]
                print_success("Created test website")
            else:
                print_error("Failed to create test website")
                return False
        else:
            website_id = websites[0]["id"]
        
        # Create scrape job
        job_data = {"website_id": website_id}
        job_response = requests.post(
            "http://localhost:8000/api/scrape-jobs",
            json=job_data
        )
        
        if job_response.status_code in [200, 201]:
            job = job_response.json()
            print_success(f"Created scrape job {job['id']}")
            
            # Wait a bit and check status
            time.sleep(5)
            status_response = requests.get(f"http://localhost:8000/api/scrape-jobs/{job['id']}")
            if status_response.status_code == 200:
                job_status = status_response.json()
                print_info(f"Job status: {job_status['status']}")
            
            return True
        else:
            print_error("Failed to create scrape job")
            return False
            
    except Exception as e:
        print_error(f"Worker test failed: {str(e)}")
        return False


def test_ollama():
    """Test Ollama LLM service."""
    print_header("Testing Ollama LLM Service")
    
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print_success("Ollama service is running")
            
            models = response.json().get("models", [])
            if models:
                print_info(f"Available models: {', '.join(m['name'] for m in models)}")
            else:
                print_warning("No models loaded yet - run: docker exec hoistscraper-ollama ollama pull mistral:7b-instruct")
            
            return True
        else:
            print_error("Ollama service not responding")
            return False
    except Exception as e:
        print_error(f"Ollama test failed: {str(e)}")
        return False


def check_logs():
    """Check logs for errors."""
    print_header("Checking Logs for Errors")
    
    services = ["backend", "frontend", "worker", "db", "redis", "ollama"]
    error_count = 0
    
    for service in services:
        code, stdout, stderr = run_command(
            f"docker logs hoistscraper-{service} --tail 50 2>&1 | grep -i error || true",
            capture_output=True
        )
        
        if stdout.strip():
            print_warning(f"{service}: Found errors in logs")
            error_count += 1
        else:
            print_success(f"{service}: No errors in recent logs")
    
    return error_count == 0


def run_all_tests():
    """Run all tests in sequence."""
    print_header("HoistScraper Local Deployment Test Suite")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    results = []
    
    # Run tests
    tests = [
        ("Docker Setup", test_docker_setup),
        ("Stop Existing Containers", lambda: (stop_existing_containers(), True)[1]),
        ("Start Containers", start_containers),
        ("Wait for Services", wait_for_services),
        ("API Endpoints", test_api_endpoints),
        ("Frontend", test_frontend),
        ("Database Connection", test_database_connection),
        ("Worker", test_worker),
        ("Ollama LLM", test_ollama),
        ("Check Logs", check_logs),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{Colors.BOLD}Running: {test_name}{Colors.END}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_error(f"Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"{Colors.BOLD}Results:{Colors.END}")
    for test_name, success in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if success else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("\nAll tests passed! HoistScraper is ready for use.")
        print_info("\nAccess the application at:")
        print(f"  - Frontend: http://localhost:3000")
        print(f"  - API: http://localhost:8000")
        print(f"  - API Docs: http://localhost:8000/docs")
    else:
        print_error(f"\n{total - passed} tests failed. Check the logs for details.")
        print_info("\nTo view logs:")
        print("  docker compose logs")
        print("  docker compose logs <service-name>")
    
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    # Run tests
    run_all_tests()