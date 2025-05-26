"""Configuration handling for site crawlers."""

import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class PaginationConfig:
    """Configuration for pagination handling."""
    selector: str
    limit: int = 10


@dataclass
class AuthConfig:
    """Configuration for authentication."""
    type: str  # 'login_form', 'basic_auth', 'api_key', etc.
    username_env: Optional[str] = None
    password_env: Optional[str] = None
    login_url: Optional[str] = None
    selectors: Optional[Dict[str, str]] = None
    
    @property
    def username(self) -> Optional[str]:
        """Get username from environment variable."""
        return os.getenv(self.username_env) if self.username_env else None
    
    @property
    def password(self) -> Optional[str]:
        """Get password from environment variable."""
        return os.getenv(self.password_env) if self.password_env else None


@dataclass
class SiteConfig:
    """Configuration for a specific site crawler."""
    name: str
    start_urls: List[str]
    pagination: Optional[PaginationConfig] = None
    auth: Optional[AuthConfig] = None
    selectors: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    delay: float = 1.0
    timeout: int = 30
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SiteConfig':
        """Create SiteConfig from dictionary."""
        pagination = None
        if 'pagination' in data:
            pagination = PaginationConfig(**data['pagination'])
        
        auth = None
        if 'auth' in data:
            auth = AuthConfig(**data['auth'])
        
        return cls(
            name=data['name'],
            start_urls=data['start_urls'],
            pagination=pagination,
            auth=auth,
            selectors=data.get('selectors'),
            headers=data.get('headers'),
            delay=data.get('delay', 1.0),
            timeout=data.get('timeout', 30)
        )


class ConfigLoader:
    """Loader for site crawler configurations."""
    
    @staticmethod
    def load_from_yaml(file_path: str) -> List[SiteConfig]:
        """Load site configurations from YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if isinstance(data, list):
            return [SiteConfig.from_dict(site) for site in data]
        else:
            return [SiteConfig.from_dict(data)]
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> SiteConfig:
        """Load site configuration from dictionary."""
        return SiteConfig.from_dict(data)


# Example configuration for testing
EXAMPLE_CONFIG = {
    "name": "Example",
    "start_urls": ["https://foo.bar/grants"],
    "pagination": {
        "selector": "a[rel=next]",
        "limit": 10
    },
    "auth": {
        "type": "login_form",
        "username_env": "EX_USER",
        "password_env": "EX_PASS",
        "login_url": "https://foo.bar/login",
        "selectors": {
            "user": "#u",
            "pass": "#p",
            "submit": "button[type=submit]"
        }
    }
} 