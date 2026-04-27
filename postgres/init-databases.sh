#!/bin/bash
set -e

# Synapse requires C locale; Keycloak uses default locale
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" << SQL
CREATE DATABASE synapse
    ENCODING 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE   = 'C'
    TEMPLATE   = template0;
CREATE USER synapse WITH PASSWORD '$SYNAPSE_DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE synapse TO synapse;

CREATE DATABASE keycloak;
CREATE USER keycloak WITH PASSWORD '$KEYCLOAK_DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
SQL
