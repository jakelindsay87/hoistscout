# Steps to Create GitHub Repository for HoistScout

## 1. Create Repository on GitHub

Go to: https://github.com/new

- **Repository name:** `hoistscout`
- **Description:** Victorian Government Tender Scraping System
- **Visibility:** Public or Private (your choice)
- **Do NOT** initialize with README, .gitignore, or license

Click **Create repository**

## 2. Push Local Code to GitHub

After creating the empty repository, run these commands in your terminal:

```bash
cd /root/hoistscout

# Add all files
git add .

# Commit changes
git commit -m "Initial commit - HoistScout tender scraping system"

# Push to GitHub
git push -u origin master
```

## 3. Update Render Services

Once the repository is on GitHub, update each Render service:

1. Go to https://dashboard.render.com
2. For each service (api, frontend, worker):
   - Click on the service
   - Go to Settings
   - Update repository to: `jakelindsay87/hoistscout`
   - Save and redeploy

## Service Direct Links:
- API: https://dashboard.render.com/web/srv-d1hltovfte5s73ad16tg/settings
- Frontend: https://dashboard.render.com/web/srv-d1hlum6r433s73avdn6g/settings
- Worker: https://dashboard.render.com/web/srv-d1hlvanfte5s73ad476g/settings

## Repository Contents

Your repository includes:
- Backend API (FastAPI)
- Frontend (Next.js)
- Worker service for background tasks
- Docker configuration
- Render deployment configuration
- Complete documentation

All code is ready for deployment once the repository is created on GitHub.