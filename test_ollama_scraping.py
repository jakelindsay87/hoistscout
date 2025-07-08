#!/usr/bin/env python3
"""
Test Ollama-powered scraping locally
"""
import asyncio
import httpx
from datetime import datetime
import json

async def test_ollama_connection():
    """Test if Ollama is available"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is running")
                tags = response.json()
                models = [tag['name'] for tag in tags.get('models', [])]
                if models:
                    print(f"   Available models: {', '.join(models)}")
                else:
                    print("   ⚠️  No models installed yet")
                return True
            else:
                print("❌ Ollama returned status:", response.status_code)
                return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running on http://localhost:11434")
        return False

async def test_llm_extraction():
    """Test LLM extraction with sample content"""
    
    # Sample tender content
    sample_html = """
    <html>
    <body>
        <div class="tender-listing">
            <h2>ICT Services Panel Refresh</h2>
            <p>The Department of Digital Government seeks to establish a new panel of ICT service providers.</p>
            <div class="details">
                <span>Reference: DGS-2025-ICT-001</span>
                <span>Closing: 15 December 2025, 2:00 PM AEDT</span>
                <span>Value: $5,000,000 - $10,000,000</span>
            </div>
        </div>
        
        <div class="tender-listing">
            <h2>Cloud Migration Services</h2>
            <p>Seeking experienced providers for government cloud migration project.</p>
            <ul>
                <li>ATM Number: ATM-2025-CLOUD-002</li>
                <li>Deadline: 30 November 2025</li>
                <li>Budget: Up to $2.5 million AUD</li>
                <li>Location: Canberra, ACT</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    prompt = """Extract all tender opportunities from this webpage.
For each tender, extract: title, description, reference_number, deadline, value, currency, location.
Return as JSON array.

CONTENT:
""" + sample_html + """

Return ONLY a JSON array, no explanations."""

    try:
        async with httpx.AsyncClient() as client:
            print("\n🤖 Sending content to Ollama for extraction...")
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '')
                
                print("\n📄 LLM Response:")
                print("-" * 50)
                print(llm_response[:500] + "..." if len(llm_response) > 500 else llm_response)
                print("-" * 50)
                
                # Try to parse JSON
                import re
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    opportunities = json.loads(json_match.group())
                    print(f"\n✅ Successfully extracted {len(opportunities)} opportunities:")
                    for i, opp in enumerate(opportunities, 1):
                        print(f"\n[{i}] {opp.get('title', 'No title')}")
                        print(f"    Reference: {opp.get('reference_number', 'N/A')}")
                        print(f"    Value: ${opp.get('value', 0):,.2f} {opp.get('currency', 'AUD')}")
                        print(f"    Deadline: {opp.get('deadline', 'N/A')}")
                else:
                    print("\n⚠️  No valid JSON found in response")
                    
            else:
                print(f"\n❌ Ollama error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")

async def test_real_website():
    """Test extraction from a real website"""
    url = "https://www.tenders.gov.au/atm"
    
    print(f"\n🌐 Testing extraction from: {url}")
    
    try:
        # First fetch the page
        async with httpx.AsyncClient() as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Fetched page successfully ({len(response.text)} bytes)")
                
                # Extract text content (limit for demo)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text(separator='\n', strip=True)[:5000]
                
                # Create extraction prompt
                prompt = f"""Extract tender/grant opportunities from this government website.
For each opportunity, extract: title, description, reference_number, deadline, value, currency, categories, location.
Return as JSON array.

URL: {url}

CONTENT:
{text}

Return ONLY a JSON array of opportunities found."""

                # Send to Ollama
                print("\n🤖 Sending to Ollama for extraction...")
                
                async with httpx.AsyncClient() as ollama_client:
                    ollama_response = await ollama_client.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama3.1",
                            "prompt": prompt,
                            "stream": False,
                            "temperature": 0.1,
                        },
                        timeout=90
                    )
                    
                    if ollama_response.status_code == 200:
                        result = ollama_response.json()
                        print("\n✅ Received response from Ollama")
                        
                        # Parse and display results
                        import re
                        llm_text = result.get('response', '')
                        json_match = re.search(r'\[.*\]', llm_text, re.DOTALL)
                        
                        if json_match:
                            opportunities = json.loads(json_match.group())
                            print(f"\n📊 Extracted {len(opportunities)} opportunities from {url}")
                            
                            for opp in opportunities[:3]:  # Show first 3
                                print(f"\n- {opp.get('title', 'No title')}")
                                if opp.get('description'):
                                    print(f"  {opp['description'][:100]}...")
                        else:
                            print("\n⚠️  No opportunities extracted")
                            print("Response preview:", llm_text[:200])
                    else:
                        print(f"\n❌ Ollama error: {ollama_response.status_code}")
            else:
                print(f"❌ Failed to fetch {url}: {response.status_code}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def main():
    print("=" * 60)
    print("HoistScout - Ollama Scraping Test")
    print("=" * 60)
    
    # Test 1: Check Ollama connection
    print("\n1. Testing Ollama Connection")
    print("-" * 30)
    if not await test_ollama_connection():
        print("\n⚠️  Please make sure Ollama is running:")
        print("   docker run -d -p 11434:11434 --name ollama ollama/ollama")
        print("   docker exec ollama ollama pull llama3.1")
        return
    
    # Test 2: Test LLM extraction with sample content  
    print("\n\n2. Testing LLM Extraction with Sample Content")
    print("-" * 30)
    await test_llm_extraction()
    
    # Test 3: Test with real website
    print("\n\n3. Testing Real Website Extraction")
    print("-" * 30)
    await test_real_website()
    
    print("\n\n✅ Tests completed!")
    print("\nTo use this with HoistScout:")
    print("1. Set OLLAMA_BASE_URL=http://localhost:11434 in your environment")
    print("2. Deploy the updated worker code")
    print("3. Trigger a scraping job for tenders.gov.au")

if __name__ == "__main__":
    asyncio.run(main())