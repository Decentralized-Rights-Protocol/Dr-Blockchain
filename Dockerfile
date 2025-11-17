FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements-ci.txt requirements.txt ./
COPY src/api/ai_transparency_service/requirements.txt ./src/api/ai_transparency_service/
COPY src/explorer/requirements.txt ./src/explorer/
COPY db/requirements.txt ./db/

# Install Python dependencies (install all service requirements)
RUN pip install --no-cache-dir -r requirements-ci.txt && \
    pip install --no-cache-dir -r src/api/ai_transparency_service/requirements.txt && \
    pip install --no-cache-dir -r src/explorer/requirements.txt && \
    pip install --no-cache-dir -r db/requirements.txt || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/keys /app/logs

# Set environment variables
ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Health check (Railway will override this with its own healthcheck from render.yaml)
# Default to /health endpoint, but Railway will use the healthCheckPath from render.yaml
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application based on SERVICE_NAME environment variable
# If SERVICE_NAME is set, use it to determine which service to run
# Otherwise, default to gateway.py
CMD sh -c 'if [ -n "$SERVICE_NAME" ]; then \
  if [ "$SERVICE_NAME" = "drp-ai-service" ]; then \
    cd src && PYTHONPATH=. uvicorn api.ai_transparency_service.main:app --host 0.0.0.0 --port ${PORT:-8000}; \
  elif [ "$SERVICE_NAME" = "drp-explorer-api" ]; then \
    cd src && PYTHONPATH=. uvicorn explorer.api:app --host 0.0.0.0 --port ${PORT:-8000}; \
  elif [ "$SERVICE_NAME" = "drp-indexer" ]; then \
    python db/indexer.py; \
  else \
    python gateway.py; \
  fi \
else \
  python gateway.py; \
fi'
