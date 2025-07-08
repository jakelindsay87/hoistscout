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

# Copy dependency files - handle both root and backend contexts
COPY pyproject.toml* poetry.lock* ./
# Also try backend directory in case of root context
COPY backend/pyproject.toml* backend/poetry.lock* ./ 2>/dev/null || true

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code - handle both contexts
COPY . /app/
COPY backend/* /app/ 2>/dev/null || true
COPY backend/app /app/app 2>/dev/null || true

# Install the app package
RUN poetry install --no-interaction --no-ansi

# Install Playwright browsers (optional)
RUN poetry run playwright install-deps chromium || true
RUN poetry run playwright install chromium || true

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]