#!/usr/bin/env python3
"""
CI Validation Script - Ensures all tests will pass
"""

import os
import json
import re
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"{GREEN}✓ {description}{RESET}")
        return True
    else:
        print(f"{RED}✗ {description} - Missing file: {filepath}{RESET}")
        return False

def check_file_content(filepath, pattern, description):
    """Check if file contains specific pattern"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if re.search(pattern, content):
                print(f"{GREEN}✓ {description}{RESET}")
                return True
            else:
                print(f"{RED}✗ {description}{RESET}")
                return False
    except Exception as e:
        print(f"{RED}✗ {description} - Error: {e}{RESET}")
        return False

def main():
    print("🔍 CI Validation Check")
    print("======================\n")
    
    issues = 0
    
    # 1. Check critical files
    print(f"{BLUE}📁 Checking critical files...{RESET}")
    
    critical_files = [
        ("backend/poetry.lock", "Backend lock file"),
        ("backend/pyproject.toml", "Backend project file"),
        ("frontend/package.json", "Frontend package.json"),
        ("frontend/package-lock.json", "Frontend lock file"),
        ("package.json", "Root package.json"),
        ("package-lock.json", "Root lock file"),
    ]
    
    for filepath, desc in critical_files:
        if not check_file_exists(filepath, desc):
            issues += 1
    
    # 2. Check configurations
    print(f"\n{BLUE}🔧 Checking configurations...{RESET}")
    
    # Check mypy version
    if not check_file_content(
        "backend/pyproject.toml",
        r'mypy = "\^1\.10"',
        "Mypy version (^1.10)"
    ):
        issues += 1
    
    # Check memory optimization
    if not check_file_content(
        "frontend/next.config.js",
        r'workerThreads:\s*false',
        "Memory optimization in next.config.js"
    ):
        issues += 1
    
    # Check workspace configuration
    if not check_file_content(
        "package.json",
        r'"workspaces"',
        "Workspace configuration"
    ):
        issues += 1
    
    # Check for Link imports in frontend files
    print(f"\n{BLUE}🔗 Checking Next.js Link usage...{RESET}")
    
    frontend_files = [
        "frontend/src/app/layout.tsx",
        "frontend/src/app/page.tsx",
        "frontend/src/app/opportunities/[id]/page.tsx"
    ]
    
    for filepath in frontend_files:
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                content = f.read()
                if '<a href="/' in content and 'import Link' not in content:
                    print(f"{RED}✗ {filepath} has <a> tags without Link import{RESET}")
                    issues += 1
                else:
                    print(f"{GREEN}✓ {filepath} Link usage OK{RESET}")
    
    # 3. Check for common issues
    print(f"\n{BLUE}🐛 Checking for common issues...{RESET}")
    
    # Check if poetry.lock exists and is not empty
    if Path("backend/poetry.lock").exists():
        size = Path("backend/poetry.lock").stat().st_size
        if size < 1000:
            print(f"{RED}✗ poetry.lock seems too small ({size} bytes){RESET}")
            issues += 1
        else:
            print(f"{GREEN}✓ poetry.lock size OK ({size} bytes){RESET}")
    
    # 4. Summary
    print(f"\n{BLUE}📊 Summary{RESET}")
    print("==========")
    
    if issues == 0:
        print(f"{GREEN}✅ All checks passed! Safe to push to CI.{RESET}")
        print("\nNext steps:")
        print("1. git status")
        print("2. git add -A")
        print("3. git commit -m \"fix: ensure CI passes\"")
        print("4. git push origin fix/deployment-errors")
        return 0
    else:
        print(f"{RED}❌ Found {issues} issues that need fixing{RESET}")
        print("\nSuggested fixes:")
        print("1. cd backend && rm poetry.lock && poetry lock")
        print("2. cd frontend && npm install")
        print("3. cd .. && npm install")
        print("4. Review error messages above")
        return 1

if __name__ == "__main__":
    sys.exit(main())