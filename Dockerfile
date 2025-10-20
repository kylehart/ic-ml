# Dockerfile for Railway deployment of IC-ML Health Quiz Service

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p runs data/rogue-herbalist config

# Set Python path to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Railway provides PORT environment variable
ENV PORT=8000

# Expose port (Railway will override with its own PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:${PORT}/health')"

# Run the application
CMD uvicorn src.web_service:app --host 0.0.0.0 --port $PORT
