"""
Production monitoring configuration for HoistScraper.
Includes Sentry integration, Prometheus metrics, and health checks.
"""

import os
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable

from loguru import logger
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


# Prometheus Metrics
scrape_jobs_total = Counter(
    'hoistscraper_scrape_jobs_total',
    'Total number of scrape jobs created',
    ['website_id', 'status']
)

scrape_job_duration_seconds = Histogram(
    'hoistscraper_scrape_job_duration_seconds',
    'Duration of scrape jobs in seconds',
    ['website_id', 'status']
)

opportunities_extracted_total = Counter(
    'hoistscraper_opportunities_extracted_total',
    'Total number of opportunities extracted',
    ['website_id']
)

active_scrape_jobs = Gauge(
    'hoistscraper_active_scrape_jobs',
    'Number of currently active scrape jobs'
)

websites_total = Gauge(
    'hoistscraper_websites_total',
    'Total number of websites in the system',
    ['status']
)

api_requests_total = Counter(
    'hoistscraper_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'hoistscraper_api_request_duration_seconds',
    'Duration of API requests in seconds',
    ['method', 'endpoint']
)

worker_health_status = Gauge(
    'hoistscraper_worker_health_status',
    'Health status of the worker (1=healthy, 0=unhealthy)'
)

database_connections_active = Gauge(
    'hoistscraper_database_connections_active',
    'Number of active database connections'
)

ollama_model_loaded = Gauge(
    'hoistscraper_ollama_model_loaded',
    'Whether Ollama model is loaded (1=loaded, 0=not loaded)'
)


def init_sentry(app=None):
    """Initialize Sentry error tracking."""
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured, Sentry monitoring disabled")
        return
    
    environment = os.getenv('ENVIRONMENT', 'production')
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        environment=environment,
        before_send=before_send_filter,
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable information
    )
    
    logger.info(f"Sentry initialized for environment: {environment}")


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter sensitive data before sending to Sentry."""
    # Filter out password fields
    if 'request' in event and 'data' in event['request']:
        data = event['request']['data']
        if isinstance(data, dict):
            # Remove sensitive fields
            sensitive_fields = ['password', 'api_key', 'secret', 'token', 'credential']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '[FILTERED]'
    
    # Filter out sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        if isinstance(headers, dict):
            sensitive_headers = ['authorization', 'x-api-key', 'cookie']
            for header in sensitive_headers:
                if header.lower() in {k.lower() for k in headers}:
                    headers[header] = '[FILTERED]'
    
    return event


def track_api_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track API request metrics."""
    api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_scrape_job_metrics(website_id: int, status: str, duration: Optional[float] = None):
    """Track scrape job metrics."""
    scrape_jobs_total.labels(website_id=str(website_id), status=status).inc()
    if duration is not None:
        scrape_job_duration_seconds.labels(website_id=str(website_id), status=status).observe(duration)


def track_opportunities_metrics(website_id: int, count: int):
    """Track opportunities extraction metrics."""
    opportunities_extracted_total.labels(website_id=str(website_id)).inc(count)


def update_active_jobs(count: int):
    """Update active scrape jobs gauge."""
    active_scrape_jobs.set(count)


def update_websites_metrics(active_count: int, inactive_count: int):
    """Update website metrics."""
    websites_total.labels(status='active').set(active_count)
    websites_total.labels(status='inactive').set(inactive_count)


def update_worker_health(is_healthy: bool):
    """Update worker health status."""
    worker_health_status.set(1 if is_healthy else 0)


def update_database_connections(count: int):
    """Update database connection metrics."""
    database_connections_active.set(count)


def update_ollama_status(is_loaded: bool):
    """Update Ollama model status."""
    ollama_model_loaded.set(1 if is_loaded else 0)


def get_metrics() -> Response:
    """Generate Prometheus metrics response."""
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


def monitor_performance(name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"{name or func.__name__} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{name or func.__name__} failed after {duration:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator


class HealthCheck:
    """Health check implementation for various services."""
    
    @staticmethod
    def check_database(engine) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            from sqlmodel import Session, text
            with Session(engine) as session:
                result = session.exec(text("SELECT 1")).first()
                return {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    @staticmethod
    def check_redis(redis_client) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            redis_client.ping()
            return {"status": "healthy", "message": "Redis connection OK"}
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    @staticmethod
    def check_ollama(ollama_host: str) -> Dict[str, Any]:
        """Check Ollama service availability."""
        try:
            import httpx
            response = httpx.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                return {
                    "status": "healthy",
                    "message": "Ollama service OK",
                    "models": model_names
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Ollama returned status {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    @staticmethod
    def check_worker_queue(redis_client) -> Dict[str, Any]:
        """Check worker queue status."""
        try:
            from rq import Queue
            queue = Queue(connection=redis_client)
            
            return {
                "status": "healthy",
                "message": "Worker queue operational",
                "stats": {
                    "queued_jobs": len(queue),
                    "failed_jobs": queue.failed_job_registry.count,
                    "workers": queue.count
                }
            }
        except Exception as e:
            logger.error(f"Worker queue health check failed: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}