"""Site-specific crawler implementation using configuration."""

import asyncio
import time
import uuid
from typing import List, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .base import BaseSiteCrawler, AuthFailure, CaptchaChallenge
from .config import SiteConfig
from ..logging_config import get_logger, log_performance, log_security_event

logger = get_logger(__name__)


class ConfigurableSiteCrawler(BaseSiteCrawler):
    """Site crawler that uses configuration for flexible crawling."""
    
    def __init__(self, config: SiteConfig, proxy_pool: List[str] = None):
        """Initialize with site configuration.
        
        Args:
            config: Site configuration object
            proxy_pool: List of proxy server URLs
        """
        logger.info(f"Initializing crawler for site: {config.name}")
        
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
        self.crawl_id = str(uuid.uuid4())
        
        logger.info(f"Crawler initialized with {len(proxy_pool or [])} proxies",
                   extra={'extra_fields': {'crawl_id': self.crawl_id, 'site': config.name}})
    
    async def _perform_login(self, page: Page) -> None:
        """Perform login using configuration."""
        if not self.config.auth or self.config.auth.type != "login_form":
            logger.warning(f"Login form authentication not configured for {self.config.name}")
            raise AuthFailure("Login form authentication not configured")
        
        log_security_event(logger, "login_attempt",
                         site=self.config.name,
                         login_url=self.config.auth.login_url,
                         crawl_id=self.crawl_id)
        
        auth = self.config.auth
        
        # Navigate to login page if specified
        if auth.login_url and page.url != auth.login_url:
            logger.info(f"Navigating to login page: {auth.login_url}")
            await page.goto(auth.login_url)
        
        # Wait for login form to be visible
        try:
            await page.wait_for_selector(auth.selectors["user"], timeout=10000)
            logger.debug("Login form found")
        except PlaywrightTimeoutError:
            log_security_event(logger, "login_failure",
                             site=self.config.name,
                             reason="login_form_not_found",
                             crawl_id=self.crawl_id)
            raise AuthFailure(f"Login form not found at {page.url}")
        
        # Fill in credentials
        logger.debug(f"Filling login credentials for user: {auth.username[:3]}***")
        await page.fill(auth.selectors["user"], auth.username)
        await page.fill(auth.selectors["pass"], auth.password)
        
        # Submit form
        logger.debug("Submitting login form")
        await page.click(auth.selectors["submit"])
        
        # Wait for navigation or success indicator
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        
        # Check if login was successful (basic check)
        if await page.locator(auth.selectors["user"]).count() > 0:
            # Still on login page, login likely failed
            log_security_event(logger, "login_failure",
                             site=self.config.name,
                             reason="still_on_login_page",
                             crawl_id=self.crawl_id)
            raise AuthFailure("Login appears to have failed - still on login page")
        
        log_security_event(logger, "login_success",
                         site=self.config.name,
                         crawl_id=self.crawl_id)
    
    async def _crawl_page(self, url: str) -> Dict[str, Any]:
        """Crawl a single page and extract data."""
        page_start = time.time()
        logger.info(f"Crawling page: {url}")
        
        context = await self._new_context()
        try:
            page = await context.new_page()
            
            nav_start = time.time()
            await page.goto(url, wait_until="domcontentloaded")
            nav_duration = time.time() - nav_start
            log_performance(logger, "page_navigation", nav_duration,
                          url=url,
                          crawl_id=self.crawl_id)
            
            # Check for CAPTCHA
            try:
                await self.detect_captcha(page)
            except CaptchaChallenge as e:
                log_security_event(logger, "captcha_detected",
                                 site=self.config.name,
                                 url=url,
                                 crawl_id=self.crawl_id)
                raise
            
            # Handle authentication if needed
            if self.config.auth:
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
                extraction_start = time.time()
                extracted_count = 0
                
                for key, selector in self.config.selectors.items():
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            data["extracted"][key] = [
                                await elem.text_content() for elem in elements
                            ]
                            extracted_count += len(elements)
                            logger.debug(f"Extracted {len(elements)} elements for selector '{key}'")
                    except Exception as e:
                        logger.error(f"Failed to extract data for selector '{key}': {str(e)}")
                        data["extracted"][key] = f"Error: {str(e)}"
                
                extraction_duration = time.time() - extraction_start
                log_performance(logger, "data_extraction", extraction_duration,
                              selectors_count=len(self.config.selectors),
                              elements_extracted=extracted_count)
            
            page_duration = time.time() - page_start
            log_performance(logger, "page_crawl_complete", page_duration,
                          url=url,
                          success=True)
            
            return data
            
        except Exception as e:
            page_duration = time.time() - page_start
            log_performance(logger, "page_crawl_complete", page_duration,
                          url=url,
                          success=False)
            logger.error(f"Error crawling page {url}: {str(e)}", exc_info=True)
            raise
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
        crawl_start = time.time()
        logger.info(f"Starting crawl for {self.config.name} with {len(self.config.start_urls)} start URLs",
                   extra={'extra_fields': {'crawl_id': self.crawl_id}})
        
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
                        logger.debug(f"Rate limiting: waiting {self.config.delay} seconds")
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
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    break
                    
                except AuthFailure as e:
                    error_msg = f"Authentication failed on {current_url}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    break
                    
                except Exception as e:
                    error_msg = f"Error crawling {current_url}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    results["errors"].append(error_msg)
                    # Continue with next page on non-critical errors
                    current_url = None
        
        crawl_duration = time.time() - crawl_start
        log_performance(logger, "crawl_complete", crawl_duration,
                      site=self.config.name,
                      pages_crawled=results["total_pages"],
                      errors_count=len(results["errors"]),
                      crawl_id=self.crawl_id)
        
        logger.info(f"Crawl completed for {self.config.name}: {results['total_pages']} pages, {len(results['errors'])} errors")
        
        return results


async def create_crawler_from_config(config_data: Dict[str, Any], proxy_pool: List[str] = None) -> ConfigurableSiteCrawler:
    """Factory function to create a crawler from configuration data."""
    from .config import ConfigLoader
    
    site_config = ConfigLoader.load_from_dict(config_data)
    return ConfigurableSiteCrawler(site_config, proxy_pool) 