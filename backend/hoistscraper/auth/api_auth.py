"""Simple API key authentication for HoistScraper."""

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

# Security scheme
security = HTTPBearer(auto_error=False)

# Get API key from environment
API_KEY = os.getenv("API_KEY")
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() == "true"


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """
    Verify API key if authentication is enabled.
    
    Returns:
        Username/identifier if authenticated, None if auth not required
    
    Raises:
        HTTPException: If authentication fails
    """
    # Skip auth if not required
    if not REQUIRE_AUTH:
        return None
    
    # Check if API key is configured
    if not API_KEY:
        logger.error("Authentication required but API_KEY not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication not configured"
        )
    
    # Check if credentials provided
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify API key
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return "api_user"


# Optional dependency - use this for endpoints that should be protected
optional_api_key = Security(verify_api_key)


def get_api_key_header() -> dict:
    """Get authorization header for internal API calls."""
    if REQUIRE_AUTH and API_KEY:
        return {"Authorization": f"Bearer {API_KEY}"}
    return {}