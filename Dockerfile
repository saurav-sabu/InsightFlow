# Use official lightweight Python runtime
FROM python:3.12-slim

WORKDIR /app

# 1. Install system tools (git is needed by datasets/ragas, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Copy application source code
COPY app/ ./app/

# 4. Security: Run as a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 5. Environment settings: disable output buffering & bytecode generation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 6. Expose default FastAPI port
EXPOSE 8000

# 7. Container health check (runs every 30s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 8. Start FastAPI server with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
