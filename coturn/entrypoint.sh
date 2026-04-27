#!/bin/sh
set -e

mkdir -p /etc/coturn

# Substitute ${VAR} placeholders with awk ENVIRON (portable, no extra packages needed)
awk '{
    for (var in ENVIRON)
        gsub("[$][{]" var "[}]", ENVIRON[var])
    print
}' /turnserver.conf.template > /etc/coturn/turnserver.conf

exec turnserver -c /etc/coturn/turnserver.conf
