FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=True \
    PYTHONPATH=/app/src

WORKDIR /app/src

RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_HTTP_TIMEOUT=150

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn matplotlib
#entorno dev
#RUN uv pip install -r requirements.txt --system && pip install matplotlib

COPY src/ .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Crear usuario no-root para seguridad
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

EXPOSE 8000

#CMD ["./entrypoint.sh"]
#local deployment
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
#Railway deployment
CMD ["/app/entrypoint.sh"]