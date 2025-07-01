#!/usr/bin/env python3
"""
Simple authentication test for Victorian Government Tenders
"""

import asyncio
from playwright.async_api import async_playwright
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleVicTendersAuth:
    """Simple authentication test for Victorian Tenders"""
    
    def __init__(self):
        self.logger = logger
        self.credentials = {
            'email': 'jacob.lindsay@senversa.com.au',
            'password': 'h87yQ*26z&ty'
        }
        self.base_url = 'https://www.tenders.vic.gov.au'
        self.login_url = 'https://www.tenders.vic.gov.au/user/login'
        
    async def test_authentication(self) -> dict:
        """Test authentication flow"""
        
        auth_result = {
            'authenticated': False,
            'timestamp': datetime.utcnow().isoformat(),
            'error': None
        }
        
        async with async_playwright() as p:
            self.logger.info("Launching browser...")
            browser = await p.chromium.launch(
                headless=False,  # Set to False to see what's happening
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to login page
                self.logger.info(f"Navigating to: {self.login_url}")
                await page.goto(self.login_url, wait_until='networkidle', timeout=30000)
                
                # Take screenshot
                await page.screenshot(path='login_page.png')
                self.logger.info("Screenshot saved: login_page.png")
                
                # Wait a bit for page to fully load
                await page.wait_for_timeout(2000)
                
                # Try to find login form fields
                self.logger.info("Looking for login form fields...")
                
                # Check for Drupal login form fields
                username_field = await page.query_selector('#edit-name')
                password_field = await page.query_selector('#edit-pass')
                
                if username_field and password_field:
                    self.logger.info("Found Drupal login form fields")
                    
                    # Fill credentials
                    self.logger.info("Filling credentials...")
                    await username_field.fill(self.credentials['email'])
                    await password_field.fill(self.credentials['password'])
                    
                    # Look for submit button
                    submit_button = await page.query_selector('#edit-submit')
                    if submit_button:
                        self.logger.info("Clicking submit button...")
                        await submit_button.click()
                        
                        # Wait for navigation
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        
                        # Check if logged in
                        current_url = page.url
                        self.logger.info(f"Current URL after login: {current_url}")
                        
                        # Take screenshot after login attempt
                        await page.screenshot(path='after_login.png')
                        self.logger.info("Screenshot saved: after_login.png")
                        
                        # Check for logout link as sign of successful login
                        logout_link = await page.query_selector('a[href*="/user/logout"]')
                        if logout_link:
                            auth_result['authenticated'] = True
                            self.logger.info("✅ Authentication successful!")
                        else:
                            self.logger.warning("❌ Could not find logout link")
                            
                            # Check for error messages
                            error_elements = await page.query_selector_all('.messages--error, .alert-danger')
                            if error_elements:
                                errors = []
                                for elem in error_elements:
                                    error_text = await elem.text_content()
                                    errors.append(error_text.strip())
                                auth_result['error'] = ' | '.join(errors)
                                self.logger.error(f"Login errors: {auth_result['error']}")
                    else:
                        self.logger.error("Could not find submit button")
                        auth_result['error'] = "Submit button not found"
                else:
                    self.logger.error("Could not find login form fields")
                    auth_result['error'] = "Login form fields not found"
                    
                    # Save page HTML for debugging
                    page_content = await page.content()
                    with open('login_page.html', 'w') as f:
                        f.write(page_content)
                    self.logger.info("Saved page HTML to login_page.html for debugging")
                    
            except Exception as e:
                self.logger.error(f"Authentication error: {e}")
                auth_result['error'] = str(e)
                
            finally:
                await browser.close()
                
        return auth_result


async def main():
    """Run authentication test"""
    
    print("🔐 Testing Victorian Government Tenders Authentication")
    print("=" * 60)
    print(f"Email: jacob.lindsay@senversa.com.au")
    print(f"URL: https://www.tenders.vic.gov.au")
    print("=" * 60)
    
    auth_tester = SimpleVicTendersAuth()
    result = await auth_tester.test_authentication()
    
    print(f"\n📊 Results:")
    print(f"  Authenticated: {'✅ YES' if result['authenticated'] else '❌ NO'}")
    
    if result['error']:
        print(f"  Error: {result['error']}")
    
    print(f"\n📸 Screenshots saved:")
    print(f"  - login_page.png")
    print(f"  - after_login.png")
    
    if not result['authenticated']:
        print(f"\n💡 Debug info saved to login_page.html")
    
    print("\n" + "=" * 60)
    
    return result


if __name__ == "__main__":
    asyncio.run(main())