#!/usr/bin/env python3
"""
Deployment Verification Script for HoistScout Backend
Checks for common deployment issues before pushing changes
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

def check_config_file() -> Tuple[bool, List[str]]:
    """Check if config.py has proper optional settings"""
    issues = []
    config_path = Path(__file__).parent / "app" / "config.py"
    
    if not config_path.exists():
        issues.append("config.py not found")
        return False, issues
    
    content = config_path.read_text()
    
    # Check if MinIO settings are optional
    if "minio_endpoint: str" in content and "Optional" not in content:
        issues.append("MinIO settings should be Optional[str] for deployment")
    
    # Check for hardcoded localhost URLs
    localhost_pattern = r'=\s*["\']http://localhost'
    if re.search(localhost_pattern, content):
        issues.append("Found hardcoded localhost URLs in config.py")
    
    return len(issues) == 0, issues


def check_import_errors() -> Tuple[bool, List[str]]:
    """Check for potential import errors"""
    issues = []
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    if not pyproject_path.exists():
        issues.append("pyproject.toml not found")
        return False, issues
    
    pyproject_content = pyproject_path.read_text()
    
    # Required packages that should be in pyproject.toml
    required_packages = [
        "minio",
        "unstructured",
        "loguru",
        "fake-useragent",
        "asyncio-throttle"
    ]
    
    for package in required_packages:
        if package not in pyproject_content:
            issues.append(f"Missing required package: {package}")
    
    return len(issues) == 0, issues


def check_dockerfile() -> Tuple[bool, List[str]]:
    """Check if Dockerfile has necessary system dependencies"""
    issues = []
    dockerfile_path = Path(__file__).parent / "Dockerfile"
    
    if not dockerfile_path.exists():
        issues.append("Dockerfile not found")
        return False, issues
    
    content = dockerfile_path.read_text()
    
    # Check for required system packages
    required_packages = ["poppler-utils", "tesseract-ocr"]
    for package in required_packages:
        if package not in content:
            issues.append(f"Missing system dependency in Dockerfile: {package}")
    
    # Check for correct COPY paths
    if "COPY backend/" not in content:
        issues.append("Dockerfile should use 'COPY backend/' prefix for correct build context")
    
    return len(issues) == 0, issues


def check_external_service_handling() -> Tuple[bool, List[str]]:
    """Check if external services are properly handled as optional"""
    issues = []
    
    # Check PDF processor
    pdf_processor_path = Path(__file__).parent / "app" / "core" / "pdf_processor.py"
    if pdf_processor_path.exists():
        content = pdf_processor_path.read_text()
        if "if self.minio_client:" not in content:
            issues.append("PDF processor should handle None minio_client")
    
    # Check health endpoint
    health_path = Path(__file__).parent / "app" / "api" / "health.py"
    if health_path.exists():
        content = health_path.read_text()
        if "if settings.minio_endpoint:" not in content:
            issues.append("Health check should handle optional MinIO")
    
    return len(issues) == 0, issues


def check_render_yaml() -> Tuple[bool, List[str]]:
    """Check render.yaml configuration"""
    issues = []
    render_path = Path(__file__).parent.parent / "render.yaml"
    
    if not render_path.exists():
        issues.append("render.yaml not found in repository root")
        return False, issues
    
    content = render_path.read_text()
    
    # Check for correct dockerfile paths
    if "./backend/Dockerfile" in content:
        issues.append("render.yaml should use 'backend/Dockerfile' without leading ./")
    
    # Check for missing critical env vars
    if "SECRET_KEY" not in content:
        issues.append("Missing SECRET_KEY in render.yaml")
    
    if "DATABASE_URL" not in content:
        issues.append("Missing DATABASE_URL in render.yaml")
    
    return len(issues) == 0, issues


def main():
    """Run all deployment checks"""
    print("🔍 HoistScout Backend Deployment Verification")
    print("=" * 50)
    
    all_passed = True
    
    # Run all checks
    checks = [
        ("Config File", check_config_file),
        ("Python Dependencies", check_import_errors),
        ("Dockerfile", check_dockerfile),
        ("External Services", check_external_service_handling),
        ("Render.yaml", check_render_yaml)
    ]
    
    for check_name, check_func in checks:
        passed, issues = check_func()
        
        if passed:
            print(f"✅ {check_name}: PASSED")
        else:
            print(f"❌ {check_name}: FAILED")
            for issue in issues:
                print(f"   - {issue}")
            all_passed = False
        print()
    
    # Summary
    print("=" * 50)
    if all_passed:
        print("✅ All deployment checks passed!")
        print("The backend should deploy successfully.")
        return 0
    else:
        print("❌ Deployment checks failed!")
        print("Fix the issues above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())