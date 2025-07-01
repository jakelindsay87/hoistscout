"""
Universal Website Authentication Manager
Handles authentication for any website with various authentication methods
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import httpx
from playwright.async_api import async_playwright, Page, BrowserContext
from bs4 import BeautifulSoup
import pickle
import base64

from ..database import Base
from ..core.simple_logging import ProductionLogger
from ..config import get_settings
from ..utils.crypto import encrypt_data, decrypt_data

settings = get_settings()
production_logger = ProductionLogger()


class UniversalAuthenticator:
    """Universal authentication system for any website."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("universal_auth")
        self.auth_methods = {
            'form': self.authenticate_form_based,
            'oauth': self.authenticate_oauth,
            'api_key': self.authenticate_api_key,
            'basic_auth': self.authenticate_basic_auth,
            'cookie': self.authenticate_cookie_based,
            'custom': self.authenticate_custom
        }
        self.session_cache = {}
        
    async def authenticate(self, website_config: dict) -> dict:
        """
        Authenticate to any website based on configuration.
        
        Args:
            website_config: {
                'url': 'https://example.com',
                'auth_method': 'form|oauth|api_key|basic_auth|cookie|custom',
                'auth_config': {
                    'login_url': 'https://example.com/login',
                    'username_field': 'email',
                    'password_field': 'password',
                    'submit_button': '#login-button',
                    'success_indicator': '.dashboard',
                    'credentials': {
                        'username': 'user@example.com',
                        'password': 'encrypted_password'
                    }
                }
            }
        """
        
        auth_result = {
            'authenticated': False,
            'method': website_config.get('auth_method', 'none'),
            'session_data': {},
            'cookies': {},
            'headers': {},
            'access_level': 'none',
            'expires_at': None,
            'error': None,
            'debug_info': {}
        }
        
        try:
            auth_method = website_config.get('auth_method', 'none')
            
            if auth_method == 'none':
                auth_result['authenticated'] = True
                auth_result['access_level'] = 'public'
                return auth_result
            
            if auth_method not in self.auth_methods:
                raise ValueError(f"Unsupported authentication method: {auth_method}")
            
            # Decrypt credentials if encrypted
            auth_config = website_config.get('auth_config', {})
            if 'credentials' in auth_config:
                auth_config['credentials'] = await self.decrypt_credentials(auth_config['credentials'])
            
            # Execute authentication method
            auth_result = await self.auth_methods[auth_method](website_config['url'], auth_config)
            
            # Cache successful session
            if auth_result['authenticated']:
                domain = urlparse(website_config['url']).netloc
                self.session_cache[domain] = {
                    'auth_result': auth_result,
                    'timestamp': datetime.utcnow()
                }
                self.logger.info(f"Successfully authenticated to {domain} using {auth_method}")
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            auth_result['error'] = str(e)
            auth_result['authenticated'] = False
            
        return auth_result
    
    async def authenticate_form_based(self, base_url: str, auth_config: dict) -> dict:
        """Handle form-based authentication (most common)."""
        
        auth_result = {
            'authenticated': False,
            'method': 'form',
            'session_data': {},
            'cookies': {},
            'headers': {},
            'access_level': 'none',
            'expires_at': None,
            'error': None,
            'debug_info': {}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.HEADLESS_BROWSER,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_https_errors=True
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                window.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                });
            """)
            
            page = await context.new_page()
            
            try:
                # 1. Navigate to login page
                login_url = auth_config.get('login_url', base_url)
                self.logger.info(f"Navigating to login page: {login_url}")
                await page.goto(login_url, wait_until='networkidle', timeout=30000)
                
                # 2. Take screenshot for debugging
                await page.screenshot(path=f'logs/auth_attempt_{urlparse(base_url).netloc}.png')
                
                # 3. Handle cookie notices
                await self.handle_cookie_notices(page)
                
                # 4. Wait for login form
                username_field = auth_config.get('username_field', '#username')
                password_field = auth_config.get('password_field', '#password')
                submit_button = auth_config.get('submit_button', 'button[type="submit"]')
                
                # Try multiple selectors if the default ones don't work
                username_selectors = [
                    username_field,
                    'input[name="username"]',
                    'input[name="email"]',
                    'input[name="user"]',
                    'input[type="email"]',
                    'input[name="name"]',
                    '#email',
                    '#user',
                    '#login'
                ]
                
                password_selectors = [
                    password_field,
                    'input[name="password"]',
                    'input[type="password"]',
                    '#pass',
                    '#pwd'
                ]
                
                # Find username field
                username_element = None
                for selector in username_selectors:
                    try:
                        username_element = await page.wait_for_selector(selector, timeout=3000)
                        if username_element:
                            self.logger.info(f"Found username field with selector: {selector}")
                            break
                    except:
                        continue
                
                if not username_element:
                    raise Exception("Could not find username/email field")
                
                # Find password field
                password_element = None
                for selector in password_selectors:
                    try:
                        password_element = await page.wait_for_selector(selector, timeout=3000)
                        if password_element:
                            self.logger.info(f"Found password field with selector: {selector}")
                            break
                    except:
                        continue
                
                if not password_element:
                    raise Exception("Could not find password field")
                
                # 5. Fill credentials
                credentials = auth_config.get('credentials', {})
                username = credentials.get('username', credentials.get('email', ''))
                password = credentials.get('password', '')
                
                self.logger.info(f"Filling credentials for user: {username}")
                
                # Clear fields first
                await username_element.click()
                await page.keyboard.press('Control+a')
                await page.keyboard.press('Delete')
                await username_element.type(username, delay=100)
                
                await password_element.click()
                await page.keyboard.press('Control+a')
                await page.keyboard.press('Delete')
                await password_element.type(password, delay=100)
                
                # 6. Handle CAPTCHA if present
                captcha_handled = await self.handle_captcha_if_present(page, auth_config)
                
                # 7. Submit form
                submit_selectors = [
                    submit_button,
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Log in")',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'button:has-text("Submit")',
                    '#submit',
                    '.login-button'
                ]
                
                submit_element = None
                for selector in submit_selectors:
                    try:
                        submit_element = await page.query_selector(selector)
                        if submit_element:
                            self.logger.info(f"Found submit button with selector: {selector}")
                            break
                    except:
                        continue
                
                if submit_element:
                    await submit_element.click()
                else:
                    # Try pressing Enter
                    await password_element.press('Enter')
                
                # 8. Wait for navigation or success indicator
                success_indicator = auth_config.get('success_indicator', None)
                
                if success_indicator:
                    try:
                        await page.wait_for_selector(success_indicator, timeout=10000)
                        auth_result['authenticated'] = True
                    except:
                        # Check URL change as fallback
                        await page.wait_for_timeout(5000)
                        current_url = page.url
                        if current_url != login_url and 'login' not in current_url.lower():
                            auth_result['authenticated'] = True
                else:
                    # Wait and check for common success indicators
                    await page.wait_for_timeout(5000)
                    
                    success_indicators = [
                        'logout', 'dashboard', 'profile', 'account',
                        'welcome', 'home', 'search', 'main'
                    ]
                    
                    current_url = page.url.lower()
                    page_content = await page.content()
                    page_text = page_content.lower()
                    
                    # Check URL change
                    if current_url != login_url.lower() and 'login' not in current_url:
                        auth_result['authenticated'] = True
                    # Check page content
                    elif any(indicator in page_text for indicator in success_indicators):
                        auth_result['authenticated'] = True
                    # Check for logout link
                    elif await page.query_selector('a[href*="logout"]'):
                        auth_result['authenticated'] = True
                
                if auth_result['authenticated']:
                    self.logger.info("✅ Authentication successful")
                    
                    # 9. Extract session data
                    auth_result['cookies'] = await self.extract_cookies(context)
                    auth_result['session_data'] = await self.extract_session_data(page)
                    auth_result['access_level'] = 'authenticated'
                    auth_result['expires_at'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
                    
                    # Save authenticated state
                    await context.storage_state(path=f"auth_state_{urlparse(base_url).netloc}.json")
                    
                else:
                    self.logger.error("❌ Authentication failed")
                    await page.screenshot(path=f'logs/auth_failed_{urlparse(base_url).netloc}.png')
                    
                    # Extract error messages
                    error_messages = await self.extract_error_messages(page)
                    auth_result['error'] = ' '.join(error_messages) if error_messages else 'Unknown authentication error'
                    auth_result['debug_info']['error_messages'] = error_messages
                
            except Exception as e:
                self.logger.error(f"Form authentication error: {e}")
                auth_result['error'] = str(e)
                await page.screenshot(path=f'logs/auth_error_{urlparse(base_url).netloc}.png')
                
            finally:
                await browser.close()
        
        return auth_result
    
    async def handle_cookie_notices(self, page: Page):
        """Handle cookie consent banners."""
        
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button[id*="accept"]',
            'button[class*="accept"]',
            'button[class*="consent"]',
            '.cookie-accept',
            '#accept-cookies',
            '[data-testid="cookie-accept"]'
        ]
        
        for selector in cookie_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=2000)
                if button and await button.is_visible():
                    await button.click()
                    self.logger.info(f"Clicked cookie consent: {selector}")
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue
    
    async def handle_captcha_if_present(self, page: Page, auth_config: dict) -> bool:
        """Detect and handle CAPTCHA challenges."""
        
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]',
            'div[class*="captcha"]',
            'div[id*="captcha"]',
            'img[src*="captcha"]',
            '.g-recaptcha',
            '#captcha'
        ]
        
        for selector in captcha_selectors:
            try:
                captcha_element = await page.query_selector(selector)
                if captcha_element:
                    self.logger.warning(f"CAPTCHA detected with selector: {selector}")
                    
                    # If 2captcha API key is configured, solve it
                    if settings.CAPTCHA_API_KEY:
                        self.logger.info("Attempting to solve CAPTCHA with 2captcha")
                        # Implementation would go here
                        # For now, wait for manual solving if in non-headless mode
                        if not settings.HEADLESS_BROWSER:
                            self.logger.info("Please solve the CAPTCHA manually...")
                            await page.wait_for_timeout(30000)  # Wait 30 seconds
                            return True
                    
                    return False
            except:
                continue
        
        return True
    
    async def extract_cookies(self, context: BrowserContext) -> dict:
        """Extract cookies from browser context."""
        
        cookies = await context.cookies()
        cookie_dict = {}
        
        for cookie in cookies:
            cookie_dict[cookie['name']] = {
                'value': cookie['value'],
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/'),
                'expires': cookie.get('expires', None),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', False)
            }
        
        return cookie_dict
    
    async def extract_session_data(self, page: Page) -> dict:
        """Extract useful session data from authenticated page."""
        
        session_data = {}
        
        try:
            # Extract user info if available
            user_info = await page.evaluate("""
                () => {
                    const data = {};
                    
                    // Try to find user name
                    const nameSelectors = [
                        '.user-name', '.username', '.profile-name',
                        '[class*="user"]', '[id*="user"]'
                    ];
                    
                    for (const selector of nameSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent) {
                            data.username = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // Extract any API tokens or session IDs from page
                    const scripts = document.querySelectorAll('script');
                    scripts.forEach(script => {
                        const content = script.textContent || '';
                        
                        // Look for common patterns
                        const tokenMatch = content.match(/token['"]\s*:\s*['"]([^'"]+)['"]/i);
                        const sessionMatch = content.match(/session['"]\s*:\s*['"]([^'"]+)['"]/i);
                        
                        if (tokenMatch) data.token = tokenMatch[1];
                        if (sessionMatch) data.session = sessionMatch[1];
                    });
                    
                    // Get current URL
                    data.authenticated_url = window.location.href;
                    
                    return data;
                }
            """)
            
            session_data.update(user_info)
            
        except Exception as e:
            self.logger.warning(f"Could not extract session data: {e}")
        
        return session_data
    
    async def extract_error_messages(self, page: Page) -> List[str]:
        """Extract error messages from login page."""
        
        try:
            errors = await page.evaluate("""
                () => {
                    const errors = [];
                    const errorSelectors = [
                        '.error', '.alert', '.alert-danger', '.alert-error',
                        '.message--error', '.error-message', '[class*="error"]',
                        '[role="alert"]'
                    ];
                    
                    errorSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > 0 && text.length < 200) {
                                errors.push(text);
                            }
                        });
                    });
                    
                    return [...new Set(errors)];  // Remove duplicates
                }
            """)
            
            return errors
            
        except:
            return []
    
    async def authenticate_oauth(self, base_url: str, auth_config: dict) -> dict:
        """Handle OAuth authentication."""
        
        # OAuth implementation would go here
        # This would handle OAuth2 flow with authorization code, client credentials, etc.
        
        return {
            'authenticated': False,
            'method': 'oauth',
            'error': 'OAuth authentication not yet implemented'
        }
    
    async def authenticate_api_key(self, base_url: str, auth_config: dict) -> dict:
        """Handle API key authentication."""
        
        auth_result = {
            'authenticated': False,
            'method': 'api_key',
            'session_data': {},
            'headers': {},
            'access_level': 'none',
            'error': None
        }
        
        try:
            api_key = auth_config.get('credentials', {}).get('api_key', '')
            api_key_header = auth_config.get('api_key_header', 'X-API-Key')
            
            # Test API key
            test_endpoint = auth_config.get('test_endpoint', base_url)
            
            headers = {
                api_key_header: api_key,
                'User-Agent': 'HoistScout/1.0'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_endpoint, headers=headers)
                
                if response.status_code in [200, 201, 204]:
                    auth_result['authenticated'] = True
                    auth_result['headers'] = headers
                    auth_result['access_level'] = 'api_authenticated'
                else:
                    auth_result['error'] = f'API key authentication failed with status {response.status_code}'
                    
        except Exception as e:
            auth_result['error'] = str(e)
        
        return auth_result
    
    async def authenticate_basic_auth(self, base_url: str, auth_config: dict) -> dict:
        """Handle HTTP Basic authentication."""
        
        auth_result = {
            'authenticated': False,
            'method': 'basic_auth',
            'headers': {},
            'access_level': 'none',
            'error': None
        }
        
        try:
            credentials = auth_config.get('credentials', {})
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            
            # Create basic auth header
            import base64
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_string}',
                'User-Agent': 'HoistScout/1.0'
            }
            
            # Test authentication
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, headers=headers)
                
                if response.status_code in [200, 201, 204]:
                    auth_result['authenticated'] = True
                    auth_result['headers'] = headers
                    auth_result['access_level'] = 'basic_authenticated'
                else:
                    auth_result['error'] = f'Basic auth failed with status {response.status_code}'
                    
        except Exception as e:
            auth_result['error'] = str(e)
        
        return auth_result
    
    async def authenticate_cookie_based(self, base_url: str, auth_config: dict) -> dict:
        """Handle cookie-based authentication."""
        
        # Implementation for sites that use cookies directly
        return {
            'authenticated': False,
            'method': 'cookie',
            'error': 'Cookie authentication not yet implemented'
        }
    
    async def authenticate_custom(self, base_url: str, auth_config: dict) -> dict:
        """Handle custom authentication flows."""
        
        # This would be extended for specific custom authentication needs
        return {
            'authenticated': False,
            'method': 'custom',
            'error': 'Custom authentication not configured'
        }
    
    async def decrypt_credentials(self, credentials: dict) -> dict:
        """Decrypt stored credentials."""
        
        decrypted = {}
        
        for key, value in credentials.items():
            if isinstance(value, str) and value.startswith('encrypted:'):
                # In production, use proper decryption
                decrypted[key] = value.replace('encrypted:', '')
            else:
                decrypted[key] = value
        
        return decrypted
    
    async def test_authenticated_access(self, base_url: str, auth_result: dict, test_urls: List[str] = None) -> dict:
        """Test if authentication provides access to protected resources."""
        
        test_result = {
            'protected_access': False,
            'accessible_urls': [],
            'blocked_urls': [],
            'features_available': []
        }
        
        if not auth_result.get('authenticated'):
            return test_result
        
        # Default test URLs
        if not test_urls:
            test_urls = [
                '/dashboard',
                '/account',
                '/profile',
                '/search',
                '/api/user'
            ]
        
        headers = auth_result.get('headers', {})
        cookies = auth_result.get('cookies', {})
        
        # Convert cookies to httpx format
        jar = httpx.Cookies()
        for name, cookie_data in cookies.items():
            if isinstance(cookie_data, dict):
                jar.set(name, cookie_data.get('value', ''))
            else:
                jar.set(name, cookie_data)
        
        async with httpx.AsyncClient(cookies=jar) as client:
            for test_path in test_urls:
                try:
                    test_url = urljoin(base_url, test_path)
                    response = await client.get(test_url, headers=headers, follow_redirects=True)
                    
                    if response.status_code == 200:
                        test_result['accessible_urls'].append(test_url)
                        test_result['protected_access'] = True
                        
                        # Extract available features from page
                        if 'html' in response.headers.get('content-type', '').lower():
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Look for feature indicators
                            features = []
                            if soup.find(text=re.compile(r'search', re.I)):
                                features.append('search')
                            if soup.find(text=re.compile(r'download', re.I)):
                                features.append('download')
                            if soup.find(text=re.compile(r'export', re.I)):
                                features.append('export')
                            
                            test_result['features_available'].extend(features)
                    else:
                        test_result['blocked_urls'].append(test_url)
                        
                except Exception as e:
                    self.logger.warning(f"Could not test {test_url}: {e}")
                    test_result['blocked_urls'].append(test_url)
        
        test_result['features_available'] = list(set(test_result['features_available']))
        
        return test_result


class AuthenticationTestSuite:
    """Test suite for validating authentication on real websites."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("auth_test_suite")
        self.authenticator = UniversalAuthenticator()
        
    async def test_victorian_tenders_authentication(self) -> dict:
        """Test authentication specifically for Victorian Government Tenders."""
        
        self.logger.info("Starting Victorian Tenders authentication test")
        
        # Victorian Tenders configuration
        vic_tenders_config = {
            'url': 'https://www.tenders.vic.gov.au',
            'auth_method': 'form',
            'auth_config': {
                'login_url': 'https://www.tenders.vic.gov.au/user/login',
                'username_field': '#edit-name',  # Drupal form field
                'password_field': '#edit-pass',   # Drupal form field
                'submit_button': '#edit-submit',  # Drupal submit button
                'success_indicator': 'a[href*="/user/logout"]',  # Logout link indicates success
                'credentials': {
                    'username': 'jacob.lindsay@senversa.com.au',
                    'password': 'h87yQ*26z&ty'
                }
            }
        }
        
        # Perform authentication
        auth_result = await self.authenticator.authenticate(vic_tenders_config)
        
        # Test authenticated access
        if auth_result['authenticated']:
            test_urls = [
                '/tender/search?preset=open',
                '/tender/search?preset=closed',
                '/user'
            ]
            
            access_test = await self.authenticator.test_authenticated_access(
                vic_tenders_config['url'],
                auth_result,
                test_urls
            )
            
            auth_result['access_test'] = access_test
            
            # Log comprehensive results
            self.logger.info(f"""
            Victorian Tenders Authentication Test Results:
            - Authenticated: {auth_result['authenticated']}
            - Method: {auth_result['method']}
            - Access Level: {auth_result['access_level']}
            - Protected Access: {access_test['protected_access']}
            - Accessible URLs: {len(access_test['accessible_urls'])}
            - Available Features: {access_test['features_available']}
            """)
        
        return auth_result
    
    async def test_generic_website_authentication(self, website_config: dict) -> dict:
        """Test authentication for any website with provided configuration."""
        
        domain = urlparse(website_config['url']).netloc
        self.logger.info(f"Starting authentication test for {domain}")
        
        # Perform authentication
        auth_result = await self.authenticator.authenticate(website_config)
        
        # Test authenticated access if successful
        if auth_result['authenticated']:
            access_test = await self.authenticator.test_authenticated_access(
                website_config['url'],
                auth_result
            )
            
            auth_result['access_test'] = access_test
            
            self.logger.info(f"""
            {domain} Authentication Test Results:
            - Authenticated: {auth_result['authenticated']}
            - Method: {auth_result['method']}
            - Access Level: {auth_result['access_level']}
            - Protected Access: {access_test.get('protected_access', False)}
            """)
        
        return auth_result