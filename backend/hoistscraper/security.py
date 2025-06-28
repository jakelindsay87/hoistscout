"""Security middleware and utilities for HoistScraper."""
import os
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
import hashlib
import hmac

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Get API key from environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
ADMIN_API_KEY_HASH = os.getenv("ADMIN_API_KEY_HASH")  # For storing hashed keys

def verify_api_key(provided_key: str) -> bool:
    """Verify API key against environment variable."""
    if not ADMIN_API_KEY and not ADMIN_API_KEY_HASH:
        return False
    
    if ADMIN_API_KEY:
        # Direct comparison (less secure but simpler for now)
        return provided_key == ADMIN_API_KEY
    
    if ADMIN_API_KEY_HASH:
        # Compare hashed version
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        return hmac.compare_digest(provided_hash, ADMIN_API_KEY_HASH)
    
    return False

async def require_admin_auth(api_key: Optional[str] = None) -> str:
    """Require admin authentication for sensitive endpoints."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return api_key

async def block_in_production(request: Request):
    """Block access to debug endpoints in production."""
    # Check if we're in production (Render sets this)
    if os.getenv("RENDER") == "true" or os.getenv("NODE_ENV") == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )

def add_security_headers(response):
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Basic CSP - adjust based on your needs
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://hoistscraper.onrender.com"
    )
    
    return response

async def security_middleware(request: Request, call_next):
    """Security middleware to add headers and protect endpoints."""
    # Block debug endpoints in production
    if request.url.path.startswith("/api/debug") and os.getenv("RENDER") == "true":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Not found"}
        )
    
    # Require auth for admin endpoints
    if request.url.path.startswith("/api/admin"):
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if not api_key or not verify_api_key(api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Admin authentication required"},
                headers={"WWW-Authenticate": "ApiKey"}
            )
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    return add_security_headers(response)