"""
Tests for logging configuration and functionality.
"""

import pytest
import logging
import json
import os
from io import StringIO
from unittest.mock import patch, Mock
from datetime import datetime

from hoistscraper.logging_config import (
    setup_logging,
    get_logger,
    log_performance,
    log_security_event,
    SensitiveDataFilter,
    StructuredFormatter,
    ColoredFormatter,
    setup_from_env
)


class TestLoggingSetup:
    """Test logging configuration setup."""
    
    def test_basic_logging_setup(self):
        """Test basic logging setup."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging(
            app_name="test-app",
            log_level="INFO",
            use_json=False,
            enable_colors=False
        )
        
        logger = get_logger("test.module")
        
        # Test logging works
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Test message")
            output = mock_stdout.getvalue()
            
            assert "Test message" in output
            assert "INFO" in output
            assert "test.module" in output
    
    def test_json_logging_setup(self):
        """Test JSON logging setup."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging(
            app_name="test-app",
            log_level="DEBUG",
            use_json=True
        )
        
        logger = get_logger("test.json")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("JSON test message")
            output = mock_stdout.getvalue().strip()
            
            # Should be valid JSON
            log_entry = json.loads(output)
            assert log_entry["message"] == "JSON test message"
            assert log_entry["level"] == "INFO"
            assert log_entry["logger"] == "test.json"
            assert "timestamp" in log_entry
    
    def test_file_logging_setup(self, tmp_path):
        """Test file logging setup."""
        log_file = tmp_path / "test.log"
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging(
            app_name="test-app",
            log_level="DEBUG",
            log_file=str(log_file),
            use_json=False
        )
        
        logger = get_logger("test.file")
        logger.info("File test message")
        
        # Check file was created and contains log
        assert log_file.exists()
        content = log_file.read_text()
        assert "File test message" in content
        assert "INFO" in content
    
    def test_setup_from_env(self):
        """Test setting up logging from environment variables."""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FORMAT': 'json',
            'LOG_COLORS': 'false',
            'ENVIRONMENT': 'production'
        }):
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            
            setup_from_env("test-app")
            
            # Verify production settings
            logger = get_logger("test.env")
            
            # In production, should use JSON format
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                logger.debug("Env test message")
                output = mock_stdout.getvalue().strip()
                
                # Should be JSON in production
                log_entry = json.loads(output)
                assert log_entry["level"] == "DEBUG"


class TestSensitiveDataFilter:
    """Test sensitive data filtering in logs."""
    
    def test_password_masking(self):
        """Test that passwords are masked."""
        filter = SensitiveDataFilter()
        
        test_cases = [
            # Database URLs
            ("postgresql://user:mypassword@localhost/db", 
             "postgresql://user:[MASKED]@localhost/db"),
            ("redis://admin:secret123@redis:6379", 
             "redis://admin:[MASKED]@redis:6379"),
            
            # API keys
            ("api_key=abc123xyz", "api_key=[MASKED]"),
            ("API-KEY: def456uvw", "API-KEY: [MASKED]"),
            ('api_key": "sensitive', 'api_key": "[MASKED]'),
            
            # Passwords
            ("password=topsecret", "password=[MASKED]"),
            ('password": "mysecret"', 'password": "[MASKED]"'),
            ("PASSWORD='classified'", "PASSWORD='[MASKED]'"),
            
            # Bearer tokens
            ("Authorization: Bearer eyJhbGc123", "Authorization: Bearer [MASKED]"),
            
            # Secrets
            ("secret=confidential", "secret=[MASKED]"),
            ("client_secret='xyz789'", "client_secret='[MASKED]'"),
        ]
        
        for input_text, expected in test_cases:
            result = filter._mask_sensitive_data(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_filter_log_record(self):
        """Test filtering of log records."""
        filter = SensitiveDataFilter()
        
        # Create a log record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Connecting with password=secret123",
            args=("api_key=xyz789",),
            exc_info=None
        )
        
        # Apply filter
        filter.filter(record)
        
        assert record.msg == "Connecting with password=[MASKED]"
        assert record.args == ("api_key=[MASKED]",)
    
    def test_complex_masking(self):
        """Test masking in complex scenarios."""
        filter = SensitiveDataFilter()
        
        # Multiple sensitive items in one string
        text = "DB: postgresql://admin:pass123@db:5432, API: key=abc, token=xyz"
        result = filter._mask_sensitive_data(text)
        
        assert "pass123" not in result
        assert "[MASKED]" in result
        assert result.count("[MASKED]") >= 2  # At least password and token


class TestStructuredFormatter:
    """Test structured JSON log formatting."""
    
    def test_basic_formatting(self):
        """Test basic JSON log formatting."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.module"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
        assert "process_id" in log_data
    
    def test_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.correlation_id = "abc-123"
        record.extra_fields = {
            "user_id": 42,
            "action": "login"
        }
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert log_data["correlation_id"] == "abc-123"
        assert log_data["user_id"] == 42
        assert log_data["action"] == "login"
    
    def test_exception_formatting(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        log_data = json.loads(output)
        
        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]


class TestColoredFormatter:
    """Test colored console log formatting."""
    
    def test_color_formatting(self):
        """Test that colors are applied correctly."""
        formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Test different log levels
        levels = {
            logging.DEBUG: '\033[36m',    # Cyan
            logging.INFO: '\033[32m',     # Green
            logging.WARNING: '\033[33m',  # Yellow
            logging.ERROR: '\033[31m',    # Red
            logging.CRITICAL: '\033[35m', # Magenta
        }
        
        for level, color in levels.items():
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            output = formatter.format(record)
            assert color in output
            assert '\033[0m' in output  # Reset code


class TestUtilityFunctions:
    """Test logging utility functions."""
    
    def test_log_performance(self):
        """Test performance logging."""
        logger = get_logger("test.perf")
        
        with patch.object(logger, 'info') as mock_info:
            log_performance(
                logger,
                "database_query",
                1.234,
                query_type="select",
                rows_returned=100
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            
            # Check message
            assert "database_query completed in 1234.0ms" in call_args[0][0]
            
            # Check extra fields
            extra_fields = call_args[1]['extra']['extra_fields']['performance_metrics']
            assert extra_fields['operation'] == "database_query"
            assert extra_fields['duration_seconds'] == 1.234
            assert extra_fields['duration_ms'] == 1234.0
            assert extra_fields['query_type'] == "select"
            assert extra_fields['rows_returned'] == 100
    
    def test_log_security_event(self):
        """Test security event logging."""
        logger = get_logger("test.security")
        
        with patch.object(logger, 'warning') as mock_warning:
            log_security_event(
                logger,
                "unauthorized_access",
                user_ip="192.168.1.100",
                resource="/api/admin",
                reason="invalid_token"
            )
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args
            
            # Check message
            assert "Security event: unauthorized_access" in call_args[0][0]
            
            # Check extra fields
            security_event = call_args[1]['extra']['extra_fields']['security_event']
            assert security_event['event_type'] == "unauthorized_access"
            assert security_event['user_ip'] == "192.168.1.100"
            assert security_event['resource'] == "/api/admin"
            assert security_event['reason'] == "invalid_token"
            assert 'timestamp' in security_event


class TestLoggerConfiguration:
    """Test logger configuration and hierarchy."""
    
    def test_logger_hierarchy(self):
        """Test that logger hierarchy works correctly."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging("hoistscraper", log_level="INFO")
        
        # Parent logger
        parent_logger = get_logger("hoistscraper")
        parent_logger.setLevel(logging.INFO)
        
        # Child logger should inherit settings
        child_logger = get_logger("hoistscraper.worker")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # INFO should be logged
            child_logger.info("Info message")
            assert "Info message" in mock_stdout.getvalue()
            
            mock_stdout.truncate(0)
            
            # DEBUG should not be logged (level is INFO)
            child_logger.debug("Debug message")
            assert "Debug message" not in mock_stdout.getvalue()
    
    def test_third_party_logger_suppression(self):
        """Test that third-party loggers are suppressed."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging("test-app", log_level="DEBUG")
        
        # Third-party loggers should be set to WARNING
        urllib_logger = logging.getLogger("urllib3")
        assert urllib_logger.level == logging.WARNING
        
        selenium_logger = logging.getLogger("selenium")
        assert selenium_logger.level == logging.WARNING


class TestIntegration:
    """Integration tests for logging system."""
    
    def test_full_logging_flow(self, tmp_path):
        """Test complete logging flow with all features."""
        log_file = tmp_path / "test_integration.log"
        
        # Setup logging with all features
        setup_logging(
            app_name="integration-test",
            log_level="DEBUG",
            log_file=str(log_file),
            use_json=True,
            enable_colors=False
        )
        
        logger = get_logger("integration.test")
        
        # Log various events
        logger.info("Starting integration test")
        
        # Log with sensitive data
        logger.warning("Database connection: postgresql://user:password123@localhost/db")
        
        # Log performance
        log_performance(logger, "test_operation", 0.123, items_processed=50)
        
        # Log security event
        log_security_event(logger, "test_auth", success=True, user="testuser")
        
        # Log with exception
        try:
            raise RuntimeError("Test error")
        except RuntimeError:
            logger.error("Error in test", exc_info=True)
        
        # Verify file contents
        log_contents = log_file.read_text()
        log_lines = log_contents.strip().split('\n')
        
        # Should have 5 log entries
        assert len(log_lines) == 5
        
        # Each line should be valid JSON
        for line in log_lines:
            log_entry = json.loads(line)
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "message" in log_entry
        
        # Check sensitive data was masked
        assert "password123" not in log_contents
        assert "[MASKED]" in log_contents
        
        # Check performance metrics
        assert "test_operation" in log_contents
        assert "items_processed" in log_contents
        
        # Check security event
        assert "test_auth" in log_contents
        
        # Check exception was logged
        assert "RuntimeError" in log_contents