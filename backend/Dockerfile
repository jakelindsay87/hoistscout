FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt* pyproject.toml* poetry.lock* ./
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-dev || \
    pip install --no-cache-dir -r requirements.txt || \
    pip install fastapi uvicorn sqlalchemy psycopg2-binary redis celery

# Copy application code
COPY . .

ENV PYTHONPATH=/app

# Run worker
CMD ["python", "-m", "celery", "-A", "app.worker", "worker", "--loglevel=info"]