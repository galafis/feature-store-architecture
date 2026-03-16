FROM python:3.11-slim

LABEL maintainer="Gabriel Demetrios Lafis <https://github.com/galafis>"
LABEL description="Feature Store Architecture - Centralized ML Feature Management"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379
ENV OFFLINE_STORE_PATH=/app/data/offline_store

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "src.feature_serving_api"]
