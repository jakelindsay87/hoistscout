"""Site-specific crawler implementation using configuration."""

import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .base import BaseSiteCrawler, AuthFailure, CaptchaChallenge
from .config import SiteConfig


class ConfigurableSiteCrawler(BaseSiteCrawler):
    """Site crawler that uses configuration for flexible crawling."""
    
    def __init__(self, config: SiteConfig, proxy_pool: List[str] = None):
        """Initialize with site configuration.
        
        Args:
            config: Site configuration object
            proxy_pool: List of proxy server URLs
        """
        # Convert config to dict format for base class
        site_cfg = {
            "name": config.name,
            "start_urls": config.start_urls,
            "selectors": config.selectors or {},
            "headers": config.headers or {},
            "delay": config.delay,
            "timeout": config.timeout,
            "credentials": {
                "username": config.auth.username if config.auth else None,
                "password": config.auth.password if config.auth else None,
            } if config.auth else None
        }
        
        super().__init__(site_cfg, proxy_pool or [])
        self.config = config
    
    async def _perform_login(self, page: Page) -> None:
        """Perform login using configuration."""
        if not self.config.auth or self.config.auth.type != "login_form":
            raise AuthFailure("Login form authentication not configured")
        
        auth = self.config.auth
        
        # Navigate to login page if specified
        if auth.login_url and page.url != auth.login_url:
            await page.goto(auth.login_url)
        
        # Wait for login form to be visible
        try:
            await page.wait_for_selector(auth.selectors["user"], timeout=10000)
        except PlaywrightTimeoutError:
            raise AuthFailure(f"Login form not found at {page.url}")
        
        # Fill in credentials
        await page.fill(auth.selectors["user"], auth.username)
        await page.fill(auth.selectors["pass"], auth.password)
        
        # Submit form
        await page.click(auth.selectors["submit"])
        
        # Wait for navigation or success indicator
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        
        # Check if login was successful (basic check)
        if await page.locator(auth.selectors["user"]).count() > 0:
            # Still on login page, login likely failed
            raise AuthFailure("Login appears to have failed - still on login page")
    
    async def _crawl_page(self, url: str) -> Dict[str, Any]:
        """Crawl a single page and extract data."""
        context = await self._new_context()
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            
            # Check for CAPTCHA
            await self.detect_captcha(page)
            
            # Handle authentication if needed
            await self.login_if_needed(page)
            
            # Wait for content to load
            await page.wait_for_load_state("networkidle")
            
            # Extract data using selectors
            data = {
                "url": url,
                "title": await page.title(),
                "content": await page.content(),
                "extracted": {}
            }
            
            # Apply custom selectors if configured
            if self.config.selectors:
                for key, selector in self.config.selectors.items():
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            data["extracted"][key] = [
                                await elem.text_content() for elem in elements
                            ]
                    except Exception as e:
                        data["extracted"][key] = f"Error: {str(e)}"
            
            return data
            
        finally:
            await context.close()
    
    async def _get_next_page_url(self, page: Page) -> str | None:
        """Get the URL of the next page using pagination config."""
        if not self.config.pagination:
            return None
        
        try:
            next_link = page.locator(self.config.pagination.selector).first
            if await next_link.count() > 0:
                return await next_link.get_attribute("href")
        except Exception:
            pass
        
        return None
    
    async def crawl(self) -> Dict[str, Any]:
        """Main crawling method that handles pagination."""
        results = {
            "site": self.config.name,
            "pages": [],
            "total_pages": 0,
            "errors": []
        }
        
        for start_url in self.config.start_urls:
            current_url = start_url
            page_count = 0
            max_pages = self.config.pagination.limit if self.config.pagination else 1
            
            while current_url and page_count < max_pages:
                try:
                    # Add delay between requests
                    if page_count > 0:
                        await asyncio.sleep(self.config.delay)
                    
                    # Crawl current page
                    page_data = await self._crawl_page(current_url)
                    results["pages"].append(page_data)
                    page_count += 1
                    results["total_pages"] += 1
                    
                    # Get next page URL if pagination is enabled
                    if self.config.pagination and page_count < max_pages:
                        context = await self._new_context()
                        try:
                            page = await context.new_page()
                            await page.goto(current_url)
                            await self.login_if_needed(page)
                            current_url = await self._get_next_page_url(page)
                        finally:
                            await context.close()
                    else:
                        current_url = None
                        
                except CaptchaChallenge as e:
                    error_msg = f"CAPTCHA challenge on {current_url}: {str(e)}"
                    results["errors"].append(error_msg)
                    break
                    
                except AuthFailure as e:
                    error_msg = f"Authentication failed on {current_url}: {str(e)}"
                    results["errors"].append(error_msg)
                    break
                    
                except Exception as e:
                    error_msg = f"Error crawling {current_url}: {str(e)}"
                    results["errors"].append(error_msg)
                    # Continue with next page on non-critical errors
                    current_url = None
        
        return results


async def create_crawler_from_config(config_data: Dict[str, Any], proxy_pool: List[str] = None) -> ConfigurableSiteCrawler:
    """Factory function to create a crawler from configuration data."""
    from .config import ConfigLoader
    
    site_config = ConfigLoader.load_from_dict(config_data)
    return ConfigurableSiteCrawler(site_config, proxy_pool) 