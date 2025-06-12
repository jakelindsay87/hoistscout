"""Base crawler implementation with stealth capabilities and error handling.

RULES
1. Pagination order:
   (a) CSS selector in sites.yml
   (b) link text ~= /(next|›)/i
   (c) stop at repeat URL or limit
2. Delay jitter 0.8-2.4 s between clicks.
3. 10 % sessions run headed for fingerprint diversity.
4. Respect robots.txt – abort if disallowed.
5. Attachments: HEAD only; skip download >50 MB or 4xx.
6. If analyse_terms forbids scraping → mark site legal_blocked.
"""

import random
from typing import Optional
from playwright.async_api import Browser, BrowserContext, Page
from playwright_stealth import stealth_async as add_stealth


class CaptchaChallenge(Exception):
    """Raised when a CAPTCHA challenge is detected."""
    pass


class AuthFailure(Exception):
    """Raised when authentication fails."""
    pass


def fake_user_agent() -> str:
    """Generate a realistic user agent string."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(user_agents)


class BaseSiteCrawler:
    """Base class for site-specific crawlers with stealth and proxy support."""
    
    def __init__(self, site_cfg: dict, proxy_pool: list[str]):
        """Initialize crawler with site configuration and proxy pool.
        
        Args:
            site_cfg: Site-specific configuration dictionary
            proxy_pool: List of proxy server URLs
        """
        self.site_cfg = site_cfg
        self.proxy_pool = proxy_pool
        self.browser: Optional[Browser] = None
    
    async def _new_context(self) -> BrowserContext:
        """Create a new browser context with stealth and proxy configuration."""
        if not self.browser:
            raise RuntimeError("Browser not initialized. Call setup() first.")
        
        ua = fake_user_agent()
        proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
        
        context_options = {"user_agent": ua}
        if proxy:
            context_options["proxy"] = {"server": proxy}
        
        context = await self.browser.new_context(**context_options)
        await add_stealth(context)
        return context
    
    async def fetch_html(self, url: str) -> str:
        """Fetch HTML content from the given URL.
        
        Args:
            url: Target URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            CaptchaChallenge: If CAPTCHA is detected
            AuthFailure: If authentication is required but fails
        """
        context = await self._new_context()
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            
            # Check for CAPTCHA before proceeding
            await self.detect_captcha(page)
            
            # Handle authentication if needed
            await self.login_if_needed(page)
            
            # Wait for content to load
            await page.wait_for_load_state("networkidle")
            
            return await page.content()
        finally:
            await context.close()
    
    async def detect_captcha(self, page: Page) -> None:
        """Detect CAPTCHA challenges on the page.
        
        Args:
            page: Playwright page object
            
        Raises:
            CaptchaChallenge: If CAPTCHA is detected
        """
        captcha_selectors = [
            'iframe[src*="captcha" i]',
            'div.g-recaptcha',
            '[data-sitekey]',
            '.captcha',
            '#captcha',
            '.hcaptcha',
            '.cf-challenge-form'
        ]
        
        for selector in captcha_selectors:
            if await page.locator(selector).count() > 0:
                raise CaptchaChallenge(f"CAPTCHA detected on {page.url}")
    
    async def login_if_needed(self, page: Page) -> None:
        """Handle authentication if required by the site.
        
        Args:
            page: Playwright page object
            
        Raises:
            AuthFailure: If authentication is required but fails
        """
        # Check if login is required
        login_indicators = [
            'input[type="password"]',
            '.login-form',
            '#login',
            'a[href*="login"]',
            'button:has-text("Sign In")',
            'button:has-text("Log In")'
        ]
        
        for indicator in login_indicators:
            if await page.locator(indicator).count() > 0:
                # Site requires authentication
                if not self.site_cfg.get("credentials"):
                    raise AuthFailure(f"Authentication required but no credentials provided for {page.url}")
                
                # Implement site-specific login logic in subclasses
                await self._perform_login(page)
                break
    
    async def _perform_login(self, page: Page) -> None:
        """Perform site-specific login. Override in subclasses.
        
        Args:
            page: Playwright page object
            
        Raises:
            AuthFailure: If login fails
        """
        raise NotImplementedError("Subclasses must implement _perform_login method")
    
    async def crawl(self) -> dict:
        """Main crawling method. Override in subclasses.
        
        Returns:
            Dictionary containing crawled data
        """
        raise NotImplementedError("Subclasses must implement crawl method")
    
    async def setup(self, browser: Browser) -> None:
        """Setup the crawler with a browser instance.
        
        Args:
            browser: Playwright browser instance
        """
        self.browser = browser
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Override in subclasses if needed
        pass 