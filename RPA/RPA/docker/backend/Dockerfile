# RPA Backend - FastAPI REST + WebSocket Server
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/BBRNGIT/RPA"
LABEL org.opencontainers.image.description="RPA Backend - FastAPI Server"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 rpa

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY rpa/ ./rpa/
COPY curriculum/ ./curriculum/
COPY config/ ./config/
COPY interactive_train.py .
COPY learn_pipeline.py .
COPY train.py .

# Create necessary directories
RUN mkdir -p /data /app/memory && \
    chown -R rpa:rpa /app /data

# Switch to non-root user
USER rpa

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Default command
CMD ["uvicorn", "rpa.core_api.server:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
