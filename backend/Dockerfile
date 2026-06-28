# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a wheels directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# STAGE 2: Runtime
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/app/.local/bin:$PATH
ENV PORT=8000
ENV WEB_CONCURRENCY=1

# Install runtime system libraries (e.g. libpq for Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Run as non-privileged system user for absolute security boundaries
RUN useradd -u 10001 -m app
USER app

# Copy wheels/packages from builder stage
COPY --from=builder --chown=app:app /root/.local /home/app/.local

# Copy application code
COPY --chown=app:app . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health/live' % os.getenv('PORT','8000'), timeout=3).read()"

# Default to one worker because Twilio Media Streams and local fallbacks are in-memory.
# Scale workers only when Redis/Supabase are configured and sticky routing is in place.
CMD ["sh", "-c", "gunicorn server.twilio_handler:app --workers ${WEB_CONCURRENCY:-1} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --timeout 120 --graceful-timeout 30 --keep-alive 30"]
