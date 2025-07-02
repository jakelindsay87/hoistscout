#!/usr/bin/env python3
"""Check API startup locally to identify the error."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from hoistscraper.main import app
    print("✅ Main app imported successfully")
    
    # Try to import all routers
    from hoistscraper.routers import credentials, admin, debug
    print("✅ All routers imported successfully")
    
    # Try to import models
    from hoistscraper.models import Website
    from hoistscraper.models_credentials import WebsiteCredential, WebsiteCredentialCreate, WebsiteCredentialRead
    print("✅ All models imported successfully")
    
    # Try to import auth
    from hoistscraper.auth.credential_manager import credential_manager
    print("✅ Credential manager imported successfully")
    
    print("\n🎉 All imports successful! The API should start correctly.")
    
except Exception as e:
    print(f"\n❌ Import error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()