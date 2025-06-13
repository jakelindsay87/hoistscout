"""Database and API tests for HoistScraper."""
import os
import pytest
from datetime import datetime

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select

from hoistscraper.main import app
from hoistscraper.db import get_session
from hoistscraper.models import Website, ScrapeJob

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


class TestDatabase:
    """Test database models and operations."""
    
    def test_create_website(self, session):
        """Test creating a website."""
        website = Website(
            url="https://example.com",
            name="Example Site",
            description="Test description"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        assert website.id is not None
        assert website.url == "https://example.com"
        assert website.name == "Example Site"
        assert website.description == "Test description"
        assert isinstance(website.created_at, datetime)
        assert isinstance(website.updated_at, datetime)
    
    def test_create_scrape_job(self, session):
        """Test creating a scrape job."""
        # Create website first
        website = Website(url="https://example.com", name="Example")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        # Create scrape job
        job = ScrapeJob(
            website_id=website.id,
            status="pending"
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        assert job.id is not None
        assert job.website_id == website.id
        assert job.status == "pending"
        assert job.started_at is None
        assert job.completed_at is None
        assert isinstance(job.created_at, datetime)
    
    def test_unique_url_constraint(self, session):
        """Test that duplicate URLs are not allowed."""
        website1 = Website(url="https://example.com", name="Example 1")
        session.add(website1)
        session.commit()
        
        website2 = Website(url="https://example.com", name="Example 2")
        session.add(website2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            session.commit()


class TestSitesAPI:
    """Test sites API endpoints."""
    
    def test_create_site(self, client):
        """Test creating a site via API."""
        response = client.post(
            "/api/sites",
            json={
                "url": "https://test.example.com",
                "name": "Test Site",
                "description": "A test website"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://test.example.com/"  # FastAPI normalizes URLs
        assert data["name"] == "Test Site"
        assert data["description"] == "A test website"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_duplicate_site(self, client):
        """Test that creating duplicate site returns 409."""
        # Create first site
        client.post(
            "/api/sites",
            json={
                "url": "https://duplicate.example.com",
                "name": "First Site"
            }
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/sites",
            json={
                "url": "https://duplicate.example.com",
                "name": "Second Site"
            }
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_list_sites_empty(self, client):
        """Test listing sites when none exist."""
        response = client.get("/api/sites")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 0
    
    def test_list_sites_with_pagination(self, client):
        """Test listing sites with pagination."""
        # Create 25 sites
        for i in range(25):
            client.post(
                "/api/sites",
                json={
                    "url": f"https://site{i}.example.com",
                    "name": f"Site {i}"
                }
            )
        
        # Get first page
        response = client.get("/api/sites?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_pages"] == 3
        
        # Get second page
        response = client.get("/api/sites?page=2&page_size=10")
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2
        
        # Get last page
        response = client.get("/api/sites?page=3&page_size=10")
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 3
    
    def test_get_site(self, client):
        """Test getting a single site."""
        # Create a site
        create_response = client.post(
            "/api/sites",
            json={
                "url": "https://single.example.com",
                "name": "Single Site"
            }
        )
        site_id = create_response.json()["id"]
        
        # Get the site
        response = client.get(f"/api/sites/{site_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == site_id
        assert data["url"] == "https://single.example.com/"
        assert data["name"] == "Single Site"
    
    def test_get_nonexistent_site(self, client):
        """Test getting a site that doesn't exist."""
        response = client.get("/api/sites/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Site not found"
    
    def test_invalid_url(self, client):
        """Test creating site with invalid URL."""
        response = client.post(
            "/api/sites",
            json={
                "url": "not-a-valid-url",
                "name": "Invalid URL Site"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_sites_ordered_by_created_at(self, client):
        """Test that sites are returned in reverse chronological order."""
        # Create sites with small delays
        import time
        for i in range(3):
            client.post(
                "/api/sites",
                json={
                    "url": f"https://ordered{i}.example.com",
                    "name": f"Ordered Site {i}"
                }
            )
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        response = client.get("/api/sites")
        items = response.json()["items"]
        
        # Most recent should be first
        assert items[0]["name"] == "Ordered Site 2"
        assert items[1]["name"] == "Ordered Site 1"
        assert items[2]["name"] == "Ordered Site 0"


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}