# Deploy Ollama Proxy on Render - Step by Step

## Overview
Since Render doesn't support GPU instances needed for running Ollama directly, we use a lightweight proxy that can either:
1. Forward requests to an external Ollama instance
2. Provide intelligent mock responses for testing

## Step 1: Deploy the Ollama Proxy

### Option A: Via Render Dashboard

1. **Go to Render Dashboard** → New → Web Service
2. **Connect your GitHub repo** (jakelindsay87/hoistscout)
3. **Configure the service:**
   - Name: `hoistscout-ollama-proxy`
   - Environment: Docker
   - Dockerfile Path: `ollama-proxy/Dockerfile`
   - Docker Context Directory: `ollama-proxy`
   - Instance Type: Starter ($7/month)

4. **Add Environment Variables:**
   - `PORT`: 10000
   - `MOCK_MODE`: true (for testing)
   - `EXTERNAL_OLLAMA_URL`: (leave empty for now)

5. **Deploy!**

### Option B: Via Blueprint

Add this to your existing `render.yaml`:

```yaml
  - type: web
    name: hoistscout-ollama-proxy
    runtime: docker
    repo: https://github.com/jakelindsay87/hoistscout
    dockerfilePath: ollama-proxy/Dockerfile
    dockerContext: ollama-proxy
    envVars:
      - key: PORT
        value: 10000
      - key: MOCK_MODE
        value: "true"
    healthCheckPath: /health
    plan: starter
```

## Step 2: Update Worker Configuration

1. **Go to your hoistscout-worker service**
2. **Click Environment tab**
3. **Add these variables:**
   ```
   OLLAMA_BASE_URL=https://hoistscout-ollama-proxy.onrender.com
   OLLAMA_MODEL=llama3.1
   ```
4. **Save Changes** (worker will restart automatically)

## Step 3: Test the Setup

Run the test script:
```bash
python3 test_enhanced_extraction.py
```

You should see opportunities extracted with the mock data, including:
- Detailed financial information
- Eligibility requirements
- Assessment criteria
- Priority areas
- Contact details

## Step 4: Connect Real Ollama (Optional)

### Option A: Use a Cloud Ollama Provider

1. **Deploy Ollama on a GPU instance:**
   - DigitalOcean GPU Droplet
   - AWS EC2 with GPU
   - Vast.ai or RunPod.io (affordable GPU rentals)

2. **Update the proxy environment:**
   - Set `MOCK_MODE`: false
   - Set `EXTERNAL_OLLAMA_URL`: http://your-ollama-ip:11434

### Option B: Use Ollama API (when available)

When Ollama releases their cloud API:
1. Get API endpoint and key
2. Update proxy to use API authentication

## What You'll See

### With Mock Mode (Default)
- Realistic Australian tender data
- All enhanced fields populated
- Confidence scores of 0.95
- Immediate responses

### With Real Ollama
- Actual extraction from tenders.gov.au
- Dynamic field extraction
- Varied confidence scores
- 30-60 second processing time

## Monitoring

Check the logs:
1. **Proxy logs**: Shows requests and mode
2. **Worker logs**: Shows extraction method used
3. **API responses**: Include extraction_method field

## Cost Considerations

- **Ollama Proxy**: $7/month (Render Starter)
- **External Ollama**: 
  - DigitalOcean GPU: ~$90/month
  - Vast.ai: ~$0.30/hour when active
  - RunPod: ~$0.40/hour for RTX 3090

## Troubleshooting

1. **"No opportunities found"**
   - Check worker logs for errors
   - Verify OLLAMA_BASE_URL is set correctly
   - Ensure proxy is running

2. **"Demo data showing"**
   - This is normal in mock mode
   - Shows the extraction format
   - Switch to real Ollama for live data

3. **"Timeout errors"**
   - Increase timeout in scraper_with_ollama.py
   - Check Ollama server resources
   - Consider smaller model (mistral vs llama3.1)