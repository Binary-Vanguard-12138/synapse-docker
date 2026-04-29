#!/bin/bash
# Backs up all persistent state: PostgreSQL databases, Synapse data, TLS certificates, and .env.
# Output: ./backups/<timestamp>/
set -euo pipefail

cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/${TIMESTAMP}"
PROJECT=$(docker compose config 2>/dev/null | awk '/^name:/{print $2}')

mkdir -p "$BACKUP_DIR"

echo "=== Synapse stack backup — ${TIMESTAMP} ==="
echo ""

# 1. PostgreSQL logical dump (restores cleanly across minor version upgrades)
echo "[1/3] Dumping PostgreSQL databases..."
if ! docker compose ps postgres | grep -q "Up"; then
    echo "ERROR: postgres container is not running. Start the stack first."
    exit 1
fi
docker compose exec -T postgres pg_dumpall -U postgres > "${BACKUP_DIR}/postgres.sql"
echo "      → ${BACKUP_DIR}/postgres.sql"

# 2. Synapse data volume (signing key, media store)
echo "[2/3] Backing up synapse-data volume..."
docker run --rm \
    -v "${PROJECT}_synapse-data:/data:ro" \
    alpine tar czf - -C /data . > "${BACKUP_DIR}/synapse-data.tar.gz"
echo "      → ${BACKUP_DIR}/synapse-data.tar.gz"

# 3. TLS certificates (certbot-webroot is ephemeral and not worth backing up)
echo "[3/3] Backing up certbot-certs volume..."
docker run --rm \
    -v "${PROJECT}_certbot-certs:/data:ro" \
    alpine tar czf - -C /data . > "${BACKUP_DIR}/certbot-certs.tar.gz"
echo "      → ${BACKUP_DIR}/certbot-certs.tar.gz"

# .env contains all secrets and domain config
cp .env "${BACKUP_DIR}/.env"
echo "      → ${BACKUP_DIR}/.env"

echo ""
echo "Backup complete: ${BACKUP_DIR}"
echo "Total size: $(du -sh "${BACKUP_DIR}" | cut -f1)"
