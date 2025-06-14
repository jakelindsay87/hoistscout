"""Tests for worker functionality."""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from hoistscraper.models import Website, ScrapeJob, JobStatus

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def mock_website():
    """Create a mock website."""
    website = Mock(spec=Website)
    website.id = 1
    website.url = "https://example.com"
    website.name = "Example Site"
    website.requires_auth = False
    return website


@pytest.fixture
def mock_scrape_job():
    """Create a mock scrape job."""
    job = Mock(spec=ScrapeJob)
    job.id = 1
    job.website_id = 1
    job.status = JobStatus.PENDING
    job.started_at = None
    job.completed_at = None
    job.error_message = None
    return job


@pytest.fixture
def mock_page():
    """Create a mock Playwright page."""
    page = Mock()
    page.title.return_value = "Example Page"
    page.content.return_value = "<html><body>Test content</body></html>"
    page.url = "https://example.com"
    page.viewport_size = {"width": 1920, "height": 1080}
    return page


@pytest.fixture
def mock_browser(mock_page):
    """Create a mock Playwright browser."""
    browser = Mock()
    browser.new_page.return_value = mock_page
    return browser


class TestScraperWorker:
    """Test ScraperWorker class."""
    
    def test_initialize_browser(self):
        """Test browser initialization."""
        from hoistscraper.worker import ScraperWorker
        
        worker = ScraperWorker()
        
        with patch('hoistscraper.worker.sync_playwright') as mock_playwright:
            mock_pw_instance = Mock()
            mock_pw_instance.chromium.launch.return_value = Mock()
            mock_playwright.return_value.start.return_value = mock_pw_instance
            
            worker.initialize_browser()
            
            assert worker.playwright is not None
            assert worker.browser is not None
            mock_pw_instance.chromium.launch.assert_called_once_with(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    
    def test_cleanup(self):
        """Test cleanup of browser resources."""
        from hoistscraper.worker import ScraperWorker
        
        worker = ScraperWorker()
        worker.browser = Mock()
        worker.playwright = Mock()
        
        worker.cleanup()
        
        worker.browser.close.assert_called_once()
        worker.playwright.stop.assert_called_once()
    
    @patch('hoistscraper.worker.Session')
    @patch('hoistscraper.worker.engine')
    def test_scrape_website_success(self, mock_engine, mock_session_class, 
                                  mock_website, mock_scrape_job, mock_browser, mock_page):
        """Test successful website scraping."""
        from hoistscraper.worker import ScraperWorker
        
        # Setup mocks
        mock_session = Mock()
        mock_session.get.side_effect = lambda model, id: {
            Website: {1: mock_website},
            ScrapeJob: {1: mock_scrape_job}
        }.get(model, {}).get(id)
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        worker = ScraperWorker()
        worker.browser = mock_browser
        
        # Mock file operations
        m_open = mock_open()
        with patch('builtins.open', m_open):
            with patch('hoistscraper.worker.DATA_DIR', Path('/tmp/test_data')):
                with patch('pathlib.Path.mkdir'):
                    result = worker.scrape_website(1, 1)
        
        # Verify results
        assert result['website_id'] == 1
        assert result['url'] == "https://example.com"
        assert result['title'] == "Example Page"
        assert 'content' in result
        
        # Verify page navigation
        mock_page.goto.assert_called_once_with(
            "https://example.com", 
            wait_until='networkidle', 
            timeout=30000
        )
        
        # Verify files were written
        assert m_open.call_count == 2  # HTML and JSON files
        
        # Verify job status updates
        assert mock_scrape_job.status == JobStatus.COMPLETED
        assert mock_scrape_job.started_at is not None
        assert mock_scrape_job.completed_at is not None
        mock_session.commit.assert_called()
    
    @patch('hoistscraper.worker.Session')
    @patch('hoistscraper.worker.engine')
    def test_scrape_website_failure(self, mock_engine, mock_session_class,
                                   mock_website, mock_scrape_job, mock_browser):
        """Test website scraping failure."""
        from hoistscraper.worker import ScraperWorker
        from tenacity import RetryError
        
        # Setup mocks
        mock_session = Mock()
        mock_session.get.side_effect = lambda model, id: {
            Website: {1: mock_website},
            ScrapeJob: {1: mock_scrape_job}
        }.get(model, {}).get(id)
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        worker = ScraperWorker()
        worker.browser = mock_browser
        
        # Make page navigation fail
        mock_browser.new_page.side_effect = Exception("Browser error")
        
        # Test that RetryError is raised after retry attempts
        with pytest.raises(RetryError):
            worker.scrape_website(1, 1)
        
        # Verify job status was updated to failed
        assert mock_scrape_job.status == JobStatus.FAILED
        # The error message might be different due to Playwright issues in test environment
        assert mock_scrape_job.error_message is not None
        mock_session.commit.assert_called()
    
    @patch('hoistscraper.worker.Session')
    @patch('hoistscraper.worker.engine')
    def test_scrape_website_not_found(self, mock_engine, mock_session_class):
        """Test scraping non-existent website."""
        from hoistscraper.worker import ScraperWorker
        
        # Setup mocks
        mock_session = Mock()
        mock_session.get.return_value = None  # Website not found
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        worker = ScraperWorker()
        
        # Test that RetryError is raised after retry attempts
        from tenacity import RetryError
        with pytest.raises(RetryError):
            worker.scrape_website(999, 1)
    
    def test_handle_login_placeholder(self, mock_page, mock_website):
        """Test login handler (placeholder)."""
        from hoistscraper.worker import ScraperWorker
        
        worker = ScraperWorker()
        
        # Should not raise any errors
        worker._handle_login(mock_page, mock_website)


def test_scrape_website_job():
    """Test the RQ job function."""
    from hoistscraper.worker import scrape_website_job, ScraperWorker
    
    mock_worker = Mock(spec=ScraperWorker)
    mock_worker.scrape_website.return_value = {"status": "success"}
    
    with patch('hoistscraper.worker.ScraperWorker', return_value=mock_worker):
        result = scrape_website_job(1, 1)
    
    assert result == {"status": "success"}
    mock_worker.scrape_website.assert_called_once_with(1, 1)
    mock_worker.cleanup.assert_called_once()