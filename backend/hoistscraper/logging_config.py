"""
Centralized logging configuration for HoistScraper.

This module provides a consistent logging setup across all components
with proper formatting, log levels, and sensitive data masking.
"""

import logging
import logging.handlers
import sys
import json
import re
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import os


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in log messages."""
    
    # Patterns for sensitive data
    PATTERNS = [
        # Passwords in URLs
        (r'(postgresql://[^:]+:)([^@]+)(@)', r'\1[MASKED]\3'),
        (r'(redis://[^:]+:)([^@]+)(@)', r'\1[MASKED]\3'),
        
        # API keys and tokens
        (r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1[MASKED]\3'),
        (r'(token["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1[MASKED]\3'),
        (r'(Bearer\s+)([^\s]+)', r'\1[MASKED]'),
        
        # Credentials
        (r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1[MASKED]\3'),
        (r'(secret["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1[MASKED]\3'),
        (r'(passphrase["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1[MASKED]\3'),
        
        # Email addresses (optional - uncomment if needed)
        # (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'[EMAIL_MASKED]@\2'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and mask sensitive data in log records."""
        # Mask message
        if hasattr(record, 'msg'):
            record.msg = self._mask_sensitive_data(str(record.msg))
        
        # Mask args
        if hasattr(record, 'args') and record.args:
            record.args = tuple(
                self._mask_sensitive_data(str(arg)) for arg in record.args
            )
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Apply all masking patterns to text."""
        for pattern, replacement in self.PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': os.getpid(),
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_obj['correlation_id'] = record.correlation_id
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for development console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Format timestamp
        record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return super().format(record)


def setup_logging(
    app_name: str = "hoistscraper",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    use_json: bool = False,
    enable_colors: bool = True,
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        app_name: Name of the application/component
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        use_json: Use JSON formatting (for production)
        enable_colors: Enable colored output (for development)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.addFilter(sensitive_filter)
    
    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        if enable_colors and sys.stdout.isatty():
            format_str = '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s'
            console_handler.setFormatter(ColoredFormatter(format_str))
        else:
            format_str = '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s'
            console_handler.setFormatter(logging.Formatter(format_str))
    
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.addFilter(sensitive_filter)
        
        if use_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            format_str = '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s'
            file_handler.setFormatter(logging.Formatter(format_str))
        
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # Set application loggers to appropriate levels
    logging.getLogger(f'{app_name}').setLevel(log_level)
    
    # Log initial setup
    logger = logging.getLogger(f'{app_name}.logging_config')
    logger.info(
        f"Logging configured for {app_name}",
        extra={'extra_fields': {
            'log_level': log_level,
            'log_file': log_file,
            'use_json': use_json,
            'pid': os.getpid()
        }}
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs) -> None:
    """
    Log performance metrics in a standardized format.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration: Duration in seconds
        **kwargs: Additional metrics to log
    """
    metrics = {
        'operation': operation,
        'duration_seconds': round(duration, 3),
        'duration_ms': round(duration * 1000, 1),
    }
    metrics.update(kwargs)
    
    logger.info(
        f"Performance metric: {operation} completed in {metrics['duration_ms']}ms",
        extra={'extra_fields': {'performance_metrics': metrics}}
    )


def log_security_event(logger: logging.Logger, event_type: str, **kwargs) -> None:
    """
    Log security-related events in a standardized format.
    
    Args:
        logger: Logger instance
        event_type: Type of security event
        **kwargs: Event details
    """
    event = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
    }
    event.update(kwargs)
    
    logger.warning(
        f"Security event: {event_type}",
        extra={'extra_fields': {'security_event': event}}
    )


# Environment-based configuration
def setup_from_env(app_name: str = "hoistscraper") -> None:
    """Set up logging based on environment variables."""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE')
    use_json = os.getenv('LOG_FORMAT', '').lower() == 'json'
    enable_colors = os.getenv('LOG_COLORS', 'true').lower() == 'true'
    
    # In production, default to JSON and no colors
    if os.getenv('ENVIRONMENT', '').lower() == 'production':
        use_json = True
        enable_colors = False
    
    setup_logging(
        app_name=app_name,
        log_level=log_level,
        log_file=log_file,
        use_json=use_json,
        enable_colors=enable_colors
    )