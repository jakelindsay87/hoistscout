FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock
COPY backend/pyproject.toml backend/poetry.lock* ./

# Install Poetry with specific version for consistency
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

# Install Playwright and browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "hoistscraper.main:app", "--host", "0.0.0.0", "--port", "8000"] 