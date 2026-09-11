FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app/src

# curl is used by the container HEALTHCHECK; postgresql-client provides pg_dump
# and psql for the database backup/restore path documented in ops/.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn matplotlib

COPY src/ .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Non-root user. STATIC_ROOT is written at container start by collectstatic, so
# it must exist and be writable by that user.
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/src/staticfiles \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Liveness probe against the unauthenticated health endpoint. Host header is set
# explicitly so this works regardless of ALLOWED_HOSTS.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS -H "Host: ${HEALTHCHECK_HOST:-localhost}" \
        "http://127.0.0.1:${PORT:-8000}/healthz" || exit 1

CMD ["/app/entrypoint.sh"]
