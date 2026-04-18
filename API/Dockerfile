FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requeriments.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requeriments.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 8007

ENTRYPOINT ["/app/docker/entrypoint.sh"]
