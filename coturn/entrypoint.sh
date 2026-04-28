#!/bin/sh
set -e

# Substitute ${VAR} placeholders with awk ENVIRON (portable, no extra packages needed)
awk '{
    for (var in ENVIRON)
        gsub("[$][{]" var "[}]", ENVIRON[var])
    print
}' /turnserver.conf.template > /tmp/turnserver.conf

exec turnserver -c /tmp/turnserver.conf
