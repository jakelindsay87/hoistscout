# Multi-stage build for Python backend
FROM python:3.11-slim as python-base

# Python and Poetry configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Poetry
RUN pip install poetry==1.8.3

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Dependencies stage
FROM python-base as dependencies
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Poetry configuration files
COPY pyproject.toml ./

# Install Python dependencies (will generate lock file)
RUN poetry lock && poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python-base as production
WORKDIR /app

# Install system dependencies for production
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    libxss1 \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from dependencies stage
COPY --from=dependencies /app/.venv /app/.venv

# Make sure to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Install Playwright browsers
RUN poetry run playwright install chromium

# Create data directory for scraping results
RUN mkdir -p /app/data

# Create non-root user
RUN addgroup --system --gid 1001 appgroup
RUN adduser --system --uid 1001 appuser
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
CMD ["sh", "-c", "uvicorn hoistscraper.main:app --host 0.0.0.0 --port ${PORT:-8000}"]