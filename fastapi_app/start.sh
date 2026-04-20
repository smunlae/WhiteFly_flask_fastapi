#!/usr/bin/env sh
set -e

PORT="${PORT:-8000}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --workers "${UVICORN_WORKERS:-2}" --proxy-headers
