#!/bin/bash
set -e

python -m marcel.init_data documents
python -m marcel.init_data admins

UVICORN_WORKERS="${UVICORN_WORKERS:-1}"
UVICORN_PORT="${UVICORN_PORT:-9000}"
UVICORN_ROOT_PATH="${UVICORN_ROOT_PATH:-/api}"

# Start the app
exec uvicorn marcel.main:app \
    --host 0.0.0.0 \
    --port "$UVICORN_PORT" \
    --root-path "$UVICORN_ROOT_PATH" \
    --workers "$UVICORN_WORKERS"
