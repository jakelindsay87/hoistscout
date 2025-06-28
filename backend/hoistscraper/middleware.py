"""
Middleware for request/response logging and monitoring.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import get_logger, log_performance

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details."""
        # Generate correlation ID for request tracking
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Skip logging for health checks to reduce noise
        if request.url.path in ["/health", "/api/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"API Request: {request.method} {request.url.path}",
            extra={'extra_fields': {
                'correlation_id': correlation_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'client_host': request.client.host if request.client else None,
            }}
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"API Response: {request.method} {request.url.path} - {response.status_code}",
                extra={'extra_fields': {
                    'correlation_id': correlation_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_seconds': round(duration, 3),
                }}
            )
            
            # Log performance metrics
            log_performance(
                logger,
                "api_request",
                duration,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                correlation_id=correlation_id
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"API Error: {request.method} {request.url.path} - {type(e).__name__}",
                exc_info=True,
                extra={'extra_fields': {
                    'correlation_id': correlation_id,
                    'method': request.method,
                    'path': request.url.path,
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'duration_seconds': round(duration, 3),
                }}
            )
            
            # Re-raise the exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.window_start = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if we need to reset the window
        current_time = time.time()
        if current_time - self.window_start > 60:
            self.request_counts = {}
            self.window_start = current_time
        
        # Check rate limit
        request_count = self.request_counts.get(client_ip, 0)
        if request_count >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={'extra_fields': {
                    'client_ip': client_ip,
                    'request_count': request_count,
                    'limit': self.requests_per_minute,
                }}
            )
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        # Increment request count
        self.request_counts[client_ip] = request_count + 1
        
        # Process request
        return await call_next(request)