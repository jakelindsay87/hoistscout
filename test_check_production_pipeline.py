#!/usr/bin/env python3
"""
Tests for check_production_pipeline.py
This is a utility script, not a module, so we just verify it exists and is executable.
"""

import os
import sys


def test_script_exists():
    """Test that the production check script exists"""
    script_path = os.path.join(os.path.dirname(__file__), "check_production_pipeline.py")
    assert os.path.exists(script_path), "check_production_pipeline.py should exist"
    assert os.access(script_path, os.X_OK), "check_production_pipeline.py should be executable"


def test_script_has_main():
    """Test that the script has a main function"""
    script_path = os.path.join(os.path.dirname(__file__), "check_production_pipeline.py")
    with open(script_path, 'r') as f:
        content = f.read()
    assert 'def main():' in content, "Script should have a main function"
    assert 'if __name__ == "__main__":' in content, "Script should have main guard"


if __name__ == "__main__":
    # Run basic tests
    test_script_exists()
    test_script_has_main()
    print("✅ All tests passed!")