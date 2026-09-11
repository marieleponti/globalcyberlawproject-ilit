#!/bin/sh
set -eu

export PYTHONPATH=/app/src

PORT="${PORT:-8000}"

# --- Wait for Postgres ------------------------------------------------------
# Compose already gates on the db healthcheck, but a restarted database or a
# managed instance still needs this. Without it the first migrate crashes the
# container and restarts churn.
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"
echo "Waiting up to ${DB_WAIT_TIMEOUT}s for the database..."
waited=0
until python -c "
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nat_state_vis_app.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    waited=$((waited + 2))
    if [ "$waited" -ge "$DB_WAIT_TIMEOUT" ]; then
        echo "ERROR: database did not become reachable within ${DB_WAIT_TIMEOUT}s." >&2
        exit 1
    fi
    sleep 2
done
echo "Database is reachable."

# --- Schema and static assets ----------------------------------------------
echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# --- Optional bootstrap superuser ------------------------------------------
# Only creates the account when it does not already exist. Requires
# DJANGO_SUPERUSER_PASSWORD as well, or the account cannot be logged into.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "Ensuring superuser '${DJANGO_SUPERUSER_USERNAME}' exists..."
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" 2>/dev/null \
        || echo "Superuser already exists, skipping."
fi

# --- Production checks ------------------------------------------------------
# `check --deploy` fails the boot on a real misconfiguration (missing SECRET_KEY,
# insecure cookies, DEBUG left on). Set SKIP_DEPLOY_CHECK=1 to bypass.
if [ "${DEBUG:-False}" != "True" ] && [ "${SKIP_DEPLOY_CHECK:-0}" != "1" ]; then
    echo "Running deployment checks..."
    python manage.py check --deploy --fail-level ERROR
fi

# --- Gunicorn ---------------------------------------------------------------
# Plotly figure generation is CPU-bound, so workers are processes, not threads.
# (2 x cores) + 1 is the usual starting point; override on a small Droplet.
WORKERS="${GUNICORN_WORKERS:-3}"
THREADS="${GUNICORN_THREADS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-120}"

echo "Starting Gunicorn on port ${PORT} (${WORKERS} workers, ${THREADS} threads)..."

exec gunicorn nat_state_vis_app.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "$WORKERS" \
    --threads "$THREADS" \
    --timeout "$TIMEOUT" \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level "${GUNICORN_LOG_LEVEL:-info}" \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
