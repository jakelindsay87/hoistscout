#!/bin/bash

echo "🧪 Testing memory usage during build..."

# Test frontend build with memory monitoring
echo -e "\n1. Testing frontend build memory usage..."
cd frontend

# Clean previous builds
rm -rf .next node_modules

# Install dependencies
echo "Installing dependencies..."
npm ci

# Monitor memory during build
echo -e "\nStarting build with memory monitoring..."
/usr/bin/time -v npm run build 2>&1 | grep -E "(Maximum resident set size|Elapsed|Exit status)"

# Check build output size
echo -e "\nBuild output size:"
du -sh .next

cd ..

echo -e "\n✅ Memory test complete!"
echo "If Maximum resident set size > 500MB, the build may fail on Render's free tier"