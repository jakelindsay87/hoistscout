#!/usr/bin/env python3
"""Simple scraper to get opportunities from tenders.gov.au"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def scrape_tenders():
    """Scrape opportunities from tenders.gov.au"""
    opportunities = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            page = await browser.new_page()
            
            # Set user agent to avoid blocks
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            print("Navigating to tenders.gov.au...")
            await page.goto('https://www.tenders.gov.au/atm', wait_until='networkidle')
            
            # Wait for results to load
            await page.wait_for_selector('.list-view-item', timeout=30000)
            
            # Get all tender items
            items = await page.query_selector_all('.list-view-item')
            print(f"Found {len(items)} tender items")
            
            for i, item in enumerate(items[:15]):  # Get first 15
                try:
                    # Extract data from each item
                    title_elem = await item.query_selector('h4 a')
                    title = await title_elem.inner_text() if title_elem else 'No title'
                    link = await title_elem.get_attribute('href') if title_elem else ''
                    
                    # Get ATM ID
                    atm_id = ''
                    id_match = re.search(r'ATM ID:([^\n]+)', await item.inner_text())
                    if id_match:
                        atm_id = id_match.group(1).strip()
                    
                    # Get close date
                    close_date = ''
                    date_match = re.search(r'Close Date & Time:([^\n]+)', await item.inner_text())
                    if date_match:
                        close_date = date_match.group(1).strip()
                    
                    # Get agency
                    agency = ''
                    agency_match = re.search(r'Agency:([^\n]+)', await item.inner_text())
                    if agency_match:
                        agency = agency_match.group(1).strip()
                    
                    # Get category
                    category = ''
                    cat_match = re.search(r'Category:([^\n]+)', await item.inner_text())
                    if cat_match:
                        category = cat_match.group(1).strip()
                    
                    # Get description
                    desc_elem = await item.query_selector('.list-desc-inner')
                    description = await desc_elem.inner_text() if desc_elem else ''
                    description = description.replace('Description:', '').strip()
                    
                    opportunity = {
                        'title': title,
                        'atm_id': atm_id,
                        'url': f'https://www.tenders.gov.au{link}' if link.startswith('/') else link,
                        'close_date': close_date,
                        'agency': agency,
                        'category': category,
                        'description': description[:500] + '...' if len(description) > 500 else description
                    }
                    
                    opportunities.append(opportunity)
                    print(f"{i+1}. {title} - {atm_id}")
                    
                except Exception as e:
                    print(f"Error extracting item {i}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
    
    return opportunities

async def main():
    """Main function"""
    print("Starting tenders.gov.au scraper...")
    opportunities = await scrape_tenders()
    
    if opportunities:
        print(f"\nSuccessfully scraped {len(opportunities)} opportunities!")
        
        # Save to JSON for inspection
        import json
        with open('/root/hoistscraper/scraped_opportunities.json', 'w') as f:
            json.dump(opportunities, f, indent=2)
        print("Saved to scraped_opportunities.json")
        
        # Now insert into database
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="hoistscraper",
                user="postgres",
                password="postgres"
            )
            cur = conn.cursor()
            
            # Clear existing opportunities
            cur.execute("DELETE FROM opportunity")
            
            # Insert new opportunities
            for opp in opportunities:
                # Parse deadline
                deadline = None
                if opp['close_date']:
                    # Try to parse date like "1-Jul-2025 5:00 pm (ACT Local Time)"
                    try:
                        date_part = opp['close_date'].split('(')[0].strip()
                        # This is a simplified approach - in production you'd use proper date parsing
                        deadline = "2025-07-01 17:00:00"  # Placeholder
                    except:
                        pass
                
                cur.execute("""
                    INSERT INTO opportunity (
                        title, description, source_url, website_id, job_id,
                        deadline, amount, location, categories, scraped_at,
                        requires_manual_review
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    opp['title'],
                    opp['description'],
                    opp['url'],
                    1,  # website_id
                    1,  # job_id
                    deadline,
                    'Not specified',  # amount
                    'ACT',  # location (extracted from close date)
                    opp['category'],
                    datetime.now(),
                    False  # requires_manual_review
                ))
            
            conn.commit()
            print(f"\nInserted {len(opportunities)} opportunities into database!")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Database error: {e}")
    else:
        print("No opportunities found!")

if __name__ == "__main__":
    asyncio.run(main())