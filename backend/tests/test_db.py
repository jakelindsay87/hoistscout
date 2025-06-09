"""Comprehensive test suite for database operations and models."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool
from datetime import datetime, UTC

from hoistscraper.main import app
from hoistscraper import models, db


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with test database."""
    def get_session_override():
        return session

    app.dependency_overrides[db.get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestWebsiteModel:
    """Test Website model operations."""

    def test_create_website(self, session: Session):
        """Test creating a website."""
        website = models.Website(
            url="https://example.com/jobs",
            name="Example Jobs",
            description="Example company job board"
        )
        session.add(website)
        session.commit()
        session.refresh(website)

        assert website.id is not None
        assert website.url == "https://example.com/jobs"
        assert website.name == "Example Jobs"
        assert website.description == "Example company job board"
        assert website.active is True
        assert isinstance(website.created_at, datetime)
        assert isinstance(website.updated_at, datetime)

    def test_unique_url_constraint(self, session: Session):
        """Test that duplicate URLs are rejected."""
        url = "https://duplicate.com/jobs"
        
        # Create first website
        website1 = models.Website(url=url, name="First")
        session.add(website1)
        session.commit()

        # Try to create second website with same URL
        website2 = models.Website(url=url, name="Second")
        session.add(website2)
        
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            session.commit()

    def test_website_read_model(self):
        """Test WebsiteRead model validation."""
        website_data = {
            "id": 1,
            "url": "https://test.com",
            "name": "Test",
            "active": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        }
        website = models.WebsiteRead(**website_data)
        assert website.id == 1
        assert website.url == "https://test.com"


class TestScrapeJobModel:
    """Test ScrapeJob model operations."""

    def test_create_scrape_job(self, session: Session):
        """Test creating a scrape job."""
        # First create a website
        website = models.Website(url="https://example.com", name="Example")
        session.add(website)
        session.commit()
        session.refresh(website)

        # Create scrape job
        job = models.ScrapeJob(
            website_id=website.id,
            status=models.JobStatus.PENDING
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.id is not None
        assert job.website_id == website.id
        assert job.status == models.JobStatus.PENDING
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error_message is None
        assert job.raw_data is None

    def test_job_status_enum(self):
        """Test JobStatus enum values."""
        assert models.JobStatus.PENDING == "pending"
        assert models.JobStatus.RUNNING == "running"
        assert models.JobStatus.COMPLETED == "completed"
        assert models.JobStatus.FAILED == "failed"

    def test_scrape_job_with_data(self, session: Session):
        """Test scrape job with all fields populated."""
        website = models.Website(url="https://test.com", name="Test")
        session.add(website)
        session.commit()
        session.refresh(website)

        now = datetime.now(UTC)
        job = models.ScrapeJob(
            website_id=website.id,
            status=models.JobStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            raw_data='{"jobs": [{"title": "Software Engineer"}]}'
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.status == models.JobStatus.COMPLETED
        assert job.started_at == now
        assert job.completed_at == now
        assert job.raw_data == '{"jobs": [{"title": "Software Engineer"}]}'


class TestWebsiteAPI:
    """Test Website API endpoints."""

    def test_create_website_api(self, client: TestClient):
        """Test creating website via API."""
        website_data = {
            "url": "https://api-test.com/jobs",
            "name": "API Test Company",
            "description": "Test description",
            "active": True
        }
        response = client.post("/api/websites", json=website_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == website_data["url"]
        assert data["name"] == website_data["name"]
        assert data["description"] == website_data["description"]
        assert "id" in data
        assert "created_at" in data

    def test_create_duplicate_website_api(self, client: TestClient):
        """Test duplicate URL returns HTTP 409."""
        website_data = {
            "url": "https://duplicate-api.com/jobs",
            "name": "First Company"
        }
        
        # Create first website
        response = client.post("/api/websites", json=website_data)
        assert response.status_code == 200

        # Try to create duplicate
        duplicate_data = {
            "url": "https://duplicate-api.com/jobs",
            "name": "Second Company"
        }
        response = client.post("/api/websites", json=duplicate_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_get_websites_api(self, client: TestClient):
        """Test getting all websites."""
        # Create test websites
        for i in range(3):
            website_data = {
                "url": f"https://test{i}.com/jobs",
                "name": f"Test Company {i}"
            }
            client.post("/api/websites", json=website_data)

        response = client.get("/api/websites")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("id" in website for website in data)

    def test_get_website_by_id(self, client: TestClient):
        """Test getting specific website by ID."""
        # Create website
        website_data = {"url": "https://specific.com", "name": "Specific"}
        create_response = client.post("/api/websites", json=website_data)
        website_id = create_response.json()["id"]

        # Get website by ID
        response = client.get(f"/api/websites/{website_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == website_id
        assert data["url"] == website_data["url"]

    def test_get_nonexistent_website(self, client: TestClient):
        """Test getting non-existent website returns 404."""
        response = client.get("/api/websites/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_website_api(self, client: TestClient):
        """Test updating website via API."""
        # Create website
        create_data = {"url": "https://update-test.com", "name": "Original"}
        create_response = client.post("/api/websites", json=create_data)
        website_id = create_response.json()["id"]

        # Update website
        update_data = {"url": "https://updated.com", "name": "Updated", "active": False}
        response = client.put(f"/api/websites/{website_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == update_data["url"]
        assert data["name"] == update_data["name"]
        assert data["active"] == update_data["active"]

    def test_delete_website_api(self, client: TestClient):
        """Test deleting website via API."""
        # Create website
        create_data = {"url": "https://delete-test.com", "name": "Delete Me"}
        create_response = client.post("/api/websites", json=create_data)
        website_id = create_response.json()["id"]

        # Delete website
        response = client.delete(f"/api/websites/{website_id}")
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Verify deletion
        get_response = client.get(f"/api/websites/{website_id}")
        assert get_response.status_code == 404


class TestScrapeJobAPI:
    """Test ScrapeJob API endpoints."""

    def test_create_scrape_job_api(self, client: TestClient):
        """Test creating scrape job via API."""
        # Create website first
        website_data = {"url": "https://job-test.com", "name": "Job Test"}
        website_response = client.post("/api/websites", json=website_data)
        website_id = website_response.json()["id"]

        # Create scrape job
        job_data = {
            "website_id": website_id,
            "status": "pending"
        }
        response = client.post("/api/scrape-jobs", json=job_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["website_id"] == website_id
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_job_for_nonexistent_website(self, client: TestClient):
        """Test creating job for non-existent website returns 404."""
        job_data = {
            "website_id": 999,
            "status": "pending"
        }
        response = client.post("/api/scrape-jobs", json=job_data)
        assert response.status_code == 404
        assert "Website not found" in response.json()["detail"]

    def test_get_scrape_jobs_api(self, client: TestClient):
        """Test getting all scrape jobs."""
        # Create website and jobs
        website_data = {"url": "https://jobs-list.com", "name": "Jobs List"}
        website_response = client.post("/api/websites", json=website_data)
        website_id = website_response.json()["id"]

        for i in range(2):
            job_data = {"website_id": website_id, "status": "pending"}
            client.post("/api/scrape-jobs", json=job_data)

        response = client.get("/api/scrape-jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_scrape_job_status(self, client: TestClient):
        """Test updating scrape job status."""
        # Create website and job
        website_data = {"url": "https://status-test.com", "name": "Status Test"}
        website_response = client.post("/api/websites", json=website_data)
        website_id = website_response.json()["id"]

        job_data = {"website_id": website_id, "status": "pending"}
        job_response = client.post("/api/scrape-jobs", json=job_data)
        job_id = job_response.json()["id"]

        # Update job status
        update_data = {
            "website_id": website_id,
            "status": "completed",
            "raw_data": '{"results": "success"}'
        }
        response = client.put(f"/api/scrape-jobs/{job_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["raw_data"] == '{"results": "success"}'


class TestDatabaseCoverage:
    """Test database operations for coverage."""

    def test_database_session_rollback(self, session: Session):
        """Test session rollback on error."""
        website = models.Website(url="https://rollback.com", name="Rollback Test")
        session.add(website)
        session.commit()

        # Attempt to create duplicate (should trigger rollback)
        duplicate = models.Website(url="https://rollback.com", name="Duplicate")
        session.add(duplicate)
        
        with pytest.raises(Exception):
            session.commit()
        
        # Session should still be usable after rollback
        session.rollback()
        count = session.exec(select(models.Website)).all()
        assert len(count) == 1

    def test_model_validation(self):
        """Test model validation."""
        # Test WebsiteCreate validation
        website_create = models.WebsiteCreate(
            url="https://validate.com",
            name="Validation Test"
        )
        assert website_create.url == "https://validate.com"
        assert website_create.active is True  # default value

        # Test ScrapeJobCreate validation
        job_create = models.ScrapeJobCreate(
            website_id=1,
            status=models.JobStatus.RUNNING
        )
        assert job_create.website_id == 1
        assert job_create.status == models.JobStatus.RUNNING

    def test_database_connection_parameters(self):
        """Test database engine configuration."""
        from hoistscraper.db import engine
        assert engine.pool._pre_ping is True
        assert engine.pool._recycle == 300