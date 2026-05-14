#!/bin/sh
set -e

apk add --no-cache openssl >/dev/null 2>&1

# Substitute ${VAR} placeholders in config template
awk '{
    for (var in ENVIRON)
        gsub("[$][{]" var "[}]", ENVIRON[var])
    print
}' /config.yaml.template > /data/config.yaml

# Generate RSA signing key on first run
if [ ! -f /data/keys.yaml ]; then
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 > /data/signing.key 2>/dev/null
    KID=$(openssl rand -hex 6)
    printf 'secrets:\n  keys:\n    - kid: "%s"\n      key: |\n' "$KID" > /data/keys.yaml
    sed 's/^/        /' /data/signing.key >> /data/keys.yaml
    rm /data/signing.key
fi
