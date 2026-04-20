#!/bin/sh
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf
rm /etc/nginx/nginx.conf
nginx -g "daemon off;"
