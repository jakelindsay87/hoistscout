"""Pytest configuration for backend tests."""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set test data directory to avoid permission issues
os.environ["DATA_DIR"] = str(backend_dir / "test_data")