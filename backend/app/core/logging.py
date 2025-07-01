"""
Advanced structured logging infrastructure with correlation tracking for production-grade observability.
"""
import structlog
import sentry_sdk
from contextvars import ContextVar
from typing import Any, Dict, Optional
import time
import uuid
import psutil
import json
from datetime import datetime
from pathlib import Path
import asyncio
from functools import wraps

# Context variables for request correlation
correlation_id_var = ContextVar('correlation_id', default=None)
job_id_var = ContextVar('job_id', default=None)
website_id_var = ContextVar('website_id', default=None)
user_id_var = ContextVar('user_id', default=None)

class ProductionLogger:
    """Enterprise-grade structured logging with comprehensive tracking."""
    
    def __init__(self, service_name: str = "hoistscout"):
        self.service_name = service_name
        self.logger = None
        self._configure_structured_logging()
        self._configure_sentry()
        
    def _configure_structured_logging(self):
        """Configure structlog with all necessary processors."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                self._add_service_context,
                self._add_performance_metrics,
                self._add_correlation_ids,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        self.logger = structlog.get_logger()
    
    def _configure_sentry(self):
        """Configure Sentry for error tracking."""
        sentry_dsn = os.environ.get("SENTRY_DSN")
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=os.environ.get("ENVIRONMENT", "development")
            )
    
    def _add_service_context(self, _, __, event_dict):
        """Add service-specific context to all logs."""
        event_dict["service"] = self.service_name
        event_dict["environment"] = os.environ.get("ENVIRONMENT", "development")
        event_dict["version"] = os.environ.get("APP_VERSION", "unknown")
        return event_dict
    
    def _add_performance_metrics(self, _, __, event_dict):
        """Add system performance metrics to logs."""
        try:
            process = psutil.Process()
            event_dict["performance"] = {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(interval=0.1),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
            }
        except Exception:
            pass
        return event_dict
    
    def _add_correlation_ids(self, _, __, event_dict):
        """Add correlation IDs for request tracking."""
        if correlation_id := correlation_id_var.get():
            event_dict["correlation_id"] = correlation_id
        if job_id := job_id_var.get():
            event_dict["job_id"] = job_id
        if website_id := website_id_var.get():
            event_dict["website_id"] = website_id
        if user_id := user_id_var.get():
            event_dict["user_id"] = user_id
        return event_dict
    
    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Set correlation ID for request tracking."""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        return correlation_id
    
    def set_job_context(self, job_id: str, website_id: str, user_id: Optional[str] = None):
        """Set job-specific context variables."""
        job_id_var.set(job_id)
        website_id_var.set(website_id)
        if user_id:
            user_id_var.set(user_id)
    
    def get_logger(self, component: str):
        """Get a logger bound to a specific component."""
        return self.logger.bind(component=component)


class ScrapingLogger:
    """Specialized logger for scraping operations with detailed tracking."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("scraper")
        self.metrics = {}
    
    def log_page_load(self, url: str, load_time: float, status: str, page_size: int):
        """Log page load events with performance metrics."""
        self.logger.info(
            "page_loaded",
            url=url,
            load_time_ms=load_time * 1000,
            status=status,
            page_size_kb=page_size / 1024,
            event_type="page_load"
        )
    
    def log_element_detection(self, selector: str, found: bool, count: int = 0):
        """Log element detection attempts."""
        self.logger.debug(
            "element_detection",
            selector=selector,
            found=found,
            element_count=count,
            event_type="element_detection"
        )
    
    def log_anti_detection_event(self, technique: str, success: bool, details: Dict[str, Any]):
        """Log anti-detection technique usage."""
        self.logger.info(
            "anti_detection",
            technique=technique,
            success=success,
            details=details,
            event_type="anti_detection"
        )
    
    def log_extraction_result(self, page_number: int, opportunities_found: int, 
                            extraction_time: float, errors: list):
        """Log extraction results for a page."""
        self.logger.info(
            "extraction_complete",
            page_number=page_number,
            opportunities_found=opportunities_found,
            extraction_time_ms=extraction_time * 1000,
            error_count=len(errors),
            errors=errors[:5] if errors else [],  # Limit error details
            event_type="extraction"
        )


class PaginationLogger:
    """Specialized logger for pagination handling."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("pagination")
    
    def log_pagination_detection(self, url: str, pagination_type: str, 
                               indicators_found: Dict[str, Any]):
        """Log pagination type detection."""
        self.logger.info(
            "pagination_detected",
            url=url,
            pagination_type=pagination_type,
            indicators=indicators_found,
            event_type="pagination_detection"
        )
    
    def log_page_navigation(self, from_page: int, to_page: int, 
                          navigation_method: str, success: bool):
        """Log page navigation attempts."""
        self.logger.info(
            "page_navigation",
            from_page=from_page,
            to_page=to_page,
            method=navigation_method,
            success=success,
            event_type="page_navigation"
        )
    
    def log_pagination_complete(self, total_pages: int, total_items: int, 
                              total_time: float):
        """Log pagination completion statistics."""
        self.logger.info(
            "pagination_complete",
            total_pages=total_pages,
            total_items=total_items,
            total_time_seconds=total_time,
            avg_items_per_page=total_items / total_pages if total_pages > 0 else 0,
            event_type="pagination_summary"
        )


class CredentialLogger:
    """Specialized logger for credential management with security considerations."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("credentials")
    
    def log_credential_storage(self, website_id: str, credential_types: list):
        """Log credential storage (without sensitive data)."""
        self.logger.info(
            "credentials_stored",
            website_id=website_id,
            credential_types=credential_types,
            event_type="credential_storage"
        )
    
    def log_authentication_attempt(self, website_id: str, auth_type: str):
        """Log authentication attempt."""
        self.logger.info(
            "authentication_attempt",
            website_id=website_id,
            auth_type=auth_type,
            event_type="auth_start"
        )
    
    def log_authentication_result(self, website_id: str, success: bool, 
                                auth_type: str, error: Optional[str] = None):
        """Log authentication result."""
        log_level = "info" if success else "error"
        getattr(self.logger, log_level)(
            "authentication_result",
            website_id=website_id,
            success=success,
            auth_type=auth_type,
            error=error,
            event_type="auth_result"
        )


class PDFLogger:
    """Specialized logger for PDF processing operations."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("pdf_processor")
    
    def log_pdf_download(self, url: str, size_bytes: int, download_time: float):
        """Log PDF download events."""
        self.logger.info(
            "pdf_downloaded",
            url=url,
            size_mb=size_bytes / 1024 / 1024,
            download_time_seconds=download_time,
            event_type="pdf_download"
        )
    
    def log_ocr_processing(self, filename: str, pages: int, processing_time: float,
                         text_length: int):
        """Log OCR processing results."""
        self.logger.info(
            "ocr_complete",
            filename=filename,
            pages=pages,
            processing_time_seconds=processing_time,
            text_length=text_length,
            pages_per_second=pages / processing_time if processing_time > 0 else 0,
            event_type="ocr_processing"
        )
    
    def log_llm_inference(self, model: str, prompt_tokens: int, 
                        completion_tokens: int, inference_time: float):
        """Log LLM inference metrics."""
        self.logger.info(
            "llm_inference",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            inference_time_seconds=inference_time,
            tokens_per_second=(prompt_tokens + completion_tokens) / inference_time if inference_time > 0 else 0,
            event_type="llm_inference"
        )


class DatabaseLogger:
    """Specialized logger for database operations."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("database")
    
    def log_query_performance(self, query_type: str, table: str, 
                            execution_time: float, rows_affected: int):
        """Log database query performance."""
        self.logger.debug(
            "query_executed",
            query_type=query_type,
            table=table,
            execution_time_ms=execution_time * 1000,
            rows_affected=rows_affected,
            event_type="db_query"
        )
    
    def log_connection_pool_stats(self, active: int, idle: int, total: int):
        """Log connection pool statistics."""
        self.logger.debug(
            "connection_pool",
            active_connections=active,
            idle_connections=idle,
            total_connections=total,
            utilization_percent=(active / total * 100) if total > 0 else 0,
            event_type="db_pool"
        )


class APILogger:
    """Specialized logger for API operations."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("api")
    
    def log_request(self, method: str, path: str, user_id: Optional[str] = None):
        """Log incoming API request."""
        self.logger.info(
            "api_request",
            method=method,
            path=path,
            user_id=user_id,
            event_type="api_request_start"
        )
    
    def log_response(self, method: str, path: str, status_code: int, 
                   response_time: float):
        """Log API response."""
        log_level = "info" if status_code < 400 else "error"
        getattr(self.logger, log_level)(
            "api_response",
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=response_time * 1000,
            event_type="api_request_complete"
        )
    
    def log_rate_limit(self, user_id: str, endpoint: str, 
                     requests_made: int, limit: int):
        """Log rate limiting events."""
        self.logger.warning(
            "rate_limit_exceeded",
            user_id=user_id,
            endpoint=endpoint,
            requests_made=requests_made,
            limit=limit,
            event_type="rate_limit"
        )


class JobLogger:
    """Specialized logger for background job processing."""
    
    def __init__(self, base_logger: ProductionLogger):
        self.base_logger = base_logger
        self.logger = base_logger.get_logger("worker")
    
    def log_job_start(self, job_id: str, job_type: str, priority: str):
        """Log job start event."""
        self.logger.info(
            "job_started",
            job_id=job_id,
            job_type=job_type,
            priority=priority,
            event_type="job_start"
        )
    
    def log_job_progress(self, job_id: str, current: int, total: int, 
                       stage: str):
        """Log job progress update."""
        self.logger.info(
            "job_progress",
            job_id=job_id,
            current=current,
            total=total,
            percentage=round((current / total * 100) if total > 0 else 0, 2),
            stage=stage,
            event_type="job_progress"
        )
    
    def log_job_complete(self, job_id: str, status: str, duration: float,
                       results: Dict[str, Any]):
        """Log job completion."""
        log_level = "info" if status == "completed" else "error"
        getattr(self.logger, log_level)(
            "job_complete",
            job_id=job_id,
            status=status,
            duration_seconds=duration,
            results=results,
            event_type="job_complete"
        )


# Initialize global logger instances
import os
production_logger = ProductionLogger()
scraping_logger = ScrapingLogger(production_logger)
pagination_logger = PaginationLogger(production_logger)
credential_logger = CredentialLogger(production_logger)
pdf_logger = PDFLogger(production_logger)
database_logger = DatabaseLogger(production_logger)
api_logger = APILogger(production_logger)
job_logger = JobLogger(production_logger)


# Decorator for automatic performance logging
def log_performance(component: str):
    """Decorator to automatically log function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = production_logger.get_logger(component)
            
            try:
                logger.debug(f"{func.__name__}_start")
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{func.__name__}_complete",
                    duration_seconds=duration,
                    success=True
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__}_failed",
                    duration_seconds=duration,
                    error=str(e),
                    success=False
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = production_logger.get_logger(component)
            
            try:
                logger.debug(f"{func.__name__}_start")
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{func.__name__}_complete",
                    duration_seconds=duration,
                    success=True
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__}_failed",
                    duration_seconds=duration,
                    error=str(e),
                    success=False
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator