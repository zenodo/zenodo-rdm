#!/bin/bash
# Set up streaming replication access for the local read-replica database.
#
# This script is sourced by the official postgres entrypoint on first
# initialization only (empty data directory). For databases that were already
# initialized before this file existed, run the statements below once manually
# and reload the config with `SELECT pg_reload_conf();`.
#
# NOTE: dev-only credentials, never use in production.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-'EOSQL'
    -- SUPERUSER is required so pg_basebackup can create a replication slot.
    CREATE ROLE replicator WITH REPLICATION SUPERUSER LOGIN PASSWORD 'replicator';
EOSQL

# Allow the replica container to open replication connections. This is appended
# before the final server start, so no reload is needed on fresh setups.
echo "host replication replicator all scram-sha-256" >> "$PGDATA/pg_hba.conf"
