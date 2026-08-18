#!/bin/sh

export PYTHONPATH=/app/src

# Si PORT no existe (local), usa 8000
PORT=${PORT:-8000}

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if env vars exist..."
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser \
        --noinput \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

echo "Starting Gunicorn on port $PORT..."

exec gunicorn nat_state_vis_app.wsgi:application --bind 0.0.0.0:$PORT