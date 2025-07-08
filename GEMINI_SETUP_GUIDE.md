# Google Gemini API Setup Guide for HoistScout

## Overview
HoistScout now supports Google Gemini API for intelligent web scraping through ScrapeGraphAI. This provides cloud-based LLM extraction without needing local resources.

## Free Tier Limits
- **15 requests per minute**
- **1,500 requests per day**
- **1 million tokens per minute**
- **Free forever** in available countries

## Setup Steps

### 1. Get Your Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key
5. Copy the key (starts with `AIza...`)

### 2. Configure HoistScout

#### For Local Development
Create a `.env` file in the backend directory:
```bash
cd backend
cp .env.example .env
```

Add your Gemini API key:
```env
USE_GEMINI=true
GEMINI_API_KEY=AIza...your-key-here
GEMINI_MODEL=gemini-1.5-flash
```

#### For Render Deployment
1. Go to your Render dashboard
2. Navigate to your services:
   - `hoistscout-api` 
   - `hoistscout-worker`
3. For each service, go to Environment → Add Environment Variable:
   - `USE_GEMINI` = `true`
   - `GEMINI_API_KEY` = `AIza...your-key-here`
   - `GEMINI_MODEL` = `gemini-1.5-flash`

### 3. Remove/Disable Ollama Proxy
Since we're using Gemini, the Ollama proxy is no longer needed:
1. You can remove the `hoistscout-ollama` service from Render
2. Or leave it for future use if you want to switch back

## Testing the Integration

### Local Testing
```bash
cd backend
python test_gemini_extraction.py
```

### Production Testing
1. Login to HoistScout
2. Add a website (e.g., https://www.tenders.gov.au)
3. Click "Scrape Now"
4. Check the jobs page for results

## Expected Behavior
With Gemini configured, HoistScout will:
1. Use ScrapeGraphAI with Gemini for intelligent extraction
2. Extract real tender/grant data from websites
3. Parse titles, descriptions, deadlines, values, etc.
4. Return structured JSON data

## Troubleshooting

### "API key not valid" Error
- Double-check your API key is correct
- Ensure no extra spaces or quotes
- Try regenerating the key in Google AI Studio

### Rate Limit Errors
- Free tier: 15 requests/minute
- Implement delays between scrapes if needed
- Consider upgrading to paid tier for production

### No Results
- Check if the website is accessible
- Verify Gemini is enabled (`USE_GEMINI=true`)
- Check worker logs for errors

## Advantages Over Ollama
- ✅ No local GPU/CPU requirements
- ✅ Consistent cloud performance
- ✅ Easy deployment on Render
- ✅ Generous free tier
- ✅ Better extraction quality with Gemini 1.5

## Model Options
- `gemini-1.5-flash` (Recommended) - Fast, efficient
- `gemini-1.5-pro` - More capable but slower
- `gemini-1.0-pro` - Legacy, still supported

## Next Steps
1. Test extraction on various websites
2. Monitor usage in Google AI Studio dashboard
3. Adjust rate limiting if needed
4. Consider implementing caching for repeated extractions