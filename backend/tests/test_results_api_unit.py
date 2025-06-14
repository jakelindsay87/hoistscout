"""Unit tests for the results API endpoint."""
import json
import os
from datetime import datetime, UTC
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from hoistscraper.main import app
from hoistscraper.models import Website, ScrapeJob, JobStatus

# Create test client
client = TestClient(app)


def test_get_results_endpoint_exists():
    """Test that the results endpoint is registered."""
    # This will return 404 for "job not found" instead of 405 for "method not allowed"
    # which proves the endpoint exists
    response = client.get("/api/results/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch('routers.jobs.get_session')
def test_get_results_success(mock_get_session):
    """Test successful retrieval of scrape results."""
    # Mock session and database objects
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    # Create mock website and job
    mock_website = Website(
        id=1,
        url="https://example.com",
        name="Test Site",
        description="Test site for results"
    )
    
    mock_job = ScrapeJob(
        id=1,
        website_id=1,
        status=JobStatus.COMPLETED,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        raw_data="test_result.json"
    )
    
    # Configure mocks
    mock_session.get.side_effect = lambda model, id: {
        (ScrapeJob, 1): mock_job,
        (Website, 1): mock_website
    }.get((model, id))
    
    # Create temporary result file
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DATA_DIR"] = temp_dir
        
        # Create result file
        result_data = {
            "website_id": 1,
            "url": "https://example.com",
            "title": "Test Page",
            "scraped_at": datetime.now(UTC).isoformat(),
            "html_path": "test.html",
            "metadata": {"test": "data"}
        }
        
        result_path = Path(temp_dir) / "test_result.json"
        with open(result_path, 'w') as f:
            json.dump(result_data, f)
        
        # Make the request
        response = client.get("/api/results/1")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["jobId"] == "1"
        assert data["websiteId"] == 1
        assert data["url"] == "https://example.com"
        assert "scrapedAt" in data
        assert data["data"]["metadata"]["test"] == "data"


@patch('routers.jobs.get_session')
def test_get_results_job_not_completed(mock_get_session):
    """Test results endpoint with incomplete job."""
    # Mock session and job
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    mock_job = ScrapeJob(
        id=1,
        website_id=1,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC)
    )
    
    mock_session.get.return_value = mock_job
    
    # Make the request
    response = client.get("/api/results/1")
    
    # Verify response
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


@patch('routers.jobs.get_session')  
def test_get_results_no_result_file(mock_get_session):
    """Test results endpoint when job has no result path."""
    # Mock session and job
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    mock_job = ScrapeJob(
        id=1,
        website_id=1,
        status=JobStatus.COMPLETED,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        raw_data=None  # No result path
    )
    
    mock_session.get.return_value = mock_job
    
    # Make the request
    response = client.get("/api/results/1")
    
    # Verify response
    assert response.status_code == 404
    assert "no results found" in response.json()["detail"].lower()


def test_results_api_integration():
    """Test that the results API is properly integrated into the app."""
    # Get the OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    # Check that the results endpoint is documented
    openapi = response.json()
    assert "/api/results/{job_id}" in openapi["paths"]
    
    # Verify the endpoint method and description
    results_endpoint = openapi["paths"]["/api/results/{job_id}"]
    assert "get" in results_endpoint
    assert "scrape results" in results_endpoint["get"]["summary"].lower()