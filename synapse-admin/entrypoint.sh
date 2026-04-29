#!/bin/sh
trap exit TERM

INSTALL_DIR="/var/www/synapse-admin"
VERSION_FILE="${INSTALL_DIR}/.version"

install_latest() {
    echo "[synapse-admin] Checking for latest release..."
    LATEST=$(wget -qO- "https://api.github.com/repos/Awesome-Technologies/synapse-admin/releases/latest" \
        | grep '"tag_name"' | cut -d'"' -f4)

    if [ -z "$LATEST" ]; then
        echo "[synapse-admin] ERROR: Could not determine latest version. Will retry in 1h."
        return 1
    fi

    if [ -f "$VERSION_FILE" ] && [ "$(cat "$VERSION_FILE")" = "$LATEST" ]; then
        echo "[synapse-admin] Already up to date (${LATEST})."
        return 0
    fi

    echo "[synapse-admin] Downloading synapse-admin ${LATEST}..."
    cd /tmp
    wget -q "https://github.com/Awesome-Technologies/synapse-admin/releases/download/${LATEST}/synapse-admin-${LATEST}.tar.gz"
    tar -xzf "synapse-admin-${LATEST}.tar.gz"
    rm "synapse-admin-${LATEST}.tar.gz"

    rm -rf "${INSTALL_DIR:?}"/*
    mv "synapse-admin-${LATEST}/"* "${INSTALL_DIR}/"
    rm -rf "synapse-admin-${LATEST}"

    cat > "${INSTALL_DIR}/config.json" << EOF
{
  "restrictBaseUrl": "https://${SYNAPSE_DOMAIN}"
}
EOF

    echo "$LATEST" > "$VERSION_FILE"
    echo "[synapse-admin] Installed synapse-admin ${LATEST}."
}

mkdir -p "$INSTALL_DIR"

while :; do
    install_latest
    sleep 24h & wait ${!}
done
