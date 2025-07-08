# 🚨 CRITICAL: Set GEMINI_API_KEY in Render

The worker cannot process jobs until you manually set the GEMINI_API_KEY in Render's dashboard.

## Current Status
- ❌ 9 jobs stuck in "pending" status
- ❌ Worker cannot start without API key
- ✅ API and Frontend are running
- ✅ CI tests should now pass

## Required Actions

### 1. Set GEMINI_API_KEY in Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to **BOTH** services:
   - `hoistscout-api` 
   - `hoistscout-worker`

3. For **EACH** service:
   - Click on the service name
   - Go to "Environment" tab
   - Click "Add Environment Variable"
   - Add:
     - Key: `GEMINI_API_KEY`
     - Value: `AIzaSyA3G2UHBuIMB26yR9yU3dhuoXs0lT6t_nA`
   - Click "Save"

### 2. Monitor Service Restart

After saving, services will automatically restart. Monitor the logs:

1. In Render dashboard, click on `hoistscout-worker`
2. Go to "Logs" tab
3. Look for these success indicators:
   ```
   Connected to Redis at redis://...
   celery@srv-... ready.
   Scraping service status: {'scrapegraph_ai': True, 'gemini': True}
   ```

### 3. Verify Jobs Processing

Once the worker restarts, run:
```bash
python3 check_worker_status.py
```

You should see jobs transitioning from "pending" → "running" → "completed"

### 4. Test Actual Scraping

Run the tenders.gov.au test:
```bash
python3 test_tenders_scraping.py
```

## Troubleshooting

If jobs remain stuck after setting the API key:

1. **Check Worker Logs**: Look for error messages in Render logs
2. **Verify Redis Connection**: Ensure Redis URL is correct
3. **Check API Key**: Verify the key is valid and has Gemini API access
4. **Rate Limits**: Gemini free tier has 15 requests/minute limit

## Next Steps

Once the worker is processing jobs:
1. Monitor job completion
2. Check opportunities are being extracted
3. Verify data appears in frontend at https://hoistscout-frontend.onrender.com/opportunities