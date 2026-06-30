#!/bin/sh
# Inject BACKEND_URL into the built HTML at container startup.
# This lets the same Docker image run in any environment.
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
sed -i "s|%%BACKEND_URL%%|$BACKEND_URL|g" /usr/share/nginx/html/index.html
exec nginx -g "daemon off;"
