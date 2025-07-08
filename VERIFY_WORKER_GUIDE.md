# How to Verify HoistScout Worker is Running

## Quick Verification Steps

### 1. Check Render Worker Logs
After setting GEMINI_API_KEY, check the worker logs in Render dashboard:

**✅ Good signs:**
```
Connected to Redis at redis://...
celery@srv-d1hlvanfte5s73ad476g ready.
Scraping service status: {'scrapegraph_ai': True, 'gemini': True, ...}
```

**❌ Bad signs:**
```
ImportError: cannot import name 'SmartScraperGraph'
ConnectionError: Error -2 connecting to redis
GEMINI_API_KEY not configured
```

### 2. Run Job Status Check
```bash
python3 check_opportunities.py
```

If working, you should see opportunities extracted.

### 3. Create Test Scraping Job
```bash
python3 test_tenders_scraping.py
```

Watch for:
- Job status changing from "pending" to "running"
- Eventually "completed" with extracted opportunities

### 4. Check Specific Job Status
```bash
curl -s -X POST https://hoistscout-api.onrender.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@hoistscout.com&password=demo123" | jq -r .access_token > token.txt

TOKEN=$(cat token.txt)

# Check all jobs
curl -s https://hoistscout-api.onrender.com/api/scraping/jobs/ \
  -H "Authorization: Bearer $TOKEN" | jq '.[0]'
```

### 5. Common Issues & Solutions

**Issue: Jobs stuck in pending**
- Solution: Set GEMINI_API_KEY in Render

**Issue: Worker crashes on startup**
- Check: Is scrapegraphai installed?
- Solution: Already fixed in Dockerfile with `-E ai`

**Issue: Cannot connect to Redis**
- Check: REDIS_URL in environment
- Solution: Verify Redis service is running

**Issue: Gemini API errors**
- Check: API key is valid
- Check: Not hitting rate limits (15 req/min)

### Expected Timeline
1. Set GEMINI_API_KEY ➜ 1-2 min for service restart
2. Worker connects to Redis ➜ Immediate
3. Jobs start processing ➜ Within 30 seconds
4. First opportunities extracted ➜ 1-2 minutes per job

### Success Criteria
When everything is working:
- Worker logs show "Connected to Redis"
- Jobs transition: pending → running → completed
- Opportunities appear in database
- API returns extracted tender data