FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy dependency files from backend directory
COPY backend/pyproject.toml /app/

# Configure poetry to not create virtual env (we're in container)
RUN poetry config virtualenvs.create false

# Generate lock file
RUN poetry lock --no-update

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy application code from backend directory
COPY backend/ /app

# Install Playwright browsers and dependencies for scrapegraphai (as root)
RUN poetry run playwright install-deps chromium
RUN poetry run playwright install chromium

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]