# HoistScout Makefile

.PHONY: help fmt test lint test-all test-local test-docker test-frontend test-backend test-worker verify-deploy health-check clean

# Default target
help:
	@echo "HoistScout Commands:"
	@echo "===================="
	@echo "Core Commands (required by CLAUDE.md):"
	@echo "make fmt             - Format code (black + ruff)"
	@echo "make test            - Run all tests"
	@echo "make lint            - Run linting checks"
	@echo ""
	@echo "Testing Commands:"
	@echo "make test-all        - Run all tests (local + docker)"
	@echo "make test-local      - Run local tests without Docker"
	@echo "make test-docker     - Run tests with Docker Compose"
	@echo "make test-frontend   - Run frontend tests only"
	@echo "make test-backend    - Run backend tests only"
	@echo "make test-worker     - Run worker tests only"
	@echo "make verify-deploy   - Pre-deployment verification"
	@echo "make health-check    - Post-deployment health check"
	@echo "make clean          - Clean up test artifacts"
	@echo ""
	@echo "Quick Commands:"
	@echo "make fix-lint       - Auto-fix linting issues"
	@echo "make docker-up      - Start test environment"
	@echo "make docker-down    - Stop test environment"
	@echo "make docker-logs    - View Docker logs"

# Core commands required by CLAUDE.md
fmt:
	@echo "🎨 Formatting code..."
	@cd backend && poetry run black . && poetry run ruff format .
	@cd frontend && npm run lint -- --fix
	@echo "✅ Formatting complete!"

test:
	@echo "🧪 Running all tests..."
	@cd backend && poetry run pytest -v
	@cd frontend && npm test -- --run
	@echo "✅ All tests passed!"

lint:
	@echo "🔍 Running linting checks..."
	@cd backend && poetry run ruff check . && poetry run mypy .
	@cd frontend && npm run lint && npm run type-check
	@echo "✅ Linting complete!"

# Run all tests
test-all: test-local test-docker

# Run local tests
test-local:
	@./scripts/test-local.sh

# Run Docker tests
test-docker:
	@./scripts/test-docker.sh

# Run frontend tests only
test-frontend:
	@echo "🎨 Running Frontend Tests..."
	@cd frontend && npm ci && npm test -- --run && npm run type-check && npm run build

# Run backend tests only
test-backend:
	@echo "📦 Running Backend Tests..."
	@cd backend && poetry install && poetry run pytest -v && poetry run mypy .

# Run worker tests only
test-worker:
	@echo "🔧 Running Worker Tests..."
	@cd backend && poetry run pytest tests/test_worker.py -v

# Pre-deployment verification
verify-deploy:
	@./scripts/test-predeploy.sh

# Post-deployment health check
health-check:
	@./scripts/test-postdeploy.sh

# Docker commands
docker-up:
	@echo "🐳 Starting Docker test environment..."
	@docker compose -f docker-compose.test.yml up -d

docker-down:
	@echo "🛑 Stopping Docker test environment..."
	@docker compose -f docker-compose.test.yml down -v

docker-logs:
	@docker compose -f docker-compose.test.yml logs -f

docker-build:
	@echo "🔨 Building Docker images..."
	@docker compose -f docker-compose.test.yml build --no-cache

# Fix common issues
fix-lint:
	@echo "🔧 Auto-fixing linting issues..."
	@cd backend && poetry run ruff format .
	@cd frontend && npm run lint -- --fix

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf frontend/.next
	@rm -rf frontend/node_modules
	@rm -rf backend/__pycache__
	@rm -rf backend/.pytest_cache
	@rm -rf backend/.mypy_cache
	@rm -rf data/*
	@docker compose -f docker-compose.test.yml down -v || true
	@echo "✨ Clean complete!"

# Install all dependencies
install:
	@echo "📦 Installing dependencies..."
	@cd backend && poetry install
	@cd frontend && npm ci
	@echo "✅ Dependencies installed!"

# Quick test before commit
pre-commit: fix-lint test-local verify-deploy
	@echo "✅ Ready to commit!"