#!/bin/sh
set -e

# Substitute only our four custom variables.
# Single-quoted SHELL-FORMAT means $host, $remote_addr, etc. are untouched by envsubst.
envsubst '${SYNAPSE_DOMAIN} ${MATRIX_DOMAIN} ${KEYCLOAK_DOMAIN} ${TURN_DOMAIN}' \
  < /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
