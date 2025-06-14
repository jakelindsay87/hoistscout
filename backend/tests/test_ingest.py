"""Tests for CSV ingest functionality."""
import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel, select
import tempfile
from hoistscraper.main import app
from hoistscraper import models, db

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
    def get_test_session():
        with Session(engine) as session:
            yield session
    
    app.dependency_overrides[db.get_session] = get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mini_csv_path():
    """Path to mini test CSV file."""
    return Path(__file__).parent / "fixtures" / "mini_sites.csv"


@pytest.fixture
def large_csv_file():
    """Create a large CSV file for performance testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("url,name,description\n")
        for i in range(10000):
            f.write(f"https://site{i}.example.com,Site {i},Description for site {i}\n")
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


class TestCSVIngest:
    """Test CSV ingest endpoints."""
    
    def test_ingest_csv_success(self, client, mini_csv_path):
        """Test successful CSV upload."""
        with open(mini_csv_path, 'rb') as f:
            response = client.post(
                "/api/ingest/csv",
                files={"file": ("mini_sites.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 5
        assert data["skipped"] == 0
        assert data["total"] == 5
        assert len(data["errors"]) == 0
    
    def test_ingest_csv_duplicates(self, client, mini_csv_path):
        """Test CSV upload with duplicate URLs."""
        # Upload once
        with open(mini_csv_path, 'rb') as f:
            response1 = client.post(
                "/api/ingest/csv",
                files={"file": ("mini_sites.csv", f, "text/csv")}
            )
        assert response1.json()["imported"] == 5
        
        # Upload again - all should be skipped
        with open(mini_csv_path, 'rb') as f:
            response2 = client.post(
                "/api/ingest/csv",
                files={"file": ("mini_sites.csv", f, "text/csv")}
            )
        
        assert response2.status_code == 200
        data = response2.json()
        assert data["imported"] == 0
        assert data["skipped"] == 5
        assert data["total"] == 5
    
    def test_ingest_invalid_file_type(self, client):
        """Test uploading non-CSV file."""
        response = client.post(
            "/api/ingest/csv",
            files={"file": ("test.txt", b"not a csv", "text/plain")}
        )
        assert response.status_code == 400
        assert "must be a CSV" in response.json()["detail"]
    
    def test_ingest_malformed_csv(self, client):
        """Test uploading malformed CSV."""
        csv_content = b"url,name\nno quotes here\"and broken\nformat"
        response = client.post(
            "/api/ingest/csv",
            files={"file": ("bad.csv", csv_content, "text/csv")}
        )
        assert response.status_code == 400
        assert "Invalid CSV format" in response.json()["detail"]
    
    def test_ingest_missing_required_fields(self, client):
        """Test CSV with missing required fields."""
        csv_content = b"url,name,description\n,Missing URL,Description\nhttps://test.com,,Missing name\n"
        response = client.post(
            "/api/ingest/csv",
            files={"file": ("partial.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0
        assert data["skipped"] == 2
        assert len(data["errors"]) == 2
        assert "Missing required url or name" in data["errors"][0]
    
    def test_ingest_large_file_performance(self, client, large_csv_file):
        """Test that 10k row import completes in under 30 seconds."""
        import time
        
        start_time = time.time()
        
        with open(large_csv_file, 'rb') as f:
            response = client.post(
                "/api/ingest/csv",
                files={"file": ("large.csv", f, "text/csv")}
            )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 10000
        assert data["total"] == 10000
        assert elapsed_time < 30  # Must complete in under 30 seconds
    
    def test_legacy_ingest_endpoint(self, client):
        """Test the legacy /sites/csv endpoint still works."""
        csv_content = b"Jurisdiction/Body,URL,Level,Type\nTest Org,https://legacy.test.com,Federal,Grant\n"
        response = client.post(
            "/api/ingest/sites/csv",
            files={"file": ("legacy.csv", csv_content, "text/csv")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Org"
        assert data[0]["url"] == "https://legacy.test.com"


class TestCLIImport:
    """Test CLI import functionality."""
    
    def test_cli_import_success(self, session, mini_csv_path):
        """Test CLI import function."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cli.import_csv import run
        
        imported = run(str(mini_csv_path))
        assert imported == 5
        
        # Verify in database
        websites = session.exec(select(models.Website)).all()
        assert len(websites) == 5
        assert any(w.url == "https://grants.gov" for w in websites)
    
    def test_cli_import_file_not_found(self):
        """Test CLI import with non-existent file."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cli.import_csv import run
        
        imported = run("/path/to/nonexistent.csv")
        assert imported == 0
    
    def test_cli_import_invalid_extension(self, tmpdir):
        """Test CLI import with non-CSV file."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cli.import_csv import run
        
        txt_file = tmpdir.join("test.txt")
        txt_file.write("not a csv")
        
        imported = run(str(txt_file))
        assert imported == 0


class TestAutoSeed:
    """Test auto-seed functionality."""
    
    @pytest.mark.asyncio
    async def test_auto_seed_empty_db(self, session, mini_csv_path, monkeypatch):
        """Test auto-seed runs when database is empty."""
        from hoistscraper.main import auto_seed_from_csv
        
        # Set environment variable
        monkeypatch.setenv("CSV_SEED_PATH", str(mini_csv_path))
        
        # Run auto-seed
        await auto_seed_from_csv(str(mini_csv_path))
        
        # Verify websites were imported
        websites = session.exec(select(models.Website)).all()
        assert len(websites) == 5
    
    @pytest.mark.asyncio
    async def test_auto_seed_skips_populated_db(self, session, mini_csv_path, monkeypatch):
        """Test auto-seed skips when database has data."""
        from hoistscraper.main import auto_seed_from_csv
        
        # Add a website
        website = models.Website(
            url="https://existing.com",
            name="Existing Site"
        )
        session.add(website)
        session.commit()
        
        # Run auto-seed
        await auto_seed_from_csv(str(mini_csv_path))
        
        # Verify no additional websites were imported
        websites = session.exec(select(models.Website)).all()
        assert len(websites) == 1
        assert websites[0].url == "https://existing.com"
    
    @pytest.mark.asyncio
    async def test_auto_seed_missing_file(self, session):
        """Test auto-seed handles missing file gracefully."""
        from hoistscraper.main import auto_seed_from_csv
        
        # Should not raise exception
        await auto_seed_from_csv("/path/to/missing.csv")
        
        # Database should remain empty
        websites = session.exec(select(models.Website)).all()
        assert len(websites) == 0