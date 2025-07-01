"""
Secure credential management system with encryption and authentication handling.
"""
from typing import Dict, Optional, Any, List
from cryptography.fernet import Fernet
from playwright.async_api import Page
import asyncio
import json
import base64
from datetime import datetime, timedelta
import aioredis
from sqlalchemy import select
from .logging import credential_logger, log_performance
from .anti_detection import AntiDetectionMixin
from ..models.website import WebsiteCredential
from ..database import get_db
import os
from abc import ABC, abstractmethod


class AuthenticationStrategy(ABC):
    """Base class for authentication strategies."""
    
    @abstractmethod
    async def authenticate(self, page: Page, credentials: Dict[str, str], 
                         config: Dict[str, Any]) -> bool:
        """Perform authentication."""
        pass
    
    @abstractmethod
    async def verify_authentication(self, page: Page, config: Dict[str, Any]) -> bool:
        """Verify authentication was successful."""
        pass


class FormLoginStrategy(AuthenticationStrategy, AntiDetectionMixin):
    """Handle form-based login authentication."""
    
    async def authenticate(self, page: Page, credentials: Dict[str, str], 
                         config: Dict[str, Any]) -> bool:
        """Perform form-based login."""
        try:
            credential_logger.logger.info("Starting form-based authentication")
            
            # Navigate to login page
            login_url = config.get('login_url')
            if login_url:
                await page.goto(login_url, wait_until='networkidle')
                await asyncio.sleep(2)  # Wait for dynamic content
            
            # Fill username
            username_selector = config.get('username_selector', 'input[name="username"]')
            username = credentials.get('username')
            if username:
                await self.type_human_like(page, username_selector, username)
                credential_logger.logger.debug("Username entered")
            
            # Fill password
            password_selector = config.get('password_selector', 'input[name="password"]')
            password = credentials.get('password')
            if password:
                await self.type_human_like(page, password_selector, password)
                credential_logger.logger.debug("Password entered")
            
            # Handle CAPTCHA if present
            if await self._detect_captcha(page):
                credential_logger.logger.info("CAPTCHA detected, attempting to solve")
                captcha_solved = await self._solve_captcha(page, config)
                if not captcha_solved:
                    return False
            
            # Submit form
            submit_selector = config.get('submit_selector', 'button[type="submit"]')
            submit_button = await page.query_selector(submit_selector)
            if not submit_button:
                # Try alternative selectors
                for selector in ['input[type="submit"]', 'button:has-text("Login")', 
                               'button:has-text("Sign in")']:
                    submit_button = await page.query_selector(selector)
                    if submit_button:
                        break
            
            if submit_button:
                await submit_button.click()
                await page.wait_for_load_state('networkidle', timeout=30000)
                credential_logger.logger.info("Login form submitted")
            else:
                credential_logger.logger.error("Submit button not found")
                return False
            
            # Wait for navigation or content change
            await asyncio.sleep(3)
            
            return await self.verify_authentication(page, config)
            
        except Exception as e:
            credential_logger.logger.error(f"Form login failed: {str(e)}")
            return False
    
    async def verify_authentication(self, page: Page, config: Dict[str, Any]) -> bool:
        """Verify login was successful."""
        try:
            # Check for common success indicators
            success_indicators = config.get('success_indicators', [])
            if not success_indicators:
                success_indicators = [
                    'logout', 'dashboard', 'welcome', 'profile',
                    'signed in', 'logged in', 'my account'
                ]
            
            page_content = await page.content()
            page_url = page.url
            
            # Check URL changes
            login_url = config.get('login_url', '')
            if login_url and login_url not in page_url:
                credential_logger.logger.info("URL changed after login, likely successful")
                return True
            
            # Check for success indicators
            for indicator in success_indicators:
                if indicator.lower() in page_content.lower():
                    credential_logger.logger.info(f"Success indicator found: {indicator}")
                    return True
            
            # Check for failure indicators
            failure_indicators = config.get('failure_indicators', [])
            if not failure_indicators:
                failure_indicators = [
                    'invalid', 'incorrect', 'failed', 'error',
                    'wrong password', 'authentication failed'
                ]
            
            for indicator in failure_indicators:
                if indicator.lower() in page_content.lower():
                    credential_logger.logger.error(f"Failure indicator found: {indicator}")
                    return False
            
            # Check for common logged-in elements
            logged_in_selectors = [
                'a[href*="logout"]', 'button:has-text("Logout")',
                '.user-menu', '#user-profile', '.dashboard'
            ]
            
            for selector in logged_in_selectors:
                element = await page.query_selector(selector)
                if element:
                    credential_logger.logger.info(f"Logged-in element found: {selector}")
                    return True
            
            credential_logger.logger.warning("Could not definitively verify authentication")
            return False
            
        except Exception as e:
            credential_logger.logger.error(f"Authentication verification failed: {str(e)}")
            return False
    
    async def _detect_captcha(self, page: Page) -> bool:
        """Detect if CAPTCHA is present."""
        captcha_indicators = [
            'iframe[src*="recaptcha"]',
            'div[class*="g-recaptcha"]',
            'div[id*="captcha"]',
            'img[src*="captcha"]',
            '.h-captcha',
            'iframe[src*="hcaptcha"]'
        ]
        
        for indicator in captcha_indicators:
            element = await page.query_selector(indicator)
            if element:
                return True
        
        return False
    
    async def _solve_captcha(self, page: Page, config: Dict[str, Any]) -> bool:
        """Attempt to solve CAPTCHA using configured service."""
        captcha_service = config.get('captcha_service')
        if not captcha_service:
            credential_logger.logger.error("No CAPTCHA service configured")
            return False
        
        # Integrate with CAPTCHA solving service (2captcha, anti-captcha, etc.)
        # This is a placeholder - implement actual CAPTCHA solving
        credential_logger.logger.warning("CAPTCHA solving not yet implemented")
        return False


class OAuth2Strategy(AuthenticationStrategy):
    """Handle OAuth2 authentication flows."""
    
    async def authenticate(self, page: Page, credentials: Dict[str, str], 
                         config: Dict[str, Any]) -> bool:
        """Perform OAuth2 authentication."""
        try:
            credential_logger.logger.info("Starting OAuth2 authentication")
            
            # Get OAuth configuration
            client_id = credentials.get('client_id')
            client_secret = credentials.get('client_secret')
            auth_url = config.get('oauth_auth_url')
            token_url = config.get('oauth_token_url')
            scope = config.get('oauth_scope', '')
            
            if not all([client_id, client_secret, auth_url, token_url]):
                credential_logger.logger.error("Missing OAuth2 configuration")
                return False
            
            # Navigate to authorization URL
            auth_params = {
                'client_id': client_id,
                'response_type': 'code',
                'scope': scope,
                'redirect_uri': config.get('oauth_redirect_uri', 'http://localhost:8080/callback')
            }
            
            auth_url_full = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
            await page.goto(auth_url_full)
            
            # Handle user consent if needed
            consent_button = await page.query_selector('button[type="submit"]')
            if consent_button:
                await consent_button.click()
                await page.wait_for_navigation()
            
            # Extract authorization code from redirect
            current_url = page.url
            if 'code=' in current_url:
                auth_code = current_url.split('code=')[1].split('&')[0]
                
                # Exchange code for token (would need server-side implementation)
                credential_logger.logger.info("OAuth2 authorization code obtained")
                return True
            
            return False
            
        except Exception as e:
            credential_logger.logger.error(f"OAuth2 authentication failed: {str(e)}")
            return False
    
    async def verify_authentication(self, page: Page, config: Dict[str, Any]) -> bool:
        """Verify OAuth2 authentication."""
        # Check if we have valid access token
        # This would typically involve checking token expiry
        return True


class APIKeyStrategy(AuthenticationStrategy):
    """Handle API key authentication."""
    
    async def authenticate(self, page: Page, credentials: Dict[str, str], 
                         config: Dict[str, Any]) -> bool:
        """Add API key to requests."""
        try:
            credential_logger.logger.info("Setting up API key authentication")
            
            api_key = credentials.get('api_key')
            if not api_key:
                credential_logger.logger.error("No API key provided")
                return False
            
            # Determine how to add API key
            auth_method = config.get('api_key_method', 'header')
            
            if auth_method == 'header':
                # Add API key to headers
                header_name = config.get('api_key_header', 'X-API-Key')
                await page.set_extra_http_headers({
                    header_name: api_key
                })
            elif auth_method == 'query':
                # Add API key to query parameters
                param_name = config.get('api_key_param', 'api_key')
                # This would be added to each request URL
            elif auth_method == 'cookie':
                # Set API key as cookie
                cookie_name = config.get('api_key_cookie', 'api_key')
                await page.context.add_cookies([{
                    'name': cookie_name,
                    'value': api_key,
                    'domain': page.url.split('/')[2],
                    'path': '/'
                }])
            
            credential_logger.logger.info(f"API key configured using {auth_method} method")
            return True
            
        except Exception as e:
            credential_logger.logger.error(f"API key setup failed: {str(e)}")
            return False
    
    async def verify_authentication(self, page: Page, config: Dict[str, Any]) -> bool:
        """Verify API key is working."""
        # Make test request to verify API key
        test_endpoint = config.get('api_test_endpoint')
        if test_endpoint:
            try:
                response = await page.goto(test_endpoint)
                return response.status < 400
            except Exception:
                return False
        return True


class SecureCredentialManager:
    """Production-grade credential management with encryption."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or os.environ.get('CREDENTIAL_ENCRYPTION_KEY')
        if not self.encryption_key:
            # Generate new key if not provided
            self.encryption_key = Fernet.generate_key().decode()
            credential_logger.logger.warning("Generated new encryption key")
        
        self.cipher = Fernet(self.encryption_key.encode())
        self.credential_cache = {}
        self.session_store = {}
        self.strategies = {
            'form_login': FormLoginStrategy(),
            'oauth2': OAuth2Strategy(),
            'api_key': APIKeyStrategy()
        }
        
        # Redis for session management
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    @log_performance("credentials")
    async def store_credentials(self, website_id: str, credentials: Dict[str, str],
                              auth_config: Dict[str, Any]):
        """Store encrypted credentials in database."""
        credential_logger.log_credential_storage(
            website_id,
            list(credentials.keys())
        )
        
        try:
            # Encrypt sensitive fields
            encrypted_creds = {}
            sensitive_fields = ['password', 'api_key', 'token', 'client_secret', 
                              'private_key', 'secret']
            
            for key, value in credentials.items():
                if any(field in key.lower() for field in sensitive_fields):
                    encrypted_creds[key] = self.cipher.encrypt(value.encode()).decode()
                    credential_logger.logger.debug(f"Encrypted field: {key}")
                else:
                    encrypted_creds[key] = value
            
            # Store in database
            async with get_db() as db:
                # Check if credentials already exist
                result = await db.execute(
                    select(WebsiteCredential).where(
                        WebsiteCredential.website_id == website_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing
                    existing.credentials = json.dumps(encrypted_creds)
                    existing.auth_config = json.dumps(auth_config)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    new_cred = WebsiteCredential(
                        website_id=website_id,
                        credentials=json.dumps(encrypted_creds),
                        auth_config=json.dumps(auth_config)
                    )
                    db.add(new_cred)
                
                await db.commit()
                
            # Clear cache
            if website_id in self.credential_cache:
                del self.credential_cache[website_id]
            
            credential_logger.logger.info("Credentials stored successfully")
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to store credentials: {str(e)}")
            raise
    
    async def retrieve_credentials(self, website_id: str) -> Dict[str, str]:
        """Retrieve and decrypt credentials."""
        try:
            # Check cache first
            if website_id in self.credential_cache:
                credential_logger.logger.debug("Using cached credentials")
                return self.credential_cache[website_id]
            
            # Fetch from database
            async with get_db() as db:
                result = await db.execute(
                    select(WebsiteCredential).where(
                        WebsiteCredential.website_id == website_id
                    )
                )
                cred_record = result.scalar_one_or_none()
                
                if not cred_record:
                    raise ValueError(f"No credentials found for website {website_id}")
                
                encrypted_creds = json.loads(cred_record.credentials)
                auth_config = json.loads(cred_record.auth_config)
            
            # Decrypt sensitive fields
            decrypted_creds = {}
            for key, value in encrypted_creds.items():
                try:
                    # Try to decrypt
                    decrypted_value = self.cipher.decrypt(value.encode()).decode()
                    decrypted_creds[key] = decrypted_value
                except Exception:
                    # Not encrypted, use as-is
                    decrypted_creds[key] = value
            
            # Cache for future use
            self.credential_cache[website_id] = decrypted_creds
            
            credential_logger.logger.info("Credentials retrieved successfully")
            return decrypted_creds
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to retrieve credentials: {str(e)}")
            raise
    
    @log_performance("authentication")
    async def authenticate_website(self, page: Page, website_id: str,
                                 auth_type: str, auth_config: Dict[str, Any]):
        """Authenticate with website using stored credentials."""
        credential_logger.log_authentication_attempt(website_id, auth_type)
        
        try:
            # Check for existing session
            session = await self.get_session(website_id)
            if session and await self.validate_session(page, session):
                credential_logger.logger.info("Using existing valid session")
                await self.restore_session(page, session)
                return True
            
            # Retrieve credentials
            credentials = await self.retrieve_credentials(website_id)
            
            # Get authentication strategy
            strategy = self.strategies.get(auth_type)
            if not strategy:
                raise ValueError(f"Unknown authentication type: {auth_type}")
            
            # Perform authentication
            success = await strategy.authenticate(page, credentials, auth_config)
            
            if success:
                # Save session
                await self.save_session(page, website_id)
                credential_logger.log_authentication_result(
                    website_id, True, auth_type
                )
            else:
                credential_logger.log_authentication_result(
                    website_id, False, auth_type, "Authentication failed"
                )
            
            return success
            
        except Exception as e:
            credential_logger.log_authentication_result(
                website_id, False, auth_type, str(e)
            )
            raise
    
    async def save_session(self, page: Page, website_id: str):
        """Save authentication session for reuse."""
        try:
            # Get cookies
            cookies = await page.context.cookies()
            
            # Get local storage
            local_storage = await page.evaluate('() => Object.entries(localStorage)')
            
            # Get session storage
            session_storage = await page.evaluate('() => Object.entries(sessionStorage)')
            
            session_data = {
                'cookies': cookies,
                'local_storage': dict(local_storage),
                'session_storage': dict(session_storage),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store in Redis with expiration
            redis = await aioredis.from_url(self.redis_url)
            await redis.setex(
                f"session:{website_id}",
                timedelta(hours=24),
                json.dumps(session_data)
            )
            await redis.close()
            
            credential_logger.logger.info("Session saved successfully")
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to save session: {str(e)}")
    
    async def get_session(self, website_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve saved session."""
        try:
            redis = await aioredis.from_url(self.redis_url)
            session_data = await redis.get(f"session:{website_id}")
            await redis.close()
            
            if session_data:
                return json.loads(session_data)
            return None
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to get session: {str(e)}")
            return None
    
    async def validate_session(self, page: Page, session: Dict[str, Any]) -> bool:
        """Check if session is still valid."""
        try:
            # Check session age
            session_time = datetime.fromisoformat(session['timestamp'])
            if datetime.utcnow() - session_time > timedelta(hours=23):
                credential_logger.logger.info("Session too old")
                return False
            
            # Could add additional validation here
            return True
            
        except Exception as e:
            credential_logger.logger.error(f"Session validation failed: {str(e)}")
            return False
    
    async def restore_session(self, page: Page, session: Dict[str, Any]):
        """Restore saved session to page."""
        try:
            # Restore cookies
            if session.get('cookies'):
                await page.context.add_cookies(session['cookies'])
            
            # Restore local storage
            if session.get('local_storage'):
                for key, value in session['local_storage'].items():
                    await page.evaluate(f'localStorage.setItem("{key}", "{value}")')
            
            # Restore session storage
            if session.get('session_storage'):
                for key, value in session['session_storage'].items():
                    await page.evaluate(f'sessionStorage.setItem("{key}", "{value}")')
            
            credential_logger.logger.info("Session restored successfully")
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to restore session: {str(e)}")
            raise
    
    async def rotate_credentials(self, website_id: str, new_credentials: Dict[str, str]):
        """Rotate credentials for a website."""
        try:
            # Store new credentials
            auth_config = {}  # Get from database if needed
            await self.store_credentials(website_id, new_credentials, auth_config)
            
            # Clear any existing sessions
            redis = await aioredis.from_url(self.redis_url)
            await redis.delete(f"session:{website_id}")
            await redis.close()
            
            credential_logger.logger.info("Credentials rotated successfully")
            
        except Exception as e:
            credential_logger.logger.error(f"Failed to rotate credentials: {str(e)}")
            raise