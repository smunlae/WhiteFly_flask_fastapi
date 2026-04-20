#!/bin/sh
set -e

# Generate config from template using sed
sed "s|@FLASK_WEB_HOST@|${FLASK_WEB_HOST}|g; s|@FASTAPI_WEB_HOST@|${FASTAPI_WEB_HOST}|g" \
  /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g "daemon off;"
