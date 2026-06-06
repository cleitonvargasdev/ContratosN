#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
API_DIR="$SCRIPT_DIR"
FRONTEND_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../FRONTEND" 2>/dev/null && pwd || true)

API_HOST=${API_HOST:-127.0.0.1}
API_PORT=${API_PORT:-8007}
API_RELOAD=${API_RELOAD:-0}
FRONTEND_HOST=${FRONTEND_HOST:-127.0.0.1}
FRONTEND_PORT=${FRONTEND_PORT:-5174}

if [ -x "$API_DIR/.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="$API_DIR/.venv/Scripts/python.exe"
elif [ -x "$API_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$API_DIR/.venv/bin/python"
else
    echo "Virtual environment python not found in $API_DIR/.venv" >&2
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Frontend path not found: $SCRIPT_DIR/../FRONTEND" >&2
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "npm is not available in PATH" >&2
    exit 1
fi

cleanup() {
    status=$?

    if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
        kill "$API_PID" 2>/dev/null || true
    fi

    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi

    wait 2>/dev/null || true
    exit "$status"
}

trap cleanup INT TERM EXIT

echo "Starting API at http://$API_HOST:$API_PORT"
(
    cd "$API_DIR"
    UVICORN_ARGS="--host $API_HOST --port $API_PORT"
    if [ "$API_RELOAD" = "1" ]; then
        UVICORN_ARGS="$UVICORN_ARGS --reload"
    fi
    PYTHONPATH="$API_DIR" exec "$PYTHON_BIN" -m uvicorn app.main:app $UVICORN_ARGS
) &
API_PID=$!

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "node_modules not found. Running npm install..."
    (
        cd "$FRONTEND_DIR"
        npm install
    )
fi

echo "Starting frontend at http://$FRONTEND_HOST:$FRONTEND_PORT"
(
    cd "$FRONTEND_DIR"
    exec npm run dev -- --host="$FRONTEND_HOST" --port="$FRONTEND_PORT"
) &
FRONTEND_PID=$!

wait "$API_PID" "$FRONTEND_PID"