#!/usr/bin/env python3
"""Test basic imports to ensure modules are properly set up"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

try:
    print("Testing imports...")
    
    # Test config import
    from app.config import get_settings
    print("✓ Config module imported successfully")
    
    # Test logging import
    from app.core.logging import ProductionLogger
    print("✓ Logging module imported successfully")
    
    # Test compliance checker import
    from app.core.compliance_checker import TermsComplianceChecker
    print("✓ Compliance checker imported successfully")
    
    # Test auth manager import
    from app.core.auth_manager import UniversalAuthenticator
    print("✓ Auth manager imported successfully")
    
    print("\n✅ All imports successful!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print(f"Module path issue: {e.name}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    sys.exit(1)