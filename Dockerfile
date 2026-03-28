FROM python:3.13-slim

WORKDIR /app

# System deps needed for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ports used by backend and frontend respectively
EXPOSE 8080

# Uses $PORT if set (Cloud Run injects it), falls back to 8000 locally.
# docker-compose overrides this CMD entirely via its own 'command' field.
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
