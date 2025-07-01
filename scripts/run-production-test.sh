#!/bin/bash
# Script to run the complete production test with compliance checking

echo "🚀 Starting HoistScout Production Test Suite"
echo "==========================================="
echo ""

# Set up environment
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
export ENV_FILE=".env.production"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q playwright pytest pytest-asyncio pandas openpyxl httpx beautifulsoup4 python-robotparser

# Install Playwright browsers if needed
echo "🌐 Setting up Playwright browsers..."
playwright install chromium

# Create necessary directories
mkdir -p logs
mkdir -p test_results
mkdir -p auth_states

# Clear old test results
echo "🧹 Cleaning up old test results..."
rm -f logs/auth_*.png
rm -f test_results/*.json
rm -f test_results/*.xlsx

# Display test configuration
echo ""
echo "📋 Test Configuration:"
echo "  - Target: Victorian Government Tenders"
echo "  - URL: https://www.tenders.vic.gov.au"
echo "  - Compliance Checking: ENABLED"
echo "  - Rate Limiting: 2000ms between requests"
echo "  - Authentication: Form-based with real credentials"
echo ""

# Confirm before proceeding
read -p "⚠️  This will perform REAL scraping on Victorian Government Tenders. Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Test cancelled by user"
    exit 1
fi

echo ""
echo "🔍 Phase 1: Pre-flight Compliance Check"
echo "--------------------------------------"

# Run compliance check first
python3 -c "
import asyncio
import sys
sys.path.append('backend')
from app.core.compliance_checker import TermsComplianceChecker

async def check_compliance():
    checker = TermsComplianceChecker()
    result = await checker.check_site_compliance({
        'url': 'https://www.tenders.vic.gov.au',
        'name': 'Victorian Government Tenders'
    })
    
    print(f'Compliance Status: {result[\"compliance_status\"]}')
    print(f'Scraping Allowed: {result[\"scraping_allowed\"]}')
    print(f'Risk Level: {result[\"risk_level\"]}')
    
    if result['scraping_allowed']:
        print('✅ Compliance check PASSED - Proceeding with test')
        return True
    else:
        print('❌ Compliance check FAILED - Cannot proceed')
        print(f'Reason: {result.get(\"recommended_approach\", \"Unknown\")}')
        return False

if not asyncio.run(check_compliance()):
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Compliance check failed. Exiting."
    exit 1
fi

echo ""
echo "🚀 Starting Full Production Test"
echo "--------------------------------"

# Run the production test
if [ "$1" == "--pytest" ]; then
    # Run with pytest for full test framework
    pytest tests/e2e/test_production_complete_workflow.py -v -s --tb=short
else
    # Run directly for more control
    python3 tests/e2e/test_production_complete_workflow.py
fi

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Production test completed successfully!"
    echo ""
    echo "📊 Test Results:"
    echo "  - Results saved in: test_results/"
    echo "  - Logs saved in: logs/"
    echo "  - Screenshots saved in: logs/"
    
    # Display summary of results
    if [ -f "test_results/production_test_results_*.json" ]; then
        echo ""
        echo "📈 Summary:"
        python3 -c "
import json
import glob

latest_result = sorted(glob.glob('test_results/production_test_results_*.json'))[-1]
with open(latest_result) as f:
    data = json.load(f)
    
if 'phases' in data:
    print(f'  - Compliance: {data[\"phases\"][\"compliance\"][\"compliance_status\"]}')
    print(f'  - Authentication: {\"PASSED\" if data[\"phases\"][\"authentication\"][\"authenticated\"] else \"FAILED\"}')
    print(f'  - Opportunities Found: {len(data[\"phases\"][\"scraping\"][\"opportunities\"])}')
    print(f'  - Data Quality: {\"PASSED\" if data[\"phases\"][\"validation\"][\"success\"] else \"FAILED\"}')
"
    fi
    
    # List exported files
    echo ""
    echo "📁 Exported Files:"
    ls -la test_results/*.xlsx 2>/dev/null || echo "  No Excel exports found"
    
else
    echo ""
    echo "❌ Production test failed!"
    echo "  Check logs/ directory for error details"
    exit 1
fi

echo ""
echo "🏁 Test suite completed"
echo ""

# Deactivate virtual environment
deactivate