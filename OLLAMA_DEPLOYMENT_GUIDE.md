# Ollama Deployment Guide for HoistScout

## Overview
This guide explains how to deploy HoistScout with Ollama for AI-powered tender extraction using ScrapeGraphAI.

## Architecture
- **Ollama Service**: Runs the LLM (llama3.1) for intelligent content extraction
- **Worker Service**: Uses Ollama via API to extract structured data from websites
- **ScrapeGraphAI**: Optional - falls back to direct Ollama integration if not available

## Deployment Options

### Option 1: Local Development with Docker Compose

1. **Start all services including Ollama:**
```bash
docker-compose -f docker-compose.hoistscout.yml up -d
```

2. **Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

3. **The worker will automatically use Ollama for extraction**

### Option 2: Render.com Deployment with External Ollama

Since Render doesn't support running Ollama directly, you need to:

1. **Set up Ollama on a separate server** (e.g., DigitalOcean, AWS EC2):
```bash
# On your server
docker run -d -p 11434:11434 --name ollama ollama/ollama:latest
docker exec ollama ollama pull llama3.1
```

2. **Update Render environment variables:**
```
OLLAMA_BASE_URL=http://your-ollama-server:11434
OLLAMA_MODEL=llama3.1
```

### Option 3: Use Ollama Cloud API (when available)

Update environment variables to point to Ollama's cloud API endpoint.

## Testing Ollama Integration

1. **Run the test script locally:**
```bash
chmod +x setup_ollama_local.sh
./setup_ollama_local.sh

python3 test_ollama_scraping.py
```

2. **Expected output:**
- Ollama connection test passes
- Sample content extraction shows structured JSON
- Real website extraction returns actual tenders

## Environment Variables

Add these to your `.env` file or Render settings:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434  # For local dev
OLLAMA_MODEL=llama3.1

# Optional: ScrapeGraphAI will use these if available
SCRAPEGRAPH_API_KEY=your-key-if-using-cloud
```

## How It Works

1. **Worker receives scraping job**
2. **Tries ScrapeGraphAI first** (if installed with `poetry install -E ai`)
3. **Falls back to OllamaScraper** if ScrapeGraphAI not available
4. **Falls back to DemoScraper** if Ollama not available
5. **Extracts structured data** using LLM prompts
6. **Saves to database** as Opportunity records

## Scraper Priority

```python
1. BulletproofTenderScraper (ScrapeGraphAI) - Most advanced
2. OllamaScraper (Direct Ollama) - Good extraction
3. DemoScraper (No AI) - Basic/demo data only
```

## LLM Extraction Features

The Ollama integration extracts:
- Tender titles and descriptions
- Reference numbers and deadlines
- Values and currencies
- Categories and locations
- Agencies and contact information
- Submission methods and requirements

## Monitoring

Check worker logs to see which scraper is being used:
```bash
# Local
docker logs hoistscout-worker

# Render
# Check logs in Render dashboard
```

## Troubleshooting

1. **"Ollama not available" errors:**
   - Ensure Ollama service is running
   - Check OLLAMA_BASE_URL is correct
   - Verify network connectivity

2. **Poor extraction quality:**
   - Try different models (llama3.1, mistral, etc.)
   - Adjust temperature in scraper_with_ollama.py
   - Improve prompts for specific sites

3. **Timeout errors:**
   - Increase timeout in httpx calls
   - Use smaller model for faster inference
   - Limit content size sent to LLM

## Production Recommendations

1. **Use dedicated Ollama server** with GPU for better performance
2. **Cache extraction results** to avoid re-processing
3. **Monitor token usage** and costs if using cloud API
4. **Set up proper error handling** and fallbacks
5. **Use specific prompts** per website for better accuracy