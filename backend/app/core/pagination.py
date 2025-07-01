"""
Advanced pagination detection and handling system for various pagination types.
"""
from typing import Dict, List, Optional, Any, Callable
from playwright.async_api import Page, ElementHandle
import asyncio
import re
from abc import ABC, abstractmethod
from .logging import pagination_logger, scraping_logger, log_performance
from .anti_detection import AntiDetectionMixin


class PaginationStrategy(ABC):
    """Base class for pagination strategies."""
    
    @abstractmethod
    async def detect(self, page: Page) -> bool:
        """Detect if this pagination type is present."""
        pass
    
    @abstractmethod
    async def navigate(self, page: Page, target_page: int = None) -> bool:
        """Navigate to next page or specific page number."""
        pass
    
    @abstractmethod
    async def get_total_pages(self, page: Page) -> Optional[int]:
        """Get total number of pages if available."""
        pass


class NumberedPaginationStrategy(PaginationStrategy):
    """Handle numbered pagination (1, 2, 3, ... Next)."""
    
    def __init__(self):
        self.selectors = [
            '.pagination a',
            '.page-numbers a',
            '.pager a',
            'ul.pagination li a',
            'div.pagination span',
            'nav[aria-label*="pagination"] a',
            'a[href*="page="]',
            'a[href*="p="]'
        ]
        self.next_patterns = [
            'Next', '>', 'next', '→', 'Continue', 'More',
            'siguiente', 'próximo', 'suivant'
        ]
    
    async def detect(self, page: Page) -> bool:
        """Detect numbered pagination elements."""
        for selector in self.selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    pagination_logger.log_pagination_detection(
                        page.url,
                        "numbered",
                        {"selector": selector, "element_count": len(elements)}
                    )
                    return True
            except Exception:
                continue
        return False
    
    async def navigate(self, page: Page, target_page: int = None) -> bool:
        """Navigate to specific page or next page."""
        try:
            if target_page:
                # Try to find and click specific page number
                for selector in self.selectors:
                    link = await page.query_selector(f'{selector}:has-text("{target_page}")')
                    if link:
                        await link.click()
                        await page.wait_for_load_state('networkidle', timeout=30000)
                        pagination_logger.log_page_navigation(
                            0, target_page, "direct_click", True
                        )
                        return True
            
            # Find and click next button
            for pattern in self.next_patterns:
                for selector in self.selectors:
                    next_link = await page.query_selector(f'{selector}:has-text("{pattern}")')
                    if next_link:
                        is_disabled = await next_link.get_attribute('disabled')
                        if not is_disabled:
                            await next_link.click()
                            await page.wait_for_load_state('networkidle', timeout=30000)
                            pagination_logger.log_page_navigation(
                                0, 0, "next_button", True
                            )
                            return True
            
            return False
        except Exception as e:
            pagination_logger.logger.error("Navigation failed", error=str(e))
            return False
    
    async def get_total_pages(self, page: Page) -> Optional[int]:
        """Extract total page count."""
        try:
            # Look for last page number
            page_numbers = []
            for selector in self.selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip().isdigit():
                        page_numbers.append(int(text.strip()))
            
            return max(page_numbers) if page_numbers else None
        except Exception:
            return None


class InfiniteScrollStrategy(PaginationStrategy, AntiDetectionMixin):
    """Handle infinite scroll pagination."""
    
    def __init__(self):
        self.triggers = [
            '[data-infinite-scroll]',
            '.infinite-scroll-container',
            '[data-scroll-trigger]',
            '.scroll-trigger',
            '[data-load-more-scroll]'
        ]
        self.loading_indicators = [
            '.loading',
            '.spinner',
            '[data-loading]',
            '.loader',
            '.loading-spinner',
            '.infinite-scroll-loader'
        ]
    
    async def detect(self, page: Page) -> bool:
        """Detect infinite scroll setup."""
        # Check for infinite scroll attributes
        for trigger in self.triggers:
            element = await page.query_selector(trigger)
            if element:
                pagination_logger.log_pagination_detection(
                    page.url,
                    "infinite_scroll",
                    {"trigger": trigger}
                )
                return True
        
        # Check JavaScript for scroll event listeners
        has_scroll_listener = await page.evaluate('''
            () => {
                const scrollHandlers = getEventListeners(window).scroll || [];
                const docScrollHandlers = getEventListeners(document).scroll || [];
                return scrollHandlers.length > 0 || docScrollHandlers.length > 0;
            }
        ''')
        
        if has_scroll_listener:
            pagination_logger.log_pagination_detection(
                page.url,
                "infinite_scroll",
                {"method": "scroll_event_detection"}
            )
            return True
        
        return False
    
    async def navigate(self, page: Page, target_page: int = None) -> bool:
        """Trigger infinite scroll to load more content."""
        try:
            initial_height = await page.evaluate('document.body.scrollHeight')
            
            # Perform human-like scrolling
            await self.human_like_scroll(page)
            
            # Wait for new content
            await self._wait_for_new_content(page, initial_height)
            
            pagination_logger.log_page_navigation(
                0, 0, "infinite_scroll", True
            )
            return True
        except Exception as e:
            pagination_logger.logger.error("Infinite scroll failed", error=str(e))
            return False
    
    async def _wait_for_new_content(self, page: Page, initial_height: int, 
                                  timeout: int = 10000):
        """Wait for new content to load after scrolling."""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            current_height = await page.evaluate('document.body.scrollHeight')
            if current_height > initial_height:
                # New content loaded
                await asyncio.sleep(1)  # Wait for content to stabilize
                return True
            
            # Check for loading indicators
            for indicator in self.loading_indicators:
                loading = await page.query_selector(indicator)
                if loading and await loading.is_visible():
                    # Wait for loading to complete
                    await page.wait_for_selector(indicator, state='hidden', timeout=5000)
                    return True
            
            await asyncio.sleep(0.5)
        
        return False
    
    async def get_total_pages(self, page: Page) -> Optional[int]:
        """Infinite scroll doesn't have fixed page count."""
        return None


class LoadMoreButtonStrategy(PaginationStrategy):
    """Handle 'Load More' button pagination."""
    
    def __init__(self):
        self.button_selectors = [
            'button:has-text("Load More")',
            'button:has-text("Show More")',
            'button:has-text("View More")',
            'a:has-text("Load More")',
            '.load-more',
            '.show-more',
            '[data-load-more]',
            'button[class*="load-more"]'
        ]
    
    async def detect(self, page: Page) -> bool:
        """Detect load more button."""
        for selector in self.button_selectors:
            button = await page.query_selector(selector)
            if button and await button.is_visible():
                pagination_logger.log_pagination_detection(
                    page.url,
                    "load_more_button",
                    {"selector": selector}
                )
                return True
        return False
    
    async def navigate(self, page: Page, target_page: int = None) -> bool:
        """Click load more button."""
        try:
            for selector in self.button_selectors:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    # Record current item count
                    initial_count = await self._count_items(page)
                    
                    await button.click()
                    
                    # Wait for new items
                    await self._wait_for_more_items(page, initial_count)
                    
                    pagination_logger.log_page_navigation(
                        0, 0, "load_more_click", True
                    )
                    return True
            
            return False
        except Exception as e:
            pagination_logger.logger.error("Load more failed", error=str(e))
            return False
    
    async def _count_items(self, page: Page) -> int:
        """Count current items on page."""
        # Common item selectors
        item_selectors = [
            '.result-item',
            '.opportunity-item',
            '.tender-item',
            'article',
            '.list-item',
            'tr.data-row'
        ]
        
        for selector in item_selectors:
            items = await page.query_selector_all(selector)
            if items:
                return len(items)
        
        return 0
    
    async def _wait_for_more_items(self, page: Page, initial_count: int, 
                                  timeout: int = 10000):
        """Wait for new items to appear."""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            current_count = await self._count_items(page)
            if current_count > initial_count:
                await asyncio.sleep(0.5)  # Wait for loading to complete
                return True
            await asyncio.sleep(0.5)
        
        return False
    
    async def get_total_pages(self, page: Page) -> Optional[int]:
        """Load more doesn't have fixed page count."""
        return None


class AjaxPaginationStrategy(PaginationStrategy):
    """Handle AJAX-based pagination without page reload."""
    
    def __init__(self):
        self.ajax_indicators = [
            '[data-ajax-pagination]',
            '[data-page-url]',
            '[data-ajax-url]',
            '.ajax-pagination'
        ]
        self.content_containers = [
            '.results-container',
            '.content-area',
            '#results',
            '.opportunities-list',
            '[data-results]'
        ]
    
    async def detect(self, page: Page) -> bool:
        """Detect AJAX pagination setup."""
        # Check for AJAX pagination attributes
        for indicator in self.ajax_indicators:
            element = await page.query_selector(indicator)
            if element:
                pagination_logger.log_pagination_detection(
                    page.url,
                    "ajax_pagination",
                    {"indicator": indicator}
                )
                return True
        
        # Check for AJAX setup in page scripts
        has_ajax = await page.evaluate('''
            () => {
                // Check for common AJAX pagination setups
                return typeof jQuery !== 'undefined' && 
                       jQuery._data(document, 'events')?.click?.some(e => 
                           e.handler.toString().includes('ajax') || 
                           e.handler.toString().includes('load')
                       );
            }
        ''')
        
        if has_ajax:
            pagination_logger.log_pagination_detection(
                page.url,
                "ajax_pagination",
                {"method": "ajax_detection"}
            )
            return True
        
        return False
    
    async def navigate(self, page: Page, target_page: int = None) -> bool:
        """Handle AJAX pagination navigation."""
        try:
            # Intercept AJAX requests
            ajax_complete = asyncio.create_task(self._wait_for_ajax_complete(page))
            
            # Try numbered pagination first
            numbered_strategy = NumberedPaginationStrategy()
            if await numbered_strategy.navigate(page, target_page):
                # Wait for AJAX to complete
                await ajax_complete
                pagination_logger.log_page_navigation(
                    0, target_page or 0, "ajax_navigation", True
                )
                return True
            
            return False
        except Exception as e:
            pagination_logger.logger.error("AJAX navigation failed", error=str(e))
            return False
    
    async def _wait_for_ajax_complete(self, page: Page, timeout: int = 10000):
        """Wait for AJAX request to complete."""
        await page.wait_for_load_state('networkidle', timeout=timeout)
        
        # Additional wait for content update
        await page.wait_for_function('''
            () => {
                // Check if jQuery AJAX is complete
                if (typeof jQuery !== 'undefined') {
                    return jQuery.active === 0;
                }
                // Check for fetch API
                return true;
            }
        ''', timeout=timeout)
    
    async def get_total_pages(self, page: Page) -> Optional[int]:
        """Get total pages from AJAX pagination."""
        # Delegate to numbered pagination strategy
        numbered_strategy = NumberedPaginationStrategy()
        return await numbered_strategy.get_total_pages(page)


class AdvancedPaginationHandler(AntiDetectionMixin):
    """Main pagination handler that detects and uses appropriate strategy."""
    
    def __init__(self):
        self.strategies = {
            'numbered': NumberedPaginationStrategy(),
            'infinite_scroll': InfiniteScrollStrategy(),
            'load_more': LoadMoreButtonStrategy(),
            'ajax': AjaxPaginationStrategy()
        }
        self.current_strategy = None
        self.pagination_type = None
    
    @log_performance("pagination")
    async def detect_and_handle_pagination(self, page: Page, 
                                         website_config: Dict[str, Any],
                                         extraction_callback: Callable) -> List[Dict[str, Any]]:
        """
        Detect pagination type and handle complete extraction.
        
        Args:
            page: Playwright page object
            website_config: Website configuration
            extraction_callback: Function to extract data from each page
            
        Returns:
            List of all extracted opportunities
        """
        pagination_logger.logger.info(
            "Starting pagination detection",
            website_id=website_config.get('id'),
            url=page.url
        )
        
        # Detect pagination type
        self.pagination_type = await self._detect_pagination_type(page)
        
        if not self.pagination_type:
            pagination_logger.logger.warning("No pagination detected, processing single page")
            return await extraction_callback(page)
        
        # Use detected strategy
        self.current_strategy = self.strategies[self.pagination_type]
        
        # Get total pages if available
        total_pages = await self.current_strategy.get_total_pages(page)
        max_pages = website_config.get('max_pages', 100)
        
        if total_pages:
            total_pages = min(total_pages, max_pages)
            pagination_logger.logger.info(f"Will process {total_pages} pages (max: {max_pages})")
        
        # Process all pages
        return await self._process_all_pages(
            page, website_config, extraction_callback, total_pages
        )
    
    async def _detect_pagination_type(self, page: Page) -> Optional[str]:
        """Detect which pagination type is present."""
        # Check in order of specificity
        detection_order = [
            ('ajax', self.strategies['ajax']),
            ('numbered', self.strategies['numbered']),
            ('load_more', self.strategies['load_more']),
            ('infinite_scroll', self.strategies['infinite_scroll'])
        ]
        
        for pag_type, strategy in detection_order:
            if await strategy.detect(page):
                pagination_logger.logger.info(f"Detected {pag_type} pagination")
                return pag_type
        
        return None
    
    async def _process_all_pages(self, page: Page, website_config: Dict[str, Any],
                               extraction_callback: Callable,
                               total_pages: Optional[int]) -> List[Dict[str, Any]]:
        """Process all pages using the detected strategy."""
        all_opportunities = []
        current_page = 1
        max_pages = website_config.get('max_pages', 100)
        consecutive_empty_pages = 0
        max_empty_pages = 3
        
        while current_page <= max_pages:
            try:
                pagination_logger.logger.info(
                    f"Processing page {current_page}" + 
                    (f"/{total_pages}" if total_pages else "")
                )
                
                # Extract opportunities from current page
                page_opportunities = await extraction_callback(page)
                
                if not page_opportunities:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= max_empty_pages:
                        pagination_logger.logger.warning(
                            f"Stopping after {max_empty_pages} consecutive empty pages"
                        )
                        break
                else:
                    consecutive_empty_pages = 0
                    all_opportunities.extend(page_opportunities)
                
                pagination_logger.log_extraction_result(
                    current_page,
                    len(page_opportunities),
                    0,  # Time tracked by decorator
                    []
                )
                
                scraping_logger.logger.info(
                    f"Page {current_page} complete",
                    opportunities_found=len(page_opportunities),
                    total_so_far=len(all_opportunities)
                )
                
                # Check if we've reached the target
                if total_pages and current_page >= total_pages:
                    break
                
                # Navigate to next page
                has_next = await self.current_strategy.navigate(page)
                if not has_next:
                    pagination_logger.logger.info("No more pages available")
                    break
                
                # Anti-detection delay
                await self.anti_detection_delay()
                
                current_page += 1
                
            except Exception as e:
                pagination_logger.logger.error(
                    f"Error processing page {current_page}",
                    error=str(e)
                )
                # Continue to next page on error
                current_page += 1
                continue
        
        # Log completion statistics
        pagination_logger.log_pagination_complete(
            current_page - 1,
            len(all_opportunities),
            0  # Time tracked by decorator
        )
        
        return all_opportunities
    
    async def handle_special_cases(self, page: Page, website_config: Dict[str, Any]):
        """Handle special pagination cases for known websites."""
        special_cases = {
            'tenders.vic.gov.au': {
                'strategy': 'numbered',
                'selectors': ['.pagination-container a'],
                'wait_after_click': 2000
            },
            'tenders.nsw.gov.au': {
                'strategy': 'ajax',
                'content_container': '#tender-results',
                'requires_auth': True
            }
        }
        
        # Check if current URL matches any special case
        for domain, config in special_cases.items():
            if domain in page.url:
                pagination_logger.logger.info(
                    f"Using special case handling for {domain}"
                )
                # Apply special configuration
                return config
        
        return None