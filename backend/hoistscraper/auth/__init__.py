"""Authentication and credential management module."""

from .credential_manager import (
    credential_manager,
    store_website_credential,
    get_website_credentials
)

__all__ = [
    "credential_manager",
    "store_website_credential", 
    "get_website_credentials"
]