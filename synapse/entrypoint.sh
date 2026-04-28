#!/bin/sh
set -e

# Substitute ${VAR} placeholders using Python (always available in the Synapse image)
python3 - << 'PYEOF'
import os

with open('/homeserver.yaml.template') as f:
    content = f.read()

for key, val in os.environ.items():
    content = content.replace('${' + key + '}', val)

with open('/data/homeserver.yaml', 'w') as f:
    f.write(content)
PYEOF

# Generate signing key on first run
if [ ! -f /data/signing.key ]; then
    python -m synapse.app.homeserver \
        --config-path /data/homeserver.yaml \
        --generate-keys
fi

exec python -m synapse.app.homeserver --config-path /data/homeserver.yaml
