FROM python:3.11-slim

# Force rebuild with new worker script
ARG CACHE_BUST=1
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

# Copy and run the robust worker startup script
COPY backend/run_worker.py /app/
CMD ["python", "run_worker.py"]