"""Simple test to verify the results endpoint is working."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set SQLite for testing to avoid PostgreSQL dependency
os.environ["DATABASE_URL"] = "sqlite:///test.db"

from fastapi.testclient import TestClient
from hoistscraper.main import app

# Create test client
client = TestClient(app)


def test_results_endpoint_exists():
    """Test that the /api/results/{job_id} endpoint exists."""
    # This should return 404 for "job not found" not 405 for "method not allowed"
    response = client.get("/api/results/99999")
    assert response.status_code == 404
    assert "Job 99999 not found" in response.json()["detail"]
    

def test_openapi_includes_results():
    """Test that the results endpoint is in the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi = response.json()
    # Check that our new endpoint is documented
    assert "/api/results/{job_id}" in openapi["paths"]
    
    # Verify it's a GET endpoint
    endpoint = openapi["paths"]["/api/results/{job_id}"]
    assert "get" in endpoint
    assert "job_id" in endpoint["get"]["parameters"][0]["name"]


if __name__ == "__main__":
    # Run tests
    print("Testing results endpoint...")
    test_results_endpoint_exists()
    print("✓ Results endpoint exists")
    
    test_openapi_includes_results()
    print("✓ Results endpoint in OpenAPI")
    
    print("\nAll tests passed!")