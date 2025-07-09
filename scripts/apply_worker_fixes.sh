#!/bin/bash
# Script to apply worker fixes to production

set -e

echo "=== HoistScout Worker Fix Deployment Script ==="
echo "This script will apply the necessary fixes for the Redis worker connection issues"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ;;
        "info")
            echo -e "${YELLOW}ℹ${NC} $message"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_status "error" "This script must be run from the hoistscout-repo root directory"
    exit 1
fi

print_status "info" "Current directory: $(pwd)"

# Step 1: Backup current worker.py
print_status "info" "Backing up current worker.py..."
cp backend/app/worker.py backend/app/worker.py.backup.$(date +%Y%m%d_%H%M%S)
print_status "success" "Backup created"

# Step 2: Apply the fixed worker.py
print_status "info" "Applying fixed worker.py..."
cp backend/app/worker_fixed.py backend/app/worker.py
print_status "success" "Fixed worker.py applied"

# Step 3: Create updated Dockerfile.worker with SSL support
print_status "info" "Creating updated Dockerfile.worker..."
cat > backend/Dockerfile.worker.fixed << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including SSL libraries
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code
COPY ./app /app/app
COPY ./pyproject.toml /app/pyproject.toml
COPY ./requirements.txt /app/requirements.txt

# Set Python path
ENV PYTHONPATH=/app

# Install Python dependencies with SSL support
RUN pip install --no-cache-dir \
    celery[redis]==5.3.0 \
    redis[hiredis]==5.0.1 \
    hiredis==2.3.2 \
    sqlalchemy[asyncio]==2.0.23 \
    asyncpg==0.29.0 \
    pydantic==2.10.2 \
    pydantic-settings==2.6.1 \
    playwright==1.43.0 \
    httpx==0.26.0 \
    python-dotenv==1.0.1 \
    loguru==0.7.2 \
    tenacity==8.2.3 \
    beautifulsoup4==4.12.0 \
    lxml==5.1.0

# Install additional dependencies
RUN pip install --no-cache-dir \
    langchain==0.3.0 \
    langchain-core==0.3.0 \
    langchain-community==0.3.0 \
    langsmith==0.1.125 \
    google-generativeai==0.8.3 \
    anthropic==0.39.0 \
    openai==1.50.2 \
    scrapegraphai==1.60.0

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Run the worker with proper SSL configuration
CMD ["python", "-m", "celery", "-A", "app.worker", "worker", "--loglevel=info", "--pool=solo"]
EOF
print_status "success" "Updated Dockerfile.worker created"

# Step 4: Test the fix locally (optional)
read -p "Do you want to test the worker locally first? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "info" "Running diagnostic script..."
    python scripts/fix_redis_worker.py
fi

# Step 5: Generate environment variables for Render
print_status "info" "Generating Render environment variables..."
cat > scripts/render_env_vars.txt << 'EOF'
# Environment variables for Render Worker Service
# Add these to your Render service environment

# Redis Configuration
REDIS_URL=<your-redis-url-here>
CELERY_BROKER_URL=<same-as-redis-url>
CELERY_RESULT_BACKEND=<same-as-redis-url>

# Python Configuration
PYTHONUNBUFFERED=1

# Database Configuration (from your Render Postgres)
DATABASE_URL=<your-database-url-here>

# Gemini Configuration (if using)
GEMINI_API_KEY=<your-gemini-api-key>
USE_GEMINI=true
GEMINI_MODEL=gemini-1.5-flash

# Worker Configuration
WORKER_TYPE=v2
DATA_DIR=/data
CRAWL_CONCURRENCY=8
EOF
print_status "success" "Environment variables template created at scripts/render_env_vars.txt"

# Step 6: Deployment instructions
echo ""
echo "=== DEPLOYMENT INSTRUCTIONS ==="
echo ""
echo "1. LOCAL TESTING (if not done above):"
echo "   python scripts/fix_redis_worker.py"
echo ""
echo "2. COMMIT CHANGES:"
echo "   git add backend/app/worker.py"
echo "   git commit -m 'Fix worker Redis connection and type casting issues'"
echo "   git push origin master"
echo ""
echo "3. UPDATE DOCKERFILE (if using SSL Redis):"
echo "   cp backend/Dockerfile.worker.fixed backend/Dockerfile.worker"
echo "   git add backend/Dockerfile.worker"
echo "   git commit -m 'Update worker Dockerfile with SSL support'"
echo "   git push origin master"
echo ""
echo "4. UPDATE RENDER ENVIRONMENT:"
echo "   - Go to your Render dashboard"
echo "   - Select your worker service"
echo "   - Go to Environment tab"
echo "   - Add/update the variables from scripts/render_env_vars.txt"
echo ""
echo "5. DEPLOY:"
echo "   - Render should auto-deploy on push"
echo "   - Or manually trigger a deploy from Render dashboard"
echo ""
echo "6. MONITOR:"
echo "   - Check worker logs in Render dashboard"
echo "   - Look for 'CELERY WORKER INITIALIZATION' messages"
echo "   - Verify 'All tests passed!' in diagnostic output"
echo ""

print_status "success" "Fix preparation complete!"