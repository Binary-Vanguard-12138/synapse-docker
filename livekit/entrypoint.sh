#!/bin/sh
set -e

awk '{
    for (var in ENVIRON)
        gsub("[$][{]" var "[}]", ENVIRON[var])
    print
}' /config.yaml.template > /data/config.yaml
