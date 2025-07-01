#!/bin/bash
# Production deployment script for HoistScraper

set -e  # Exit on error

echo "=== HoistScraper Production Deployment ==="
echo "Time: $(date)"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/jakelindsay87/hoistscraper"
BRANCH="main"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running in CI/CD environment
if [ -n "$RENDER" ]; then
    print_status "Running in Render environment"
    CI_MODE=true
else
    CI_MODE=false
fi

# Step 1: Verify Git repository
print_status "Checking Git repository..."
if [ -d .git ]; then
    CURRENT_BRANCH=$(git branch --show-current)
    print_status "Current branch: $CURRENT_BRANCH"
    
    if [ "$CI_MODE" = false ]; then
        # Check for uncommitted changes
        if [ -n "$(git status --porcelain)" ]; then
            print_warning "Uncommitted changes detected"
            echo "Please commit or stash changes before deploying"
            exit 1
        fi
        
        # Pull latest changes
        print_status "Pulling latest changes..."
        git pull origin $BRANCH
    fi
else
    print_warning "Not a git repository"
fi

# Step 2: Backend deployment preparation
print_status "Preparing backend deployment..."

# Check Python dependencies
if [ -f backend/pyproject.toml ]; then
    print_status "Found pyproject.toml"
    
    # Generate requirements.txt for Render if needed
    if [ ! -f backend/requirements.txt ] || [ backend/pyproject.toml -nt backend/requirements.txt ]; then
        print_status "Generating requirements.txt from pyproject.toml..."
        cd backend
        if command -v poetry &> /dev/null; then
            poetry export -f requirements.txt --output requirements.txt --without-hashes
        else
            print_warning "Poetry not found, using pip-compile"
            pip-compile pyproject.toml
        fi
        cd ..
    fi
fi

# Step 3: Frontend build preparation
print_status "Preparing frontend build..."

# Check if frontend dependencies need updating
if [ -f frontend/package.json ]; then
    print_status "Found package.json"
    
    # Set build environment variables
    export NODE_OPTIONS="--max-old-space-size=2048"
    export NEXT_TELEMETRY_DISABLED=1
    
    if [ "$CI_MODE" = false ]; then
        cd frontend
        print_status "Installing frontend dependencies..."
        npm install
        
        # Run type checking
        print_status "Running TypeScript type check..."
        npm run type-check || print_warning "Type check failed, continuing..."
        
        # Build frontend
        print_status "Building frontend..."
        npm run build
        cd ..
    fi
fi

# Step 4: Database migration check
print_status "Checking database migrations..."

cat > check_db_migration.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from hoistscraper.db import engine
    from sqlmodel import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Found {len(tables)} tables in database")
    
    # Check for required columns in website table
    if 'website' in tables:
        columns = [col['name'] for col in inspector.get_columns('website')]
        required_columns = ['credentials', 'region', 'government_level', 'grant_type']
        missing = [col for col in required_columns if col not in columns]
        
        if missing:
            print(f"Missing columns in website table: {missing}")
            print("Database migration required!")
            sys.exit(1)
        else:
            print("All required columns present")
    else:
        print("Website table not found - initial migration required")
        sys.exit(1)
        
except Exception as e:
    print(f"Database check failed: {e}")
    sys.exit(1)
EOF

if [ "$CI_MODE" = false ]; then
    print_status "Running database migration check..."
    python3 check_db_migration.py || {
        print_warning "Database migration needed"
        print_status "Running database initialization..."
        python3 init_database.py
    }
fi

# Step 5: Create deployment configuration
print_status "Creating deployment configuration..."

cat > render_deploy.json << EOF
{
  "services": [
    {
      "name": "hoistscraper",
      "type": "web",
      "env": "docker",
      "dockerfilePath": "./backend/Dockerfile",
      "envVars": {
        "USE_SIMPLE_QUEUE": "true",
        "WORKER_TYPE": "v2",
        "LOG_LEVEL": "INFO"
      }
    },
    {
      "name": "hoistscraper-fe",
      "type": "web", 
      "env": "docker",
      "dockerfilePath": "./frontend/Dockerfile",
      "envVars": {
        "NEXT_PUBLIC_API_URL": "https://hoistscraper.onrender.com"
      }
    },
    {
      "name": "hoistscraper-worker",
      "type": "worker",
      "env": "docker",
      "dockerfilePath": "./backend/Dockerfile.worker",
      "envVars": {
        "USE_SIMPLE_QUEUE": "true",
        "WORKER_TYPE": "v2"
      }
    }
  ]
}
EOF

# Step 6: Push changes if not in CI
if [ "$CI_MODE" = false ]; then
    print_status "Pushing changes to repository..."
    git add -A
    git commit -m "Deploy: Update configuration and models for production" || true
    git push origin $BRANCH
fi

# Step 7: Trigger Render deployment
if command -v render &> /dev/null; then
    print_status "Triggering Render deployment..."
    render deploy --service hoistscraper
    render deploy --service hoistscraper-fe
    render deploy --service hoistscraper-worker
else
    print_warning "Render CLI not found"
    echo "Please deploy manually through Render dashboard or install Render CLI"
fi

# Step 8: Post-deployment validation
print_status "Creating post-deployment validation script..."

cat > validate_deployment.sh << 'EOF'
#!/bin/bash
echo "Waiting for services to stabilize..."
sleep 30

echo "Running deployment validation..."
python3 check_deployment.py

echo "Running functionality test..."
python3 test_scraping.py

echo "Checking worker status..."
curl -s https://hoistscraper.onrender.com/health | jq .
EOF

chmod +x validate_deployment.sh

print_status "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. If using Render dashboard, trigger manual deploy for each service"
echo "2. Wait for deployments to complete (5-10 minutes)"
echo "3. Run ./validate_deployment.sh to verify deployment"
echo ""
echo "Services to deploy:"
echo "  - Backend API: hoistscraper"
echo "  - Frontend: hoistscraper-fe"  
echo "  - Worker: hoistscraper-worker"