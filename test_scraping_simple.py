#!/usr/bin/env python3
"""
Simple scraping test without authentication to test basic functionality
"""

import asyncio
from playwright.async_api import async_playwright
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleScrapingTest:
    """Test basic scraping functionality"""
    
    def __init__(self):
        self.logger = logger
        self.base_url = 'https://www.tenders.vic.gov.au'
        
    async def test_public_tender_access(self) -> dict:
        """Test accessing public tender listings"""
        
        test_result = {
            'success': False,
            'tenders_found': 0,
            'sample_tenders': [],
            'timestamp': datetime.utcnow().isoformat(),
            'error': None
        }
        
        async with async_playwright() as p:
            self.logger.info("Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Try to access public tender search
                search_url = f"{self.base_url}/tender/search?preset=open"
                self.logger.info(f"Navigating to public tenders: {search_url}")
                
                await page.goto(search_url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                await page.wait_for_timeout(5000)
                
                # Take screenshot
                await page.screenshot(path='public_tenders.png')
                self.logger.info("Screenshot saved: public_tenders.png")
                
                # Try different selectors for tender listings
                selectors_to_try = [
                    'a[href*="/tender/view/"]',
                    'a[href*="/tender/"]',
                    '.tender-item',
                    '.opportunity-item',
                    '.search-result',
                    'table tr a',
                    '[class*="tender"]',
                    '[class*="opportunity"]'
                ]
                
                tender_links = []
                for selector in selectors_to_try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        tender_links = elements
                        break
                
                if tender_links:
                    test_result['tenders_found'] = len(tender_links)
                    test_result['success'] = True
                    
                    # Get sample tender info
                    for i, link in enumerate(tender_links[:3]):  # First 3 tenders
                        try:
                            href = await link.get_attribute('href')
                            text = await link.text_content()
                            
                            if href and text:
                                test_result['sample_tenders'].append({
                                    'title': text.strip(),
                                    'url': href if href.startswith('http') else f"{self.base_url}{href}"
                                })
                        except:
                            pass
                    
                    self.logger.info(f"✅ Found {test_result['tenders_found']} tenders")
                else:
                    self.logger.warning("Could not find any tender listings")
                    
                    # Save page HTML for debugging
                    page_content = await page.content()
                    with open('public_tenders.html', 'w') as f:
                        f.write(page_content)
                    self.logger.info("Saved page HTML to public_tenders.html for debugging")
                    
                    # Check if we need authentication
                    if 'login' in page.url.lower() or 'signin' in page.url.lower():
                        test_result['error'] = "Redirected to login page - authentication may be required"
                    else:
                        test_result['error'] = "Could not find tender listings on page"
                    
            except Exception as e:
                self.logger.error(f"Scraping error: {e}")
                test_result['error'] = str(e)
                
            finally:
                await browser.close()
                
        return test_result


async def main():
    """Run scraping test"""
    
    print("🔍 Testing Public Tender Access on Victorian Government Tenders")
    print("=" * 60)
    print(f"URL: https://www.tenders.vic.gov.au/tender/search?preset=open")
    print("=" * 60)
    
    scraper_test = SimpleScrapingTest()
    result = await scraper_test.test_public_tender_access()
    
    print(f"\n📊 Results:")
    print(f"  Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print(f"  Tenders Found: {result['tenders_found']}")
    
    if result['sample_tenders']:
        print(f"\n📋 Sample Tenders:")
        for i, tender in enumerate(result['sample_tenders'], 1):
            print(f"  {i}. {tender['title'][:60]}...")
            print(f"     URL: {tender['url']}")
    
    if result['error']:
        print(f"\n❌ Error: {result['error']}")
    
    print(f"\n📸 Screenshot saved: public_tenders.png")
    
    if not result['success']:
        print(f"💡 Debug info saved to public_tenders.html")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Results saved to test_results.json")
    
    print("\n" + "=" * 60)
    
    return result


if __name__ == "__main__":
    asyncio.run(main())