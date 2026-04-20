#!/usr/bin/env sh
set -e

PORT="${PORT:-8000}"
exec gunicorn --bind "0.0.0.0:${PORT}" --workers "${GUNICORN_WORKERS:-2}" --threads "${GUNICORN_THREADS:-4}" run:app
