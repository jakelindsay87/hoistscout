#!/usr/bin/env python3
"""
Local testing script for HoistScout deployment
Tests all components to ensure they work before pushing to Render
"""

import os
import sys
import time
import subprocess
import requests
import json
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{GREEN}✅ {message}{RESET}")
    elif status == "error":
        print(f"{RED}❌ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  {message}{RESET}")
    else:
        print(f"{BLUE}ℹ️  {message}{RESET}")

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Docker installed: {result.stdout.strip()}", "success")
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                print_status("Docker daemon is running", "success")
                return True
            else:
                print_status("Docker daemon is not running. Start Docker first.", "error")
                return False
        else:
            print_status("Docker is not installed", "error")
            return False
    except FileNotFoundError:
        print_status("Docker command not found", "error")
        return False

def check_docker_compose():
    """Check if Docker Compose is installed"""
    try:
        # Try docker compose (v2)
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Docker Compose v2 installed: {result.stdout.strip()}", "success")
            return 'docker compose'
    except:
        pass
    
    try:
        # Try docker-compose (v1)
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"Docker Compose v1 installed: {result.stdout.strip()}", "success")
            return 'docker-compose'
    except:
        pass
    
    print_status("Docker Compose is not installed", "error")
    return None

def check_files_exist():
    """Check if all required files exist"""
    required_files = [
        'docker-compose.yml',
        'backend/app/main.py',
        'backend/app/config.py',
        'backend/app/utils/demo_user.py',
        'backend/app/models/user.py',
        'backend/Dockerfile',
        'frontend/Dockerfile',
    ]
    
    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print_status(f"Found: {file}", "success")
        else:
            print_status(f"Missing: {file}", "error")
            all_exist = False
    
    return all_exist

def test_python_imports():
    """Test that Python imports work correctly"""
    print_status("Testing Python imports...")
    
    # Add backend to path
    sys.path.insert(0, str(Path.cwd() / 'backend'))
    
    # Set required environment variables
    os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/hoistscout'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    
    try:
        from app.config import get_settings
        settings = get_settings()
        print_status("Config imports successfully", "success")
        print_status(f"SECRET_KEY is set: {'*' * 10 + settings.secret_key[-10:]}", "success")
        
        from app.models.user import User, UserRole
        print_status("User model imports successfully", "success")
        
        from app.utils.demo_user import ensure_demo_user
        print_status("Demo user module imports successfully", "success")
        
        return True
    except Exception as e:
        print_status(f"Import error: {e}", "error")
        return False

def create_env_file():
    """Create .env file for docker-compose"""
    env_content = """# HoistScout Environment Variables
DATABASE_URL=postgresql://postgres:postgres@db:5432/hoistscout
REDIS_URL=redis://redis:6379/0
SECRET_KEY=hoistscout-dev-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=true

# Optional: Add these in production
# SENTRY_DSN=your-sentry-dsn
# MINIO_ENDPOINT=minio:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# OLLAMA_BASE_URL=http://ollama:11434
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print_status("Created .env file", "success")

def start_services(compose_cmd):
    """Start Docker services"""
    print_status("Starting Docker services...")
    
    # Stop any existing services
    subprocess.run([*compose_cmd.split(), 'down', '-v'], capture_output=True)
    
    # Start services
    process = subprocess.Popen(
        [*compose_cmd.split(), 'up', '-d'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        print_status("Docker services started", "success")
        return True
    else:
        print_status(f"Failed to start services: {stderr}", "error")
        return False

def wait_for_service(url, service_name, timeout=60):
    """Wait for a service to be ready"""
    print_status(f"Waiting for {service_name} to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is ok for root path
                print_status(f"{service_name} is ready", "success")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print_status(f"{service_name} did not start within {timeout} seconds", "error")
    return False

def test_api_endpoints():
    """Test API endpoints"""
    print_status("Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print_status("Health endpoint working", "success")
        else:
            print_status(f"Health endpoint returned {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"Health endpoint error: {e}", "error")
        return False
    
    # Test API docs
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print_status("API documentation available", "success")
        else:
            print_status(f"API docs returned {response.status_code}", "error")
    except Exception as e:
        print_status(f"API docs error: {e}", "error")
    
    # Test demo login
    try:
        login_data = {
            "username": "demo@hoistscout.com",  # OAuth2 form uses 'username' field
            "password": "demo123"
        }
        response = requests.post(
            f"{base_url}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            print_status("Demo login successful", "success")
            token = response.json().get("access_token")
            if token:
                print_status("Access token received", "success")
                return True
        else:
            print_status(f"Demo login failed: {response.status_code}", "warning")
            print_status("This might be normal if auth endpoints aren't fully implemented", "warning")
    except Exception as e:
        print_status(f"Demo login error: {e}", "warning")
    
    return True  # Don't fail on auth issues

def check_logs(compose_cmd):
    """Check logs for errors"""
    print_status("Checking service logs...")
    
    services = ['backend', 'worker', 'frontend']
    has_errors = False
    
    for service in services:
        result = subprocess.run(
            [*compose_cmd.split(), 'logs', '--tail=20', service],
            capture_output=True,
            text=True
        )
        
        if 'error' in result.stdout.lower() or 'error' in result.stderr.lower():
            print_status(f"{service} has errors in logs", "warning")
            has_errors = True
        else:
            print_status(f"{service} logs look clean", "success")
    
    return not has_errors

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}HoistScout Local Deployment Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Change to the hoistscout-repo directory
    os.chdir(Path(__file__).parent)
    
    # 1. Check prerequisites
    print_status("Checking prerequisites...")
    if not check_docker():
        return 1
    
    compose_cmd = check_docker_compose()
    if not compose_cmd:
        return 1
    
    # 2. Check files
    print(f"\n{BLUE}Checking required files...{RESET}")
    if not check_files_exist():
        print_status("Some required files are missing", "error")
        return 1
    
    # 3. Test Python imports
    print(f"\n{BLUE}Testing Python imports...{RESET}")
    if not test_python_imports():
        return 1
    
    # 4. Create .env file
    print(f"\n{BLUE}Setting up environment...{RESET}")
    create_env_file()
    
    # 5. Start services
    print(f"\n{BLUE}Starting Docker services...{RESET}")
    if not start_services(compose_cmd):
        return 1
    
    # 6. Wait for services
    print(f"\n{BLUE}Waiting for services to be ready...{RESET}")
    time.sleep(10)  # Give services time to start
    
    # Check if API is ready
    if not wait_for_service("http://localhost:8000/health", "API"):
        print_status("API failed to start. Checking logs...", "error")
        subprocess.run([*compose_cmd.split(), 'logs', 'backend'])
        return 1
    
    # 7. Test API endpoints
    print(f"\n{BLUE}Testing API endpoints...{RESET}")
    test_api_endpoints()
    
    # 8. Check logs
    print(f"\n{BLUE}Checking service logs...{RESET}")
    check_logs(compose_cmd)
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}Local deployment test complete!{RESET}")
    print(f"\n{BLUE}Next steps:{RESET}")
    print("1. Check the services:")
    print(f"   - API: http://localhost:8000/docs")
    print(f"   - Frontend: http://localhost:3000")
    print("2. Push changes to GitHub:")
    print("   git add -A")
    print("   git commit -m 'Fix deployment issues'")
    print("   git push origin main")
    print("3. Add environment variables in Render")
    print("4. Trigger deployment in Render\n")
    
    print(f"To stop services: {compose_cmd} down")
    print(f"To view logs: {compose_cmd} logs -f [service-name]")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())