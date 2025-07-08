# 🚨 HoistScout Production Checklist - URGENT

## Current Status: BROKEN ❌
- Frontend: ✅ Live at https://hoistscout-frontend.onrender.com
- API: ✅ Live at https://hoistscout-api.onrender.com
- Worker: ❌ NOT PROCESSING JOBS (missing GEMINI_API_KEY)
- Opportunities Extracted: **0** (should be hundreds)

## Step 1: Push Current Fixes (5 min)
```bash
cd /root/hoistscout-repo
git push origin main
```
This will deploy our dependency fixes and ensure services can build.

## Step 2: Set GEMINI_API_KEY (5 min) 🔑
1. Go to https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g
2. Click "Environment" tab
3. Add environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: Your Google Gemini API key
4. Click "Save Changes"
5. The worker will auto-restart

**Don't have a Gemini API key?**
Get one FREE at: https://makersuite.google.com/app/apikey

## Step 3: Verify Worker is Running (2 min)
1. Check worker logs in Render dashboard
2. Look for: "Celery worker ready" or similar
3. Ensure no errors about missing API key

## Step 4: Test Extraction Pipeline (10 min)
Run this test script:

```bash
cd /root/hoistscout-repo
python3 check_production_pipeline.py
```

Or manually:
1. Login: https://hoistscout-frontend.onrender.com
   - Username: `demo`
   - Password: `demo123`
2. Go to "Websites" tab
3. Find "Australian Government Tenders" (tenders.gov.au)
4. Click "Scrape" button
5. Go to "Jobs" tab - verify job is "running" not "pending"
6. Wait 2-3 minutes
7. Go to "Opportunities" tab - you should see extracted grants!

## Step 5: Monitor Extraction (5 min)
Check that opportunities are being extracted:
- API endpoint: https://hoistscout-api.onrender.com/api/opportunities
- Should return actual funding opportunities, not empty array

## Expected Results
After completing these steps:
- ✅ Worker processing jobs (status: running → completed)
- ✅ Opportunities appearing in database
- ✅ Frontend showing funding opportunities
- ✅ Search/filter functionality working
- ✅ Export to CSV working

## If Still Not Working
1. Check worker logs for errors
2. Verify GEMINI_API_KEY is set correctly
3. Check if jobs are failing with specific errors
4. Look for timeout issues or rate limits

## Next Steps (After Core Working)
- [ ] Enable scheduled scraping (cron jobs)
- [ ] Add email notifications
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy

---
**Time to Production: ~30 minutes**