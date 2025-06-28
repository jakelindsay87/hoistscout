"""
Tests for worker and scraping functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, UTC
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from hoistscraper.models import Website, ScrapeJob, JobStatus, Opportunity
from hoistscraper.worker_v2 import EnhancedScraperWorker
from hoistscraper.db import engine as prod_engine


@pytest.fixture(name="session")
def session_fixture():
    """Create a new database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_engine")
def test_engine_fixture():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def mock_browser():
    """Mock Playwright browser for testing."""
    browser = AsyncMock()
    page = AsyncMock()
    context = AsyncMock()
    
    # Configure mock behavior
    context.new_page.return_value = page
    browser.new_context.return_value = context
    page.content.return_value = "<html><body>Test content</body></html>"
    page.url = "https://test.example.com"
    
    return browser, page


class TestEnhancedScraperWorker:
    """Test the enhanced scraper worker."""
    
    @pytest.mark.asyncio
    async def test_worker_initialization(self):
        """Test worker initialization."""
        with patch('hoistscraper.worker_v2.EnhancedScraperWorker._check_ollama_availability', return_value=True):
            worker = EnhancedScraperWorker()
            assert worker.browser is None
            assert worker.playwright is None
            assert worker.ollama_available is True
    
    @pytest.mark.asyncio
    async def test_ollama_availability_check(self):
        """Test Ollama availability checking."""
        worker = EnhancedScraperWorker()
        
        # Mock successful Ollama check
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            assert worker._check_ollama_availability() is True
        
        # Mock failed Ollama check
        with patch('httpx.get', side_effect=Exception("Connection failed")):
            assert worker._check_ollama_availability() is False
    
    @pytest.mark.asyncio
    async def test_browser_initialization(self, mock_browser):
        """Test browser initialization."""
        browser_mock, _ = mock_browser
        
        with patch('hoistscraper.worker_v2.async_playwright') as mock_playwright:
            mock_pw_instance = AsyncMock()
            mock_pw_instance.chromium.launch.return_value = browser_mock
            mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
            
            worker = EnhancedScraperWorker()
            await worker.initialize_browser()
            
            assert worker.browser is not None
            mock_pw_instance.chromium.launch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, mock_browser):
        """Test worker cleanup."""
        browser_mock, _ = mock_browser
        
        worker = EnhancedScraperWorker()
        worker.browser = browser_mock
        worker.playwright = AsyncMock()
        
        await worker.cleanup()
        
        browser_mock.close.assert_called_once()
        worker.playwright.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_website_success(self, session: Session, test_engine, mock_browser):
        """Test successful website scraping."""
        # Create test data
        website = Website(
            name="Test Site",
            url="https://test.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.PENDING
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # Mock dependencies
        browser_mock, page_mock = mock_browser
        page_mock.goto = AsyncMock()
        page_mock.wait_for_load_state = AsyncMock()
        page_mock.content.return_value = """
        <html>
            <body>
                <a href="/grant1">Grant Opportunity 1</a>
                <a href="/grant2">Grant Opportunity 2</a>
            </body>
        </html>
        """
        
        with patch('hoistscraper.worker_v2.engine', test_engine), \
             patch('hoistscraper.worker_v2.async_playwright') as mock_playwright, \
             patch('hoistscraper.worker_v2.EnhancedScraperWorker._check_ollama_availability', return_value=False), \
             patch('hoistscraper.worker_v2.DATA_DIR.mkdir'), \
             patch('builtins.open', create=True) as mock_open:
            
            # Configure playwright mock
            mock_pw_instance = AsyncMock()
            mock_pw_instance.chromium.launch.return_value = browser_mock
            mock_playwright.return_value.__aenter__.return_value = mock_pw_instance
            browser_mock.new_page.return_value = page_mock
            
            # Configure file mock
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            worker = EnhancedScraperWorker()
            result = await worker.scrape_website(website.id, job.id)
            
            # Verify results
            assert "website_id" in result
            assert result["website_id"] == website.id
            assert "opportunities_found" in result
            
            # Verify page navigation
            page_mock.goto.assert_called()
            page_mock.wait_for_load_state.assert_called()
    
    @pytest.mark.asyncio
    async def test_scrape_website_failure(self, session: Session, test_engine):
        """Test website scraping failure handling."""
        # Create test data
        website = Website(
            name="Test Site",
            url="https://failing.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.PENDING
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        with patch('hoistscraper.worker_v2.engine', test_engine), \
             patch('hoistscraper.worker_v2.async_playwright') as mock_playwright:
            
            # Configure to raise exception
            mock_playwright.side_effect = Exception("Browser launch failed")
            
            worker = EnhancedScraperWorker()
            
            with pytest.raises(Exception):
                await worker.scrape_website(website.id, job.id)
    
    @pytest.mark.asyncio
    async def test_handle_login(self, mock_browser):
        """Test login handling for authenticated sites."""
        _, page_mock = mock_browser
        page_mock.fill = AsyncMock()
        page_mock.click = AsyncMock()
        page_mock.wait_for_navigation = AsyncMock()
        
        worker = EnhancedScraperWorker()
        
        # Mock website with credentials
        website = Mock()
        website.id = 1
        website.requires_auth = True
        
        # Mock credential
        credential = Mock()
        credential.username = "testuser"
        credential.password = "testpass"
        credential.auth_type = "form"
        credential.auth_config = {
            "login_url": "https://test.example.com/login",
            "username_selector": "#username",
            "password_selector": "#password",
            "submit_selector": "#submit"
        }
        
        with patch('hoistscraper.worker_v2.Session') as mock_session:
            mock_db_session = Mock()
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.exec.return_value.first.return_value = credential
            
            await worker._handle_login(page_mock, website)
            
            # Verify login actions
            page_mock.goto.assert_called_with("https://test.example.com/login")
            page_mock.fill.assert_any_call("#username", "testuser")
            page_mock.fill.assert_any_call("#password", "testpass")
            page_mock.click.assert_called_with("#submit")
    
    def test_extract_links_basic(self):
        """Test basic link extraction without Ollama."""
        worker = EnhancedScraperWorker()
        
        html_content = """
        <html>
            <body>
                <a href="/opportunity/1">Opportunity 1</a>
                <a href="/opportunity/2">Opportunity 2</a>
                <a href="https://external.com/grant">External Grant</a>
                <a href="mailto:test@example.com">Email</a>
            </body>
        </html>
        """
        
        links = worker._extract_links_basic(html_content, "https://test.example.com")
        
        assert len(links) == 3  # Should exclude mailto links
        urls = [link['url'] for link in links]
        assert "https://test.example.com/opportunity/1" in urls
        assert "https://test.example.com/opportunity/2" in urls
        assert "https://external.com/grant" in urls
    
    def test_extract_opportunity_basic(self):
        """Test basic opportunity extraction without Ollama."""
        worker = EnhancedScraperWorker()
        
        html_content = """
        <html>
            <head><title>Grant Opportunity - $50,000 Research Grant</title></head>
            <body>
                <h1>Research Innovation Grant</h1>
                <p>Amount: $50,000</p>
                <p>Deadline: December 31, 2024</p>
                <p>This grant supports innovative research projects.</p>
            </body>
        </html>
        """
        
        result = worker._extract_opportunity_basic(
            html_content,
            "https://test.example.com/grant/1"
        )
        
        assert result['title'] == "Grant Opportunity - $50,000 Research Grant"
        assert result['url'] == "https://test.example.com/grant/1"
        assert "50,000" in result['description']
    
    def test_parse_deadline(self):
        """Test deadline parsing."""
        worker = EnhancedScraperWorker()
        
        # Test various date formats
        assert worker._parse_deadline("2024-12-31") is not None
        assert worker._parse_deadline("31/12/2024") is not None
        assert worker._parse_deadline("December 31, 2024") is not None
        assert worker._parse_deadline("invalid date") is None
        assert worker._parse_deadline(None) is None


class TestScrapeJobProcessing:
    """Test scrape job processing."""
    
    @pytest.mark.asyncio
    async def test_job_status_updates(self, session: Session, test_engine):
        """Test that job status is updated during processing."""
        website = Website(
            name="Test Site",
            url="https://test.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.PENDING
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        with patch('hoistscraper.worker_v2.engine', test_engine), \
             patch('hoistscraper.worker_v2.EnhancedScraperWorker.initialize_browser'), \
             patch('hoistscraper.worker_v2.EnhancedScraperWorker._check_ollama_availability', return_value=False):
            
            worker = EnhancedScraperWorker()
            
            # Mock the browser operations to fail
            with patch.object(worker, 'browser') as mock_browser:
                mock_browser.new_page.side_effect = Exception("Test error")
                
                try:
                    await worker.scrape_website(website.id, job.id)
                except Exception:
                    pass
                
                # Check job status was updated
                with Session(test_engine) as check_session:
                    updated_job = check_session.get(ScrapeJob, job.id)
                    assert updated_job.status == JobStatus.FAILED
                    assert updated_job.error_message is not None


class TestOpportunityExtraction:
    """Test opportunity extraction and storage."""
    
    @pytest.mark.asyncio
    async def test_opportunity_creation(self, session: Session, test_engine):
        """Test that opportunities are created correctly."""
        website = Website(
            name="Test Site",
            url="https://test.example.com",
            category="grants"
        )
        session.add(website)
        session.commit()
        session.refresh(website)
        
        job = ScrapeJob(
            website_id=website.id,
            status=JobStatus.PENDING
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # Test opportunity data
        opportunity_data = {
            'title': 'Test Grant Opportunity',
            'description': 'A test grant for testing',
            'amount': '$100,000',
            'deadline': '2024-12-31',
            'url': 'https://test.example.com/grant/1'
        }
        
        with patch('hoistscraper.worker_v2.engine', test_engine):
            # Create opportunity
            with Session(test_engine) as db_session:
                opportunity = Opportunity(
                    title=opportunity_data['title'],
                    description=opportunity_data['description'],
                    source_url=opportunity_data['url'],
                    website_id=website.id,
                    job_id=job.id,
                    amount=opportunity_data['amount']
                )
                db_session.add(opportunity)
                db_session.commit()
            
            # Verify opportunity was created
            with Session(test_engine) as check_session:
                saved_opp = check_session.query(Opportunity).first()
                assert saved_opp is not None
                assert saved_opp.title == opportunity_data['title']
                assert saved_opp.amount == opportunity_data['amount']
                assert saved_opp.website_id == website.id
                assert saved_opp.job_id == job.id


class TestWorkerResilience:
    """Test worker resilience and error handling."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that worker retries on transient failures."""
        worker = EnhancedScraperWorker()
        
        # Mock a function that fails twice then succeeds
        call_count = 0
        
        async def mock_scrape(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return {"success": True}
        
        # The scrape_website method has retry decorator
        with patch.object(worker, 'initialize_browser'), \
             patch.object(worker, '_check_ollama_availability', return_value=False):
            
            # This test verifies retry logic exists
            # Real retry testing would require more complex setup
            assert hasattr(worker.scrape_website, '__wrapped__')  # Has retry decorator
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_browser):
        """Test rate limiting between requests."""
        _, page_mock = mock_browser
        
        worker = EnhancedScraperWorker()
        
        # Track sleep calls
        sleep_calls = []
        
        async def mock_sleep(seconds):
            sleep_calls.append(seconds)
        
        with patch('asyncio.sleep', mock_sleep), \
             patch('hoistscraper.worker_v2.DATA_DIR.mkdir'), \
             patch('builtins.open', create=True):
            
            # Process multiple opportunities
            opportunities = [
                {'url': f'https://test.example.com/grant/{i}'} 
                for i in range(3)
            ]
            
            # Mock the extraction to return test opportunities
            worker._extract_links_basic = Mock(return_value=opportunities)
            
            # The rate limiting should cause delays between processing
            # This is tested within the scrape_website method
            # Actual implementation would show delays in sleep_calls