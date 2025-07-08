#!/usr/bin/env python3
"""
Test script for Google Gemini integration with ScrapeGraphAI
"""
import asyncio
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Check if Gemini is configured
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY not set in .env file")
    print("Please add: GEMINI_API_KEY=your-api-key-here")
    exit(1)

if os.getenv("USE_GEMINI", "false").lower() != "true":
    print("❌ USE_GEMINI not set to true in .env file")
    print("Please add: USE_GEMINI=true")
    exit(1)


async def test_gemini_extraction():
    """Test Gemini extraction with a real website"""
    print("🚀 Testing Google Gemini integration with HoistScout...")
    print(f"Using model: {os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')}")
    
    # Import after env check
    from app.core.scraper import BulletproofTenderScraper, SCRAPEGRAPH_AVAILABLE
    from app.models.website import WebsiteConfig
    
    if not SCRAPEGRAPH_AVAILABLE:
        print("❌ ScrapeGraphAI not installed")
        print("Run: pip install scrapegraphai")
        return
    
    # Create test website config
    website = WebsiteConfig(
        id=1,
        name="Test - Tenders.gov.au",
        url="https://www.tenders.gov.au",
        is_active=True,
        scrape_frequency="daily",
        selectors={}
    )
    
    # Initialize scraper
    print("\n📊 Initializing BulletproofTenderScraper with Gemini...")
    scraper = BulletproofTenderScraper()
    
    if not scraper.scraper:
        print("❌ Failed to initialize scraper - check Gemini configuration")
        return
    
    print("✅ Scraper initialized successfully!")
    
    # Test extraction
    print(f"\n🔍 Extracting tenders from {website.url}...")
    print("This may take 30-60 seconds...")
    
    try:
        result = await scraper.scrape_website(website)
        
        if result.success:
            print(f"\n✅ Extraction successful!")
            print(f"Found {result.total_found} opportunities")
            
            # Display first 3 results
            for i, opp in enumerate(result.opportunities[:3]):
                print(f"\n--- Opportunity {i+1} ---")
                print(f"Title: {opp.get('title', 'N/A')}")
                print(f"Description: {opp.get('description', 'N/A')[:200]}...")
                print(f"Deadline: {opp.get('deadline', 'N/A')}")
                print(f"Value: {opp.get('value', 'N/A')}")
                print(f"Reference: {opp.get('reference_number', 'N/A')}")
                
            if result.total_found > 3:
                print(f"\n... and {result.total_found - 3} more opportunities")
                
        else:
            print(f"\n❌ Extraction failed: {result.error_message}")
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        logger.exception("Extraction error")
        
    print("\n✅ Test complete!")
    
    # Test API limits
    print("\n📊 Gemini API Free Tier Limits:")
    print("- 15 requests per minute")
    print("- 1,500 requests per day")
    print("- 1 million tokens per minute")
    print("\nMonitor usage at: https://aistudio.google.com/")


if __name__ == "__main__":
    asyncio.run(test_gemini_extraction())