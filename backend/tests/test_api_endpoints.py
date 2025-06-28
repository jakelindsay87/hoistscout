"""
Tests for HoistScraper API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from hoistscraper.main import app
from hoistscraper.db import get_session
from hoistscraper.models import Website, ScrapeJob, Opportunity, WebsiteCredential
from hoistscraper.logging_config import setup_logging


# Setup test logging
setup_logging("hoistscraper-test", log_level="DEBUG", use_json=False)


@pytest.fixture(name="session")
def session_fixture():
    """Create a new database session for testing."""
    # Use in-memory SQLite for tests
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
    """Create a test client with overridden dependencies."""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


class TestRootEndpoints:
    """Test root and health endpoints."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "HoistScraper API"
        assert "version" in data
    
    def test_health_endpoint(self, client: TestClient):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hoistscraper-api"


class TestWebsiteEndpoints:
    """Test website CRUD operations."""
    
    def test_create_website(self, client: TestClient):
        """Test creating a new website."""
        website_data = {
            "name": "Test Grant Site",
            "url": "https://grants.example.com",
            "description": "Test grant website",
            "category": "grants",
            "is_active": True,
            "scrape_frequency": "daily"
        }
        
        response = client.post("/api/websites", json=website_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == website_data["name"]
        assert data["url"] == website_data["url"]
        assert data["id"] is not None
    
    def test_create_duplicate_website(self, client: TestClient, session: Session):
        """Test creating a website with duplicate URL returns 409."""
        # Create first website
        website = Website(
            name="Existing Site",
            url="https://duplicate.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        
        # Try to create duplicate
        website_data = {
            "name": "Duplicate Site",
            "url": "https://duplicate.example.com",
            "category": "tenders"
        }
        
        response = client.post("/api/websites", json=website_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_get_all_websites(self, client: TestClient, session: Session):
        """Test retrieving all websites."""
        # Create test websites
        websites = [
            Website(name=f"Site {i}", url=f"https://site{i}.com", category="grants")
            for i in range(3)
        ]
        session.add_all(websites)
        session.commit()
        
        response = client.get("/api/websites")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert all("id" in site for site in data)
    
    def test_get_website_by_id(self, client: TestClient, session: Session):
        """Test retrieving a specific website by ID."""
        website = Website(
            name="Specific Site",
            url="https://specific.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        response = client.get(f"/api/websites/{website.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == website.id
        assert data["name"] == website.name
    
    def test_get_nonexistent_website(self, client: TestClient):
        """Test retrieving a non-existent website returns 404."""
        response = client.get("/api/websites/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_website(self, client: TestClient, session: Session):
        """Test updating an existing website."""
        website = Website(
            name="Original Name",
            url="https://original.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        update_data = {
            "name": "Updated Name",
            "url": "https://original.example.com",  # Keep same URL
            "category": "tenders",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/websites/{website.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["category"] == update_data["category"]
        assert data["description"] == update_data["description"]
    
    def test_delete_website(self, client: TestClient, session: Session):
        """Test deleting a website."""
        website = Website(
            name="To Delete",
            url="https://delete.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        response = client.delete(f"/api/websites/{website.id}")
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify website is deleted
        deleted = session.get(Website, website.id)
        assert deleted is None


class TestScrapeJobEndpoints:
    """Test scrape job operations."""
    
    def test_create_scrape_job(self, client: TestClient, session: Session):
        """Test creating a new scrape job."""
        # Create a website first
        website = Website(
            name="Job Test Site",
            url="https://jobtest.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job_data = {"website_id": website.id}
        
        response = client.post("/api/scrape-jobs", json=job_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["website_id"] == website.id
        assert data["status"] == "pending"
        assert data["id"] is not None
    
    def test_create_job_invalid_website(self, client: TestClient):
        """Test creating a job for non-existent website returns 404."""
        job_data = {"website_id": 999}
        
        response = client.post("/api/scrape-jobs", json=job_data)
        assert response.status_code == 404
        assert "Website not found" in response.json()["detail"]
    
    def test_get_all_jobs(self, client: TestClient, session: Session):
        """Test retrieving all scrape jobs."""
        # Create website and jobs
        website = Website(name="Site", url="https://site.com", category="grants")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        jobs = [
            ScrapeJob(website_id=website.id, status="pending"),
            ScrapeJob(website_id=website.id, status="completed"),
            ScrapeJob(website_id=website.id, status="failed")
        ]
        session.add_all(jobs)
        session.commit()
        
        response = client.get("/api/scrape-jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        statuses = [job["status"] for job in data]
        assert "pending" in statuses
        assert "completed" in statuses
        assert "failed" in statuses
    
    def test_get_job_by_id(self, client: TestClient, session: Session):
        """Test retrieving a specific job by ID."""
        website = Website(name="Site", url="https://site.com", category="grants")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(website_id=website.id, status="running")
        session.add(job)
        session.commit()
        session.refresh(job)
        
        response = client.get(f"/api/scrape-jobs/{job.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == job.id
        assert data["status"] == "running"


class TestOpportunityEndpoints:
    """Test opportunity operations."""
    
    def test_get_all_opportunities(self, client: TestClient, session: Session):
        """Test retrieving all opportunities."""
        # Create website, job, and opportunities
        website = Website(name="Site", url="https://site.com", category="grants")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(website_id=website.id, status="completed")
        session.add(job)
        session.commit()
        session.refresh(job)
        
        opportunities = [
            Opportunity(
                title=f"Grant Opportunity {i}",
                description=f"Description {i}",
                source_url=f"https://site.com/grant{i}",
                website_id=website.id,
                job_id=job.id
            )
            for i in range(3)
        ]
        session.add_all(opportunities)
        session.commit()
        
        response = client.get("/api/opportunities")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert all("title" in opp for opp in data)
    
    def test_get_opportunity_by_id(self, client: TestClient, session: Session):
        """Test retrieving a specific opportunity by ID."""
        website = Website(name="Site", url="https://site.com", category="grants")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(website_id=website.id, status="completed")
        session.add(job)
        session.commit()
        session.refresh(job)
        
        opportunity = Opportunity(
            title="Specific Grant",
            description="A specific grant opportunity",
            source_url="https://site.com/specific",
            website_id=website.id,
            job_id=job.id,
            amount="$100,000"
        )
        session.add(opportunity)
        session.commit()
        session.refresh(opportunity)
        
        response = client.get(f"/api/opportunities/{opportunity.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == opportunity.id
        assert data["title"] == opportunity.title
        assert data["amount"] == opportunity.amount
    
    def test_search_opportunities(self, client: TestClient, session: Session):
        """Test searching opportunities."""
        website = Website(name="Site", url="https://site.com", category="grants")
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(website_id=website.id, status="completed")
        session.add(job)
        session.commit()
        session.refresh(job)
        
        opportunities = [
            Opportunity(
                title="Technology Innovation Grant",
                description="Grant for tech startups",
                source_url="https://site.com/tech",
                website_id=website.id,
                job_id=job.id
            ),
            Opportunity(
                title="Environmental Research Grant",
                description="Grant for environmental projects",
                source_url="https://site.com/env",
                website_id=website.id,
                job_id=job.id
            ),
            Opportunity(
                title="Community Development Fund",
                description="Fund for community projects",
                source_url="https://site.com/community",
                website_id=website.id,
                job_id=job.id
            )
        ]
        session.add_all(opportunities)
        session.commit()
        
        # Search for "Grant"
        response = client.get("/api/opportunities/search?q=Grant")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2  # Should find Technology and Environmental grants
        titles = [opp["title"] for opp in data]
        assert "Technology Innovation Grant" in titles
        assert "Environmental Research Grant" in titles


class TestStatsEndpoint:
    """Test statistics endpoint."""
    
    def test_get_stats(self, client: TestClient, session: Session):
        """Test retrieving system statistics."""
        # Create test data
        websites = [
            Website(name=f"Site {i}", url=f"https://site{i}.com", category="grants", is_active=(i % 2 == 0))
            for i in range(5)
        ]
        session.add_all(websites)
        session.commit()
        
        jobs = [
            ScrapeJob(website_id=websites[0].id, status="completed"),
            ScrapeJob(website_id=websites[1].id, status="pending"),
            ScrapeJob(website_id=websites[2].id, status="failed"),
        ]
        session.add_all(jobs)
        session.commit()
        
        opportunities = [
            Opportunity(
                title=f"Opportunity {i}",
                source_url=f"https://opp{i}.com",
                website_id=websites[0].id,
                job_id=jobs[0].id
            )
            for i in range(10)
        ]
        session.add_all(opportunities)
        session.commit()
        
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_websites"] == 5
        assert data["active_websites"] == 3  # Sites 0, 2, 4 are active
        assert data["total_jobs"] == 3
        assert data["total_opportunities"] == 10
        assert "jobs_by_status" in data
        assert data["jobs_by_status"]["completed"] == 1
        assert data["jobs_by_status"]["pending"] == 1
        assert data["jobs_by_status"]["failed"] == 1


class TestCSVIngestion:
    """Test CSV file ingestion."""
    
    def test_ingest_csv(self, client: TestClient):
        """Test ingesting websites from CSV file."""
        csv_content = """name,url,description,category
Test Grant Site 1,https://grants1.example.com,First test site,grants
Test Grant Site 2,https://grants2.example.com,Second test site,tenders
Test Grant Site 3,https://grants3.example.com,Third test site,grants
"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post("/api/ingest/csv", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 3
        assert data["skipped"] == 0
    
    def test_ingest_csv_with_duplicates(self, client: TestClient, session: Session):
        """Test ingesting CSV with duplicate URLs."""
        # Create existing website
        existing = Website(
            name="Existing Site",
            url="https://grants1.example.com",
            category="grants"
        )
        session.add(existing)
        session.commit()
        
        csv_content = """name,url,description,category
Test Grant Site 1,https://grants1.example.com,Duplicate URL,grants
Test Grant Site 2,https://grants2.example.com,New site,tenders
"""
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post("/api/ingest/csv", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1
        assert data["skipped"] == 1
    
    def test_ingest_invalid_csv(self, client: TestClient):
        """Test ingesting invalid CSV file."""
        csv_content = """invalid,csv,without,proper,headers
some,random,data,here
"""
        
        files = {"file": ("invalid.csv", csv_content, "text/csv")}
        response = client.post("/api/ingest/csv", files=files)
        
        assert response.status_code == 422  # Validation error


class TestAuthentication:
    """Test API authentication."""
    
    def test_protected_endpoint_without_auth(self, client: TestClient):
        """Test accessing protected endpoint without authentication."""
        import os
        # Set API key requirement
        os.environ["REQUIRE_AUTH"] = "true"
        os.environ["API_KEY"] = "test-api-key"
        
        website_data = {
            "name": "Test Site",
            "url": "https://test.example.com",
            "category": "grants"
        }
        
        response = client.post("/api/websites", json=website_data)
        # Should still work with optional auth (current implementation)
        assert response.status_code == 200
        
        # Clean up
        del os.environ["REQUIRE_AUTH"]
        del os.environ["API_KEY"]


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_malformed_json_request(self, client: TestClient):
        """Test handling malformed JSON in request."""
        response = client.post(
            "/api/websites",
            data="{'invalid': json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test creating website without required fields."""
        website_data = {
            "description": "Missing required fields"
        }
        
        response = client.post("/api/websites", json=website_data)
        assert response.status_code == 422
    
    def test_invalid_data_types(self, client: TestClient):
        """Test with invalid data types."""
        website_data = {
            "name": 123,  # Should be string
            "url": "not-a-valid-url",
            "category": ["invalid", "list"],  # Should be string
            "is_active": "yes"  # Should be boolean
        }
        
        response = client.post("/api/websites", json=website_data)
        assert response.status_code == 422