FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock
COPY backend/pyproject.toml backend/poetry.lock* ./

# Install Poetry with specific version for consistency
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi || \
    (poetry lock --no-update && poetry install --no-root --no-interaction --no-ansi)

# Install Playwright and browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY backend/ .

# Copy and make entrypoint executable
COPY backend/api_entrypoint.sh ./
RUN chmod +x api_entrypoint.sh

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the entrypoint script
CMD ["./api_entrypoint.sh"] 