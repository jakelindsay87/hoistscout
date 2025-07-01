#!/usr/bin/env python3
"""
Debug script to understand the page structure of Victorian Tenders
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def debug_page_structure():
    """Debug the page to understand its structure"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        page = await browser.new_page()
        
        try:
            url = 'https://www.tenders.vic.gov.au/tender/search?preset=open'
            print(f"Navigating to: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(10000)  # Wait 10 seconds for page to fully load
            
            # Get page info
            current_url = page.url
            title = await page.title()
            
            print(f"\nPage loaded:")
            print(f"  Current URL: {current_url}")
            print(f"  Title: {title}")
            
            # Take screenshot
            await page.screenshot(path='debug_page.png', full_page=True)
            print(f"\nScreenshot saved: debug_page.png")
            
            # Try to find any content that looks like tenders
            page_data = await page.evaluate("""
                () => {
                    const data = {
                        forms: document.querySelectorAll('form').length,
                        tables: document.querySelectorAll('table').length,
                        links: document.querySelectorAll('a').length,
                        divs_with_tender: document.querySelectorAll('div[class*="tender"]').length,
                        divs_with_result: document.querySelectorAll('div[class*="result"]').length,
                        all_text_content: document.body.innerText.substring(0, 1000),
                        interesting_elements: []
                    };
                    
                    // Look for elements that might contain tender data
                    const selectors = [
                        'table',
                        '.results',
                        '.search-results',
                        '[class*="tender"]',
                        '[class*="opportunity"]',
                        '[class*="listing"]',
                        '[class*="item"]',
                        'article',
                        'section'
                    ];
                    
                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            data.interesting_elements.push({
                                selector: selector,
                                count: elements.length,
                                sample_html: elements[0].outerHTML.substring(0, 200)
                            });
                        }
                    });
                    
                    return data;
                }
            """)
            
            print(f"\nPage analysis:")
            print(f"  Forms: {page_data['forms']}")
            print(f"  Tables: {page_data['tables']}")
            print(f"  Links: {page_data['links']}")
            print(f"  Divs with 'tender': {page_data['divs_with_tender']}")
            print(f"  Divs with 'result': {page_data['divs_with_result']}")
            
            print(f"\nInteresting elements found:")
            for elem in page_data['interesting_elements']:
                print(f"  - {elem['selector']}: {elem['count']} found")
                print(f"    Sample: {elem['sample_html'][:100]}...")
            
            print(f"\nFirst 1000 chars of page text:")
            print(page_data['all_text_content'])
            
            # Save full page HTML
            html = await page.content()
            with open('debug_page_full.html', 'w') as f:
                f.write(html)
            print(f"\nFull HTML saved to: debug_page_full.html")
            
            # Save analysis data
            with open('debug_analysis.json', 'w') as f:
                json.dump(page_data, f, indent=2)
            print(f"Analysis data saved to: debug_analysis.json")
            
            print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\nError: {e}")
            await page.screenshot(path='debug_error.png')
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page_structure())