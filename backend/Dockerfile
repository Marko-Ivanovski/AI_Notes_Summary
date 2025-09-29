# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# System deps for Postgres client & build tools
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

EXPOSE 5000

# Use gunicorn as the entrypoint
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "3"]
