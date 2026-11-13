"""Health check endpoints for the container orchestrator and nginx.

`healthz` is a liveness probe: it answers as long as the Python process is up.
`readyz` is a readiness probe: it also opens a database connection, so it fails
while Postgres is still starting or has gone away.

Neither endpoint requires authentication and neither exposes internal detail.
"""
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache


@never_cache
def healthz(request):
    """Liveness: the WSGI worker is accepting requests."""
    return JsonResponse({"status": "ok"})


@never_cache
def readyz(request):
    """Readiness: the database answers a trivial query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse({"status": "unavailable", "database": "down"}, status=503)
    return JsonResponse({"status": "ok", "database": "up"})
