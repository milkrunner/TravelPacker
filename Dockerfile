# Multi-stage build for NikNotes Trip Packing Assistant
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL and build tools
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Create non-root user and group
RUN groupadd -r niknotes && \
    useradd -r -g niknotes -u 1000 niknotes && \
    chown -R niknotes:niknotes /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web_app.py
ENV PYTHONPATH=/app

# Switch to non-root user
USER niknotes

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:5000/health', timeout=5); exit(0 if r.status_code == 200 and r.json().get('status') == 'healthy' else 1)" || exit 1

# Run database migrations and start the app
# Note: Flask runs on 0.0.0.0 to be accessible from outside the container
CMD ["sh", "-c", "python scripts/migrate.py create && python -c 'from web_app import app; app.run(host=\"0.0.0.0\", port=5000)'"]
