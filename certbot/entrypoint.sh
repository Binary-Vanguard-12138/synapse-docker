#!/bin/sh
trap exit TERM

CERT_FILE="/etc/letsencrypt/live/${SYNAPSE_DOMAIN}/fullchain.pem"

if [ ! -f "$CERT_FILE" ]; then
    echo "[certbot] Waiting for nginx to be ready on port 80..."
    sleep 5

    echo "[certbot] Issuing initial certificates..."
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "${CERTBOT_EMAIL}" \
        --agree-tos \
        --non-interactive \
        -d "${SYNAPSE_DOMAIN}" \
        -d "${MATRIX_DOMAIN}" \
        -d "${KEYCLOAK_DOMAIN}" \
        -d "${TURN_DOMAIN}"
fi

echo "[certbot] Entering renewal loop..."
while :; do
    certbot renew --webroot --webroot-path=/var/www/certbot --quiet
    sleep 12h & wait ${!}
done
