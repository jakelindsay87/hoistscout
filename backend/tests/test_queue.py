"""Tests for queue operations."""
import pytest
from unittest.mock import Mock, patch
from fakeredis import FakeRedis
from rq import Queue
from rq.job import Job

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return FakeRedis()


@pytest.fixture
def mock_queue(fake_redis):
    """Create a mock queue with fake Redis."""
    with patch('hoistscraper.queue.redis_conn', fake_redis):
        with patch('hoistscraper.queue.default_queue', Queue(connection=fake_redis)):
            with patch('hoistscraper.queue.scraper_queue', Queue('scraper', connection=fake_redis)):
                yield


def test_get_redis_connection(mock_queue):
    """Test getting Redis connection."""
    from hoistscraper.queue import get_redis_connection
    
    conn = get_redis_connection()
    assert conn is not None


def test_get_queue_default(mock_queue):
    """Test getting default queue."""
    from hoistscraper.queue import get_queue
    
    queue = get_queue()
    assert isinstance(queue, Queue)
    assert queue.name == 'default'


def test_get_queue_scraper(mock_queue):
    """Test getting scraper queue."""
    from hoistscraper.queue import get_queue
    
    queue = get_queue('scraper')
    assert isinstance(queue, Queue)
    assert queue.name == 'scraper'


def test_enqueue_job(mock_queue, fake_redis):
    """Test enqueuing a job."""
    from hoistscraper.queue import enqueue_job
    
    # Use a built-in function that can be serialized
    test_func = sum
    
    with patch('hoistscraper.queue.redis_conn', fake_redis):
        job = enqueue_job(test_func, [1, 2], queue_name='scraper')
        assert isinstance(job, Job)
        assert job.func == test_func
        assert job.args == ([1, 2],)


def test_get_job_status_exists():
    """Test getting status of existing job."""
    from hoistscraper.queue import get_job_status
    
    # Create a mock job
    mock_job = Mock(spec=Job)
    mock_job.id = 'test-job-123'
    mock_job.get_status.return_value = 'queued'
    mock_job.created_at = '2024-01-01T00:00:00'
    mock_job.started_at = None
    mock_job.ended_at = None
    mock_job.result = None
    mock_job.exc_info = None
    mock_job.meta = {}
    
    with patch('hoistscraper.queue.Job.fetch', return_value=mock_job):
        status = get_job_status('test-job-123')
        
        assert status is not None
        assert status['id'] == 'test-job-123'
        assert status['status'] == 'queued'
        assert status['created_at'] == '2024-01-01T00:00:00'


def test_get_job_status_not_exists():
    """Test getting status of non-existent job."""
    from hoistscraper.queue import get_job_status
    
    with patch('hoistscraper.queue.Job.fetch', return_value=None):
        status = get_job_status('non-existent-job')
        assert status is None


def test_cancel_job_success():
    """Test successfully cancelling a job."""
    from hoistscraper.queue import cancel_job
    
    # Create a mock job
    mock_job = Mock(spec=Job)
    mock_job.cancel = Mock()
    
    with patch('hoistscraper.queue.Job.fetch', return_value=mock_job):
        result = cancel_job('test-job-123')
        
        assert result is True
        mock_job.cancel.assert_called_once()


def test_cancel_job_failure():
    """Test failing to cancel a job."""
    from hoistscraper.queue import cancel_job
    
    # Mock Job.fetch to raise an exception
    with patch('hoistscraper.queue.Job.fetch', side_effect=Exception("Job not found")):
        result = cancel_job('non-existent-job')
        assert result is False