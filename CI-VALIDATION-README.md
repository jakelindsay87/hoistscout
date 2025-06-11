# CI Validation Tools

This directory contains scripts to ensure GitHub Actions CI tests pass before pushing.

## 🚀 Quick Start

Run this single command to ensure CI will pass:

```bash
./ensure-ci-passes.sh
```

This master script will:
1. Sync all lock files
2. Apply automated fixes
3. Validate everything locally
4. Run exact CI commands

## 📋 Individual Scripts

### 1. `sync-lock-files.sh`
Regenerates all lock files (poetry.lock, package-lock.json) to ensure they're in sync.

```bash
./sync-lock-files.sh
```

### 2. `fix-all-issues.sh`
Automatically fixes common CI issues:
- Reinstalls dependencies
- Runs auto-fixers (ruff, eslint)
- Ensures proper configuration

```bash
./fix-all-issues.sh
```

### 3. `pre-flight-check.sh`
Comprehensive validation that checks:
- Python/Node versions
- Dependencies installed
- Linting passes
- Type checking passes
- Tests pass
- Docker builds work

```bash
./pre-flight-check.sh
```

### 4. `validate-ci-exact.sh`
Runs the EXACT commands from CI workflows to ensure they'll pass.

```bash
./validate-ci-exact.sh
```

### 5. `ci-fix-loop.sh`
Interactive script for push-test-fix cycles:

```bash
./ci-fix-loop.sh
```

## 🔧 Common CI Failures and Fixes

### Poetry Lock Issues
```bash
cd backend
rm poetry.lock
poetry lock
```

### Frontend Lint Issues
```bash
cd frontend
npm run lint -- --fix
```

### Type Errors
```bash
cd frontend
npm run type-check
# Fix the errors shown
```

### Memory Issues
Ensure `frontend/next.config.js` has:
```javascript
experimental: {
  workerThreads: false,
  cpus: 1,
}
```

### Missing Dependencies
```bash
# Backend
cd backend && poetry install --with dev

# Frontend
cd frontend && npm ci
```

## 📝 Workflow

1. **Before any push**, run:
   ```bash
   ./ensure-ci-passes.sh
   ```

2. **If it fails**, fix the issues and run again

3. **Once it passes**, commit and push:
   ```bash
   git add -A
   git commit -m "fix: ensure CI passes"
   git push origin your-branch
   ```

## 🎯 CI Workflows Validated

These scripts validate against:

1. **`.github/workflows/ci.yml`**
   - Database tests with PostgreSQL
   - Python linting (ruff)
   - Python tests (pytest)
   - Frontend linting (ESLint)
   - Frontend type checking (TypeScript)
   - Frontend tests (Vitest)

2. **`.github/workflows/test-deployment.yml`**
   - Docker builds
   - Memory-constrained builds
   - Import validation

## ⚡ Pro Tips

1. **Always run validation before pushing**:
   ```bash
   alias cipush='./ensure-ci-passes.sh && git push'
   ```

2. **Fix lock files after dependency changes**:
   ```bash
   ./sync-lock-files.sh
   ```

3. **Auto-fix what you can**:
   ```bash
   ./fix-all-issues.sh
   ```

4. **Debug specific CI job failures**:
   ```bash
   # Check exact command that's failing
   ./validate-ci-exact.sh
   ```

## 🔍 Debugging

If CI still fails after validation:

1. Check the exact error in GitHub Actions
2. Run the failing command locally
3. Update validation scripts with new checks
4. Share the error message for help

## 📦 Requirements

- Python 3.11+
- Node.js 20+
- Poetry (for backend)
- npm (for frontend)
- Docker (optional, for build tests)

## 🤝 Contributing

If you find a CI failure not caught by these scripts:
1. Add the check to the appropriate script
2. Test it catches the issue
3. Commit the improvement

Remember: The goal is 100% confidence that pushing won't break CI!