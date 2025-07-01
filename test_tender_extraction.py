#!/usr/bin/env python3
"""
Test tender extraction with correct selectors for Victorian Government Tenders
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import pandas as pd
import os

async def extract_tenders():
    """Extract tender data from Victorian Government Tenders"""
    
    print("🔍 Testing Tender Extraction from Victorian Government Tenders")
    print("=" * 80)
    
    results = {
        'success': False,
        'tenders': [],
        'timestamp': datetime.utcnow().isoformat(),
        'error': None
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = 'https://www.tenders.vic.gov.au/tender/search?preset=open'
            print(f"Navigating to: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Extract tender data from the table
            tenders = await page.evaluate("""
                () => {
                    const tenderData = [];
                    
                    // Find all tender rows in the table
                    const rows = document.querySelectorAll('#tenderTable-249237 tbody tr, .list tbody tr');
                    
                    rows.forEach((row) => {
                        // Skip header rows
                        if (row.querySelector('th')) return;
                        
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 3) {
                            const tender = {
                                scraped_at: new Date().toISOString()
                            };
                            
                            // First cell - RFx Number and Status
                            const firstCell = cells[0];
                            const rfxLink = firstCell.querySelector('a');
                            if (rfxLink) {
                                tender.rfx_number = rfxLink.textContent.trim();
                                tender.url = rfxLink.href;
                            }
                            
                            // Extract status
                            const statusText = firstCell.textContent;
                            if (statusText.includes('Open')) {
                                tender.status = 'Open';
                            } else if (statusText.includes('Closed')) {
                                tender.status = 'Closed';
                            }
                            
                            // Extract type (EOI, RFQ, etc.)
                            if (statusText.includes('Expression of Interest')) {
                                tender.type = 'Expression of Interest';
                            } else if (statusText.includes('Request for Tender')) {
                                tender.type = 'Request for Tender';
                            } else if (statusText.includes('Request for Quotation')) {
                                tender.type = 'Request for Quotation';
                            }
                            
                            // Second cell - Details
                            const detailsCell = cells[1];
                            const titleLink = detailsCell.querySelector('a');
                            if (titleLink) {
                                tender.title = titleLink.textContent.trim();
                                tender.details_url = titleLink.href;
                            }
                            
                            // Extract issued by
                            const issuedByMatch = detailsCell.textContent.match(/Issued by: ([^\\n]+)/);
                            if (issuedByMatch) {
                                tender.issued_by = issuedByMatch[1].trim();
                            }
                            
                            // Extract UNSPSC
                            const unspscMatch = detailsCell.textContent.match(/UNSPSC: ([^\\n]+)/);
                            if (unspscMatch) {
                                tender.unspsc = unspscMatch[1].trim();
                            }
                            
                            // Third cell - Dates
                            const datesCell = cells[2];
                            const datesText = datesCell.textContent;
                            
                            // Extract opened date
                            const openedMatch = datesText.match(/Opened\\s+([^\\n]+)/);
                            if (openedMatch) {
                                tender.opened_date = openedMatch[1].trim();
                            }
                            
                            // Extract closing date
                            const closingMatch = datesText.match(/Closing\\s+([^\\n]+)/);
                            if (closingMatch) {
                                tender.closing_date = closingMatch[1].trim();
                            }
                            
                            // Only add if we have meaningful data
                            if (tender.rfx_number || tender.title) {
                                tenderData.push(tender);
                            }
                        }
                    });
                    
                    return tenderData;
                }
            """)
            
            results['tenders'] = tenders
            results['success'] = len(tenders) > 0
            results['total_found'] = len(tenders)
            
            print(f"\n✅ Extracted {len(tenders)} tenders")
            
            # Display sample data
            if tenders:
                print("\n📋 Sample Tender Data:")
                for i, tender in enumerate(tenders[:3], 1):
                    print(f"\n{i}. RFx Number: {tender.get('rfx_number', 'N/A')}")
                    print(f"   Title: {tender.get('title', 'N/A')[:80]}...")
                    print(f"   Status: {tender.get('status', 'N/A')} | Type: {tender.get('type', 'N/A')}")
                    print(f"   Issued by: {tender.get('issued_by', 'N/A')}")
                    print(f"   Closing: {tender.get('closing_date', 'N/A')}")
            
            # Save results
            os.makedirs('extracted_data', exist_ok=True)
            
            # Save to JSON
            json_file = f'extracted_data/tenders_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 JSON saved to: {json_file}")
            
            # Save to Excel
            if tenders:
                excel_file = f'extracted_data/tenders_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
                df = pd.DataFrame(tenders)
                
                # Reorder columns for better readability
                column_order = ['rfx_number', 'title', 'status', 'type', 'issued_by', 
                              'opened_date', 'closing_date', 'unspsc', 'url', 'details_url', 'scraped_at']
                existing_columns = [col for col in column_order if col in df.columns]
                df = df[existing_columns]
                
                df.to_excel(excel_file, index=False)
                print(f"📊 Excel saved to: {excel_file}")
                
                # Show data quality metrics
                print(f"\n📈 Data Quality Metrics:")
                print(f"   Total records: {len(df)}")
                print(f"   Records with title: {df['title'].notna().sum()} ({df['title'].notna().mean()*100:.1f}%)")
                print(f"   Records with closing date: {df['closing_date'].notna().sum()} ({df['closing_date'].notna().mean()*100:.1f}%)")
                print(f"   Records with issuer: {df['issued_by'].notna().sum()} ({df['issued_by'].notna().mean()*100:.1f}%)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            results['error'] = str(e)
            
        finally:
            await browser.close()
    
    print("\n" + "=" * 80)
    print("✅ Extraction test completed")
    
    return results


if __name__ == "__main__":
    asyncio.run(extract_tenders())