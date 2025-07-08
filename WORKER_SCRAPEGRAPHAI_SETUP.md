# Worker ScrapegraphAI Setup Guide

This guide explains how to configure HoistScout workers to use ScrapegraphAI with Google Gemini for advanced tender scraping.

## Prerequisites

1. Docker and Docker Compose installed
2. Google Cloud account with Gemini API access

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the generated API key

## Configuration Steps

### 1. Create Environment File

Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Configure Gemini

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your-api-key-here
USE_GEMINI=true
```

### 3. Build and Run with ScrapegraphAI

```bash
# Build the containers with the updated Dockerfiles
docker-compose -f docker-compose.hoistscout.yml build

# Start the services
docker-compose -f docker-compose.hoistscout.yml up -d
```

## Verify Installation

Check if ScrapegraphAI is properly installed in the worker:

```bash
# Check worker logs
docker logs hoistscout-worker

# Verify ScrapegraphAI installation
docker exec hoistscout-worker python -c "import scrapegraphai; print('ScrapegraphAI version:', scrapegraphai.__version__)"
```

## Architecture

The worker uses the following scraper priority:

1. **BulletproofTenderScraper with Gemini** (when `USE_GEMINI=true` and API key is set)
   - Uses ScrapegraphAI for intelligent content extraction
   - Powered by Google's Gemini model
   - Best for complex tender websites

2. **BulletproofTenderScraper with Ollama** (when Ollama is available)
   - Uses ScrapegraphAI with local Ollama models
   - No API costs but requires more resources

3. **OllamaScraper** (fallback when ScrapegraphAI is not available)
   - Direct LLM extraction without ScrapegraphAI
   - Less sophisticated but still functional

4. **DemoScraper** (last resort)
   - Basic scraping for testing purposes

## Troubleshooting

### ScrapegraphAI Import Error

If you see import errors for ScrapegraphAI:

1. Ensure the worker Dockerfile includes the AI extra:
   ```dockerfile
   RUN poetry install --no-interaction --no-ansi -E ai
   ```

2. Rebuild the worker container:
   ```bash
   docker-compose -f docker-compose.hoistscout.yml build worker --no-cache
   ```

### Gemini API Errors

1. Verify your API key is valid
2. Check API quotas in Google Cloud Console
3. Ensure the `USE_GEMINI` flag is set to `true`

### Worker Not Processing Jobs

1. Check Redis connectivity:
   ```bash
   docker exec hoistscout-worker redis-cli -h hoistscout-redis ping
   ```

2. Verify worker is listening to correct queues:
   ```bash
   docker logs hoistscout-worker | grep "Listening"
   ```

## Performance Considerations

- ScrapegraphAI with Gemini provides the best extraction quality
- API costs apply when using Gemini (check Google's pricing)
- For high-volume scraping, consider using Ollama for cost efficiency
- The worker automatically falls back to simpler scrapers if ScrapegraphAI is unavailable