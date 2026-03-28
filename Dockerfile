FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /usr/src/influxnews

# Install system dependencies and create cron log directory
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /cron && \
    touch /cron/influxnews.log

# Copy dependency file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./influxnews .
COPY ./firebase-creds.json accounts/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /usr/src/influxnews /cron

USER appuser

EXPOSE 8000

CMD service cron start && \
    python manage.py crontab add && \
    gunicorn influxnews.wsgi:application --bind 0.0.0.0:${PORT}