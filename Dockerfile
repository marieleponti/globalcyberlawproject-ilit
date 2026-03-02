FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1 \
DJANGO_DEBUG=True

WORKDIR /app/src

#RUN apt-get update && apt-get install -y curl

RUN apt-get update && \
    apt-get update && apt-get install -y curl

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_HTTP_TIMEOUT=150

COPY src/requirements.txt .
RUN uv pip install -r requirements.txt --system && pip install matplotlib

COPY src/ .

EXPOSE 8000

#CMD ["./entrypoint.sh"]
#local deployment
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
#Railway deployment
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8000"]