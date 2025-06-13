#!/bin/bash

echo "🔍 Validating for CI..."
echo "======================="

# Track issues
issues=0

# 1. Check critical files exist
echo -e "\n📁 Checking critical files..."

files=(
    "backend/poetry.lock"
    "backend/pyproject.toml"
    "frontend/package.json"
    "frontend/package-lock.json"
    "package.json"
    "package-lock.json"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
        ((issues++))
    fi
done

# 2. Check for common CI breakers
echo -e "\n🔧 Checking configurations..."

# Check mypy version
if grep -q 'mypy = "\^1.10"' backend/pyproject.toml; then
    echo "✓ mypy version is correct"
else
    echo "✗ mypy version needs to be ^1.10"
    ((issues++))
fi

# Check for memory optimization
if grep -q "workerThreads: false" frontend/next.config.js; then
    echo "✓ Memory optimization configured"
else
    echo "✗ Memory optimization missing"
    ((issues++))
fi

# Check for workspace configuration
if grep -q '"workspaces"' package.json; then
    echo "✓ Workspace configured"
else
    echo "✗ Workspace not configured"
    ((issues++))
fi

# 3. Summary
echo -e "\n📊 Summary"
echo "=========="

if [ $issues -eq 0 ]; then
    echo "✅ No issues found! Should be safe to push."
    echo ""
    echo "Next steps:"
    echo "1. git status  # Review changes"
    echo "2. git add -A"
    echo "3. git commit -m \"fix: ensure CI passes\""
    echo "4. git push origin fix/deployment-errors"
else
    echo "❌ Found $issues issues that need fixing"
    echo ""
    echo "To fix:"
    echo "1. Run: bash fix-all-issues.sh"
    echo "2. Or fix manually based on errors above"
fi

exit $issues