#!/bin/sh
set -e

: "${FLASK_WEB_PORT:=8000}"
: "${FASTAPI_WEB_PORT:=8000}"

# Debug: show what hostnames are being substituted
echo "[entrypoint] FLASK_WEB_HOST=${FLASK_WEB_HOST}"
echo "[entrypoint] FASTAPI_WEB_HOST=${FASTAPI_WEB_HOST}"
echo "[entrypoint] FLASK_WEB_PORT=${FLASK_WEB_PORT}"
echo "[entrypoint] FASTAPI_WEB_PORT=${FASTAPI_WEB_PORT}"

# Generate config from template using sed
sed "s|@FLASK_WEB_HOST@|${FLASK_WEB_HOST}|g; s|@FASTAPI_WEB_HOST@|${FASTAPI_WEB_HOST}|g; s|@FLASK_WEB_PORT@|${FLASK_WEB_PORT}|g; s|@FASTAPI_WEB_PORT@|${FASTAPI_WEB_PORT}|g" \
  /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Debug: show the generated upstream server lines
echo "[entrypoint] Generated upstream config:"
grep -E "server [^{]" /etc/nginx/conf.d/default.conf || true

# Start nginx
exec nginx -g "daemon off;"
