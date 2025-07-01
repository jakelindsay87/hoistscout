#!/bin/bash

echo "🚀 Initializing HoistScout Project..."

# Create necessary directories
mkdir -p backend/alembic/versions
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/{dashboards,datasources}

# Create environment file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file from example..."
    cp backend/.env.example backend/.env
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
poetry install

# Generate initial migration
echo "🗄️ Creating initial database migration..."
poetry run alembic revision --autogenerate -m "Initial migration"

# Go back to root
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

# Go back to root
cd ..

# Pull Ollama model
echo "🤖 Pulling Ollama model (this may take a while)..."
docker pull ollama/ollama:latest

echo "✅ Project initialization complete!"
echo ""
echo "To start the development environment, run:"
echo "  docker-compose up -d"
echo ""
echo "Then apply database migrations:"
echo "  docker-compose exec backend poetry run alembic upgrade head"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  MinIO Console: http://localhost:9001"
echo "  Grafana: http://localhost:3001"