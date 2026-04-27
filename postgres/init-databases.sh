#!/bin/bash
set -e

# Synapse requires C locale; Keycloak uses default locale
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" << SQL
# Create synapse user and database owned by that user
CREATE USER synapse WITH PASSWORD '$SYNAPSE_DB_PASSWORD';
CREATE DATABASE synapse
    WITH OWNER = synapse
    ENCODING 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE   = 'C'
    TEMPLATE   = template0;

-- Ensure synapse can use the public schema
\connect synapse
ALTER SCHEMA public OWNER TO synapse;
GRANT ALL ON SCHEMA public TO synapse;

-- Create keycloak user and database owned by that user
CREATE USER keycloak WITH PASSWORD '$KEYCLOAK_DB_PASSWORD';
CREATE DATABASE keycloak
    WITH OWNER = keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
SQL
