#!/bin/sh
# Ajusta PYTHONPATH
export PYTHONPATH=/app/src

# Aplica migraciones automáticamente
python manage.py migrate --noinput

# Recopila archivos estáticos
python manage.py collectstatic --noinput

# Levanta Gunicorn en el puerto que asigna Railway
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT