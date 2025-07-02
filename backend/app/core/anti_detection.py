"""
Anti-detection system for bulletproof scraping.
"""

import random
import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
from loguru import logger

from fake_useragent import UserAgent
from twocaptcha import TwoCaptcha
import undetected_chromedriver as uc
from asyncio_throttle import Throttler


@dataclass
class BrowserConfig:
    """Browser configuration for anti-detection."""
    user_agent: str
    viewport: Dict[str, int]
    proxy: Optional[str]
    headers: Dict[str, str]
    cookies: Optional[List[Dict]]


class ProxyRotator:
    """Manages proxy rotation with health checking."""
    
    def __init__(self, proxy_list: List[str]):
        self.proxies = proxy_list
        self.healthy_proxies = set(proxy_list)
        self.failed_proxies = set()
        
    async def get_proxy(self) -> Optional[str]:
        """Get a healthy proxy."""
        if not self.healthy_proxies:
            # Reset if all proxies failed
            self.healthy_proxies = set(self.proxies)
            self.failed_proxies.clear()
            
        if self.healthy_proxies:
            return random.choice(list(self.healthy_proxies))
        return None
    
    def mark_failed(self, proxy: str):
        """Mark a proxy as failed."""
        self.healthy_proxies.discard(proxy)
        self.failed_proxies.add(proxy)
        logger.warning(f"Proxy marked as failed: {proxy}")
    
    def mark_success(self, proxy: str):
        """Mark a proxy as successful."""
        if proxy in self.failed_proxies:
            self.failed_proxies.remove(proxy)
            self.healthy_proxies.add(proxy)


class DomainThrottler:
    """Rate limiting per domain to avoid detection."""
    
    def __init__(self):
        self.throttlers = {}
        self.default_rate = 2  # requests per second
        
    def get_throttler(self, domain: str) -> Throttler:
        """Get or create throttler for domain."""
        if domain not in self.throttlers:
            # Different rates for different domains
            if "gov" in domain:
                rate = 1  # Be extra careful with government sites
            else:
                rate = self.default_rate
                
            self.throttlers[domain] = Throttler(
                rate_limit=rate,
                period=1.0
            )
        
        return self.throttlers[domain]
    
    async def throttle(self, url: str):
        """Apply rate limiting for URL."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        throttler = self.get_throttler(domain)
        async with throttler:
            pass  # Rate limit applied


class CaptchaSolver:
    """Handles CAPTCHA solving with 2captcha service."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.solver = TwoCaptcha(api_key) if api_key else None
        
    async def solve_recaptcha(
        self, 
        site_key: str, 
        page_url: str
    ) -> Optional[str]:
        """Solve reCAPTCHA v2."""
        if not self.solver:
            logger.error("2captcha API key not configured")
            return None
            
        try:
            result = await asyncio.to_thread(
                self.solver.recaptcha,
                sitekey=site_key,
                url=page_url
            )
            return result['code']
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None
    
    async def solve_image_captcha(
        self, 
        image_path: str
    ) -> Optional[str]:
        """Solve image-based CAPTCHA."""
        if not self.solver:
            return None
            
        try:
            result = await asyncio.to_thread(
                self.solver.normal,
                image_path
            )
            return result['code']
        except Exception as e:
            logger.error(f"Image CAPTCHA solving failed: {e}")
            return None


class FlareSolverrClient:
    """Client for FlareSolverr to bypass Cloudflare."""
    
    def __init__(self, api_url: Optional[str] = None):
        from ..config import get_settings
        settings = get_settings()
        self.api_url = api_url or settings.flaresolverr_url
        
    async def solve_challenge(self, url: str) -> Optional[Dict]:
        """Solve Cloudflare challenge."""
        if not self.api_url:
            logger.warning("FlareSolverr not configured - skipping Cloudflare bypass")
            return None
            
        import httpx
        
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v1",
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "cookies": data.get("solution", {}).get("cookies", []),
                        "user_agent": data.get("solution", {}).get("userAgent"),
                        "html": data.get("solution", {}).get("response")
                    }
        except Exception as e:
            logger.error(f"FlareSolverr failed: {e}")
            
        return None


class AntiDetectionManager:
    """
    Manages all anti-detection strategies.
    """
    
    def __init__(self):
        self.ua = UserAgent()
        self.proxy_rotator = ProxyRotator(self._load_proxies())
        self.domain_throttler = DomainThrottler()
        self.captcha_solver = CaptchaSolver(self._load_2captcha_key())
        self.flaresolverr = FlareSolverrClient()
        
    def _load_proxies(self) -> List[str]:
        """Load proxy list from configuration."""
        # In production, load from database or config
        return []
    
    def _load_2captcha_key(self) -> Optional[str]:
        """Load 2captcha API key."""
        import os
        return os.getenv("TWO_CAPTCHA_API_KEY")
    
    async def prepare_browser(self, url: str) -> BrowserConfig:
        """Prepare browser configuration with anti-detection measures."""
        # Apply rate limiting
        await self.domain_throttler.throttle(url)
        
        # Get random user agent
        user_agent = self.ua.random
        
        # Random viewport size
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864}
        ]
        viewport = random.choice(viewports)
        
        # Get proxy if available
        proxy = await self.proxy_rotator.get_proxy()
        
        # Realistic headers
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        return BrowserConfig(
            user_agent=user_agent,
            viewport=viewport,
            proxy=proxy,
            headers=headers,
            cookies=None
        )
    
    def create_stealth_driver(self) -> uc.Chrome:
        """Create undetected Chrome driver instance."""
        options = uc.ChromeOptions()
        
        # Stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-web-security')
        
        # Random window size
        viewport = random.choice([
            (1920, 1080), (1366, 768), (1440, 900)
        ])
        options.add_argument(f'--window-size={viewport[0]},{viewport[1]}')
        
        # Create driver
        driver = uc.Chrome(options=options)
        
        # Additional stealth measures
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
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
            '''
        })
        
        return driver
    
    async def handle_cloudflare(self, url: str) -> Optional[Dict]:
        """Handle Cloudflare protection."""
        logger.info(f"Attempting to bypass Cloudflare for {url}")
        result = await self.flaresolverr.solve_challenge(url)
        
        if result:
            logger.success(f"Cloudflare bypass successful for {url}")
        else:
            logger.error(f"Cloudflare bypass failed for {url}")
            
        return result
    
    async def solve_captcha(
        self, 
        captcha_type: str,
        **kwargs
    ) -> Optional[str]:
        """Solve various types of CAPTCHAs."""
        if captcha_type == "recaptcha":
            return await self.captcha_solver.solve_recaptcha(
                kwargs.get("site_key"),
                kwargs.get("page_url")
            )
        elif captcha_type == "image":
            return await self.captcha_solver.solve_image_captcha(
                kwargs.get("image_path")
            )
        else:
            logger.warning(f"Unknown CAPTCHA type: {captcha_type}")
            return None