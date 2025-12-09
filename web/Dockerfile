# ==========================================================
# Eón Web Dashboard Dockerfile
# ==========================================================
# Flask-based dashboard with real-time AI interaction
# ==========================================================

FROM python:3.11-slim

LABEL maintainer="Eón Project AI"
LABEL description="Web Dashboard for Eón AI System"
LABEL version="1.7.1"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure
COPY phase1-foundations /app/phase1-foundations
COPY phase7-language /app/phase7-language
COPY web /app/web
COPY GENESIS.json /app/GENESIS.json

# Set Python path
ENV PYTHONPATH=/app:/app/phase1-foundations/python:/app/phase7-language
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run Flask app
WORKDIR /app/web
CMD ["python", "server.py"]
