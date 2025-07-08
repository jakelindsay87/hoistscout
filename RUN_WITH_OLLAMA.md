# Running HoistScout with Ollama - Quick Start

## Step 1: Start Ollama
```bash
# Pull and run Ollama
docker run -d -p 11434:11434 --name ollama ollama/ollama:latest

# Pull the llama3.1 model (this takes a few minutes)
docker exec ollama ollama pull llama3.1

# Verify it's working
curl http://localhost:11434/api/tags
```

## Step 2: Run HoistScout with Ollama
```bash
# Set environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.1

# Option A: Use the new docker-compose
docker-compose -f docker-compose.hoistscout.yml up -d

# Option B: Run existing setup with env vars
docker-compose up -d
```

## Step 3: Test Extraction
```bash
# Run the test script
python3 test_ollama_scraping.py
```

## Step 4: Trigger Real Scraping

1. Access the UI at http://localhost:3000
2. Login with demo/demo123
3. Add tenders.gov.au if not already added
4. Click "Scrape Now" 
5. Monitor the job - it will use Ollama for extraction

## What You'll See

When Ollama is working properly, the extracted opportunities will have:
- Accurate titles extracted from the page
- Proper reference numbers
- Deadline dates in correct format
- Values and currencies identified
- Categories automatically determined
- High confidence scores (0.9+)

## Monitoring

Watch the worker logs to see Ollama in action:
```bash
docker logs -f hoistscout-worker
```

You'll see messages like:
- "Extracting opportunities from ... using Ollama"
- The actual LLM prompts and responses
- Extracted data being saved

## For Production (Render.com)

Since Render doesn't support running Ollama directly:

1. **Set up Ollama on a cloud server:**
   - DigitalOcean Droplet ($20/mo)
   - AWS EC2 instance
   - Any VPS with Docker

2. **Configure Render environment:**
   ```
   OLLAMA_BASE_URL=http://your-server-ip:11434
   OLLAMA_MODEL=llama3.1
   ```

3. **Ensure firewall allows port 11434**

4. **Redeploy the worker service**