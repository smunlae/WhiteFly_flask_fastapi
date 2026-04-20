FROM nginx:latest

# Install gettext for envsubst
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

# Copy the template config
COPY nginx.conf /etc/nginx/nginx.conf.template

# Create entrypoint script
RUN echo '#!/bin/sh\nenvsubst < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf\nnginx -g "daemon off;"' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
