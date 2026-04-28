#!/bin/bash
# Tears down the entire stack: containers, networks, and all named volumes.
# All data (Postgres databases, Synapse media, Let's Encrypt certificates) will be lost.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Synapse stack uninstall ==="
echo ""
echo "This will permanently delete:"
echo "  - All containers (synapse, keycloak, nginx, certbot, coturn, postgres)"
echo "  - All named volumes (postgres-data, synapse-data, certbot-certs, certbot-webroot)"
echo "  - Docker networks created by this compose project"
echo ""
echo "This cannot be undone."
echo ""
read -rp "Type 'yes' to confirm: " confirm
[ "$confirm" = "yes" ] || { echo "Aborted."; exit 0; }

echo ""
echo "Stopping and removing containers, networks, and volumes..."
docker compose down --volumes --remove-orphans

echo ""
echo "Done. All containers, networks, and volumes have been removed."
