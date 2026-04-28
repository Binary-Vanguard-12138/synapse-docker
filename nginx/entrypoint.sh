#!/bin/sh
set -e

CERT_FILE="/etc/letsencrypt/live/${MATRIX_DOMAIN}/fullchain.pem"

# Bootstrap: certs don't exist yet on first run.
# Start HTTP-only so certbot can serve the ACME challenge, then reload to HTTPS.
if [ ! -f "$CERT_FILE" ]; then
    echo "[nginx] Certificates not found — starting HTTP-only for ACME bootstrap..."

    cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / {
        return 503 "Awaiting SSL certificate provisioning";
    }
}
EOF

    nginx

    echo "[nginx] Waiting for ${CERT_FILE} ... (run scripts/init-certs.sh if not done yet)"
    while [ ! -f "$CERT_FILE" ]; do
        sleep 5
    done

    echo "[nginx] Certificates found — switching to HTTPS config..."
    nginx -s quit
    sleep 2
fi

envsubst '${SYNAPSE_DOMAIN} ${MATRIX_DOMAIN} ${KEYCLOAK_DOMAIN} ${TURN_DOMAIN}' \
  < /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
