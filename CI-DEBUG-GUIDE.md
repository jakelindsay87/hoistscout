# CI Debug Guide

## Quick Commands

### 1. Push and Check Status
```bash
# Push current branch
git push origin fix/deployment-errors

# Check CI status (if you have gh CLI)
gh run list --limit 5

# Watch the latest run
gh run watch

# Or open in browser
gh run view --web
```

### 2. View Failure Logs

**Option A: GitHub Web UI**
1. Go to: https://github.com/jakelindsay87/hoistscraper/actions
2. Click on the failed workflow run
3. Click on the failed job
4. Expand the failed step to see error details

**Option B: GitHub CLI**
```bash
# View failed logs in terminal
gh run view --log-failed

# Download all logs
gh run download

# View specific job logs
gh run view --job=<job-id> --log
```

### 3. Common Fixes Based on Errors

#### Poetry Lock Issues
```bash
cd backend
rm poetry.lock
poetry lock
cd ..
git add backend/poetry.lock
git commit --amend --no-edit
git push --force-with-lease
```

#### Frontend Build Issues
```bash
cd frontend
npm ci
npm run lint --fix  # Auto-fix lint issues
npm run build       # Test build locally
cd ..
git add -A
git commit --amend --no-edit
git push --force-with-lease
```

#### Type Errors
```bash
cd frontend
npm run type-check
# Fix any TypeScript errors shown
cd ..
git add -A
git commit --amend --no-edit
git push --force-with-lease
```

### 4. Amend and Re-push Workflow

After fixing issues:
```bash
# Stage all changes
git add -A

# Amend the last commit (keeps same message)
git commit --amend --no-edit

# Force push (safely)
git push --force-with-lease origin fix/deployment-errors
```

## Automated Scripts

### Linux/Mac/WSL
```bash
./ci-fix-loop.sh
```

### Windows PowerShell
```powershell
.\ci-fix-loop.ps1
```

## Manual Debugging Process

1. **Push your changes**
   ```bash
   git push origin fix/deployment-errors
   ```

2. **Watch CI in browser**
   - Go to: https://github.com/jakelindsay87/hoistscraper/actions
   - Click on your workflow run
   - Watch which job fails

3. **Identify the error**
   - Click on the failed job
   - Find the red ❌ step
   - Click to expand error details
   - Copy the error message

4. **Fix locally**
   - Make the necessary changes
   - Test the fix locally if possible

5. **Amend and push**
   ```bash
   git add -A
   git commit --amend --no-edit
   git push --force-with-lease
   ```

6. **Repeat until green** ✅

## Quick Test Commands

Test locally before pushing:

```bash
# Backend tests
cd backend
poetry install
poetry run pytest
poetry run ruff check
poetry run mypy .

# Frontend tests  
cd frontend
npm ci
npm run lint
npm run type-check
npm run build
npm test
```

## Need Help?

If you get stuck, share the error message and I can help you fix it!