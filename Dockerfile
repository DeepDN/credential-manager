# 🔐 SecureVault Docker Image
FROM python:3.9-slim

# Metadata
LABEL maintainer="SecureVault Contributors <contact@securevault.dev>"
LABEL description="🔐 Enterprise-grade password manager"
LABEL version="1.0.0"

# Security: Create non-root user
RUN groupadd -r securevault && useradd -r -g securevault securevault

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY docs/ ./docs/
COPY *.py ./
COPY *.md ./
COPY *.txt ./
COPY *.sh ./

# Create necessary directories
RUN mkdir -p /app/vault /app/backups /app/logs

# Set permissions
RUN chown -R securevault:securevault /app
RUN chmod +x *.sh *.py

# Switch to non-root user
USER securevault

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Environment variables
ENV SECUREVAULT_HOST=0.0.0.0
ENV SECUREVAULT_PORT=8000
ENV SECUREVAULT_VAULT_PATH=/app/vault/vault.enc
ENV SECUREVAULT_BACKUP_DIR=/app/backups
ENV SECUREVAULT_LOG_LEVEL=INFO

# Volume for persistent data
VOLUME ["/app/vault", "/app/backups"]

# Start command
CMD ["python", "run_web.py"]
