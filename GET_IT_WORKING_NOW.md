# 🚀 GET HOISTSCOUT WORKING - 3 STEPS

## The Problem
HoistScout is deployed but **NOT extracting any funding opportunities** because the worker can't process jobs without GEMINI_API_KEY.

## Step 1: Push & Deploy (2 min)
```bash
cd /root/hoistscout-repo
git add check_production_pipeline.py PRODUCTION_CHECKLIST.md GET_IT_WORKING_NOW.md
git commit -m "Add production verification scripts"
git push origin main
```

## Step 2: Add GEMINI_API_KEY (3 min) 🔑
1. **Get your API key** (if you don't have one):
   - Go to: https://makersuite.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key

2. **Add to Render Worker**:
   - Go to: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g
   - Click "Environment" tab
   - Click "Add Environment Variable"
   - Key: `GEMINI_API_KEY`
   - Value: [paste your API key]
   - Click "Save Changes"
   - Worker will auto-restart

## Step 3: Verify It's Working (5 min)
Run the verification script:
```bash
python3 check_production_pipeline.py
```

Or manually check:
1. Login at https://hoistscout-frontend.onrender.com (demo/demo123)
2. Go to Websites → Find "Australian Government Tenders"
3. Click "Scrape"
4. Go to Jobs tab - should show "running" not "pending"
5. After 2-3 min, check Opportunities tab - should see grants!

## Success Criteria ✅
- Jobs change from "pending" → "running" → "completed"
- Opportunities appear in the database
- You can search/filter/export funding opportunities

## If It's Not Working
Check worker logs at: https://dashboard.render.com/worker/srv-d1hlvanfte5s73ad476g/logs
- Look for "GEMINI_API_KEY not found" errors
- Check for timeout or rate limit issues

---
**Total Time: ~10 minutes to working production app**