#!/usr/bin/env python3
"""
Test with proper wait conditions
"""

import asyncio
from playwright.async_api import async_playwright

async def test_with_proper_wait():
    """Test with proper wait for dynamic content"""
    
    print("Testing with proper wait conditions...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        page = await browser.new_page()
        
        try:
            url = 'https://www.tenders.vic.gov.au/tender/search?preset=open'
            print(f"Navigating to: {url}")
            
            # Navigate and wait for specific element
            await page.goto(url)
            
            # Wait for tender rows to appear
            print("Waiting for tender data to load...")
            
            try:
                # Wait for any of these selectors
                await page.wait_for_selector('tr[id^="tenderRow"]', timeout=30000)
                print("✅ Tender rows found!")
            except:
                print("❌ No tender rows found after 30 seconds")
            
            # Count elements
            count = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('tr[id^="tenderRow"]');
                    return rows.length;
                }
            """)
            
            print(f"Found {count} tender rows")
            
            # Check page content
            content = await page.evaluate("""
                () => {
                    return {
                        url: window.location.href,
                        title: document.title,
                        hasTable: !!document.querySelector('table'),
                        bodyText: document.body.innerText.substring(0, 500)
                    };
                }
            """)
            
            print(f"\nPage info:")
            print(f"  URL: {content['url']}")
            print(f"  Title: {content['title']}")
            print(f"  Has table: {content['hasTable']}")
            print(f"\nFirst 500 chars of body text:")
            print(content['bodyText'])
            
            print("\n⏸️  Keeping browser open for 20 seconds...")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_with_proper_wait())