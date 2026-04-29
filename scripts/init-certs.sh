#!/bin/bash
# Run this ONCE on a fresh server before starting the full stack.
# It uses certbot standalone (no nginx needed) to obtain the initial certificates.
# After this completes, run: docker compose up -d
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Copy .env.example to .env and fill in your values."
    exit 1
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

echo "=== Let's Encrypt certificate initialisation ==="
echo ""
echo "Domains to certify:"
printf "  %s\n" "${SYNAPSE_DOMAIN}" "${KEYCLOAK_DOMAIN}" "${TURN_DOMAIN}"
[ "${MATRIX_DOMAIN}" != "${SYNAPSE_DOMAIN}" ] && printf "  %s\n" "${MATRIX_DOMAIN}"
echo ""
echo "Requirements:"
echo "  - DNS A records for all domains above must point to ${SERVER_IP}"
echo "  - Port 80 must be free on this host (stop nginx if running)"
echo ""
read -rp "Proceed? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

# Build -d args; deduplicate if MATRIX_DOMAIN == SYNAPSE_DOMAIN
DOMAIN_ARGS="-d ${SYNAPSE_DOMAIN} -d ${KEYCLOAK_DOMAIN} -d ${TURN_DOMAIN}"
[ "${MATRIX_DOMAIN}" != "${SYNAPSE_DOMAIN}" ] && \
    DOMAIN_ARGS="-d ${MATRIX_DOMAIN} ${DOMAIN_ARGS}"

# docker compose run shares the named volumes defined in docker-compose.yml
docker compose run --rm --entrypoint certbot -p 80:80 certbot \
    certonly \
    --standalone \
    --email "${CERTBOT_EMAIL}" \
    --agree-tos \
    --no-eff-email \
    ${DOMAIN_ARGS}

# Make certs readable by non-root services (coturn runs as nobody)
docker compose run --rm --entrypoint sh certbot \
    -c 'chmod -R a+rX /etc/letsencrypt/archive /etc/letsencrypt/live'

echo ""
echo "Done! Start the full stack with:"
echo "  docker compose up -d"
