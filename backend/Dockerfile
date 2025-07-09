FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copy backend files from root context
COPY backend/requirements.txt backend/pyproject.toml backend/poetry.lock* ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-dev || \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

ENV PYTHONPATH=/app

# Copy entrypoint script
COPY backend/worker_entrypoint.sh /app/
RUN chmod +x /app/worker_entrypoint.sh

# Run worker
CMD ["/app/worker_entrypoint.sh"]