#!/bin/sh
set -eu

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

python - <<'PY'
import os
import time

import psycopg2
from app.core.config import settings

host = os.environ["DB_HOST"]
port = int(os.environ.get("DB_PORT", "5432"))
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
database = settings.tenant_registry_db_name if settings.tenancy_enabled else settings.db_name

deadline = time.time() + 60
last_error = None

while time.time() < deadline:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=database,
        )
        conn.close()
        break
    except Exception as exc:
        last_error = exc
        time.sleep(2)
else:
    raise SystemExit(f"PostgreSQL did not become available in time: {last_error}")
PY

echo "Running Alembic migrations..."
python -m scripts.migrate_databases

echo "Starting API..."
exec "$@"
