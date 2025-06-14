"""Tests for the results API endpoint."""
import json
import os
from datetime import datetime, UTC
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from hoistscraper.main import app
from hoistscraper.db import get_session
from hoistscraper.models import Website, ScrapeJob, JobStatus

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Test database URL
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hoistscraper_test")


@pytest.fixture(scope="function")
def engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """Create a test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(engine):
    """Create a test client with test database."""
    # Override the get_session dependency
    def get_test_session():
        with Session(engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_get_results_success(client: TestClient, session: Session):
    """Test successful retrieval of scrape results."""
    # Create test data
    website = Website(
        url="https://example.com",
        name="Test Site",
        description="Test site for results"
    )
    session.add(website)
    session.commit()
    
    # Create a completed job with results
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set DATA_DIR to temp directory
        os.environ["DATA_DIR"] = temp_dir
        
        # Create result file
        result_data = {
            "website_id": website.id,
            "url": website.url,
            "title": "Test Page",
            "scraped_at": datetime.now(UTC).isoformat(),
            "html_path": f"{website.id}_1.html",
            "metadata": {"test": "data"}
        }
        
        result_filename = f"{website.id}_1.json"
        result_path = Path(temp_dir) / result_filename
        with open(result_path, 'w') as f:
            json.dump(result_data, f)
        
        # Create job pointing to result file
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            raw_data=result_filename
        )
        session.add(job)
        session.commit()
        
        # Test the endpoint
        response = client.get(f"/api/results/{job.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["jobId"] == str(job.id)
        assert data["websiteId"] == website.id
        assert data["url"] == website.url
        assert "scrapedAt" in data
        assert data["data"]["metadata"]["test"] == "data"


def test_get_results_job_not_found(client: TestClient):
    """Test results endpoint with non-existent job."""
    response = client.get("/api/results/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_results_job_not_completed(client: TestClient, session: Session):
    """Test results endpoint with incomplete job."""
    # Create test data
    website = Website(url="https://example.com", name="Test Site")
    session.add(website)
    session.commit()
    
    job = ScrapeJob(
        website_id=website.id,
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC)
    )
    session.add(job)
    session.commit()
    
    response = client.get(f"/api/results/{job.id}")
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


def test_get_results_file_not_found(client: TestClient, session: Session):
    """Test results endpoint when result file doesn't exist."""
    # Create test data
    website = Website(url="https://example.com", name="Test Site")
    session.add(website)
    session.commit()
    
    job = ScrapeJob(
        website_id=website.id,
        status=JobStatus.COMPLETED,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        raw_data="nonexistent.json"
    )
    session.add(job)
    session.commit()
    
    response = client.get(f"/api/results/{job.id}")
    assert response.status_code == 404
    assert "file not found" in response.json()["detail"].lower()


def test_get_results_invalid_json(client: TestClient, session: Session):
    """Test results endpoint with invalid JSON file."""
    # Create test data
    website = Website(url="https://example.com", name="Test Site")
    session.add(website)
    session.commit()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DATA_DIR"] = temp_dir
        
        # Create invalid JSON file
        result_filename = "invalid.json"
        result_path = Path(temp_dir) / result_filename
        with open(result_path, 'w') as f:
            f.write("{ invalid json")
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            raw_data=result_filename
        )
        session.add(job)
        session.commit()
        
        response = client.get(f"/api/results/{job.id}")
        assert response.status_code == 500
        assert "invalid json" in response.json()["detail"].lower()


def test_get_results_no_result_path(client: TestClient, session: Session):
    """Test results endpoint when job has no result path."""
    # Create test data
    website = Website(url="https://example.com", name="Test Site")
    session.add(website)
    session.commit()
    
    job = ScrapeJob(
        website_id=website.id,
        status=JobStatus.COMPLETED,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        raw_data=None  # No result path
    )
    session.add(job)
    session.commit()
    
    response = client.get(f"/api/results/{job.id}")
    assert response.status_code == 404
    assert "no results found" in response.json()["detail"].lower()


def test_get_results_absolute_path(client: TestClient, session: Session):
    """Test results endpoint with absolute path in raw_data."""
    # Create test data
    website = Website(url="https://example.com", name="Test Site")
    session.add(website)
    session.commit()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create result file with absolute path
        result_data = {
            "website_id": website.id,
            "url": website.url,
            "scraped_at": datetime.now(UTC).isoformat(),
            "data": {"test": "absolute path"}
        }
        
        result_path = Path(temp_dir) / "result.json"
        with open(result_path, 'w') as f:
            json.dump(result_data, f)
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            raw_data=str(result_path)  # Absolute path
        )
        session.add(job)
        session.commit()
        
        response = client.get(f"/api/results/{job.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["data"]["test"] == "absolute path"