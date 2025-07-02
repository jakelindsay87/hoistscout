#!/bin/bash
# Quick deployment fix script for common issues

echo "🔧 HoistScout Deployment Fixer"
echo "=============================="

# Check if we're in the backend directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the backend directory"
    exit 1
fi

echo "✅ Fixing common deployment issues..."

# Fix 1: Update scrapegraph package name
echo "1. Fixing scrapegraph package name..."
sed -i 's/scrapegraphai/scrapegraph-ai/g' pyproject.toml
sed -i 's/from scrapegraphai/from scrapegraph_ai/g' app/core/scraper.py

# Fix 2: Ensure asyncpg is present
echo "2. Ensuring asyncpg is in dependencies..."
if ! grep -q "asyncpg" pyproject.toml; then
    sed -i '/^psycopg2-binary/a asyncpg = "^0.29.0"' pyproject.toml
fi

# Fix 3: Regenerate lock file
echo "3. Regenerating poetry lock file..."
poetry lock --no-update

# Fix 4: Make deployment check executable
echo "4. Making deployment check executable..."
chmod +x app/deployment_check.py

# Fix 5: Run deployment validation
echo "5. Running deployment validation..."
python app/deployment_check.py

echo ""
echo "✅ Common fixes applied!"
echo ""
echo "Next steps:"
echo "1. Review the validation output above"
echo "2. Fix any remaining issues"
echo "3. Commit changes: git add -A && git commit -m 'fix: deployment issues'"
echo "4. Push to deploy: git push origin main"