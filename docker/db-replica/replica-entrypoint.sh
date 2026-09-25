#!/bin/bash
# Entrypoint for the local streaming-replica database.
#
# On first start (empty data directory) it waits for the primary, bootstraps
# via pg_basebackup (which writes standby.signal and primary_conninfo), and
# then hands over to the official postgres entrypoint. On later starts the
# existing data directory is reused and the replica just reconnects.
#
# Configuration via environment (defaults suit docker-services.yml):
#   PRIMARY_HOST, PRIMARY_PORT, REPLICATOR_PASSWORD, REPLICATION_SLOT, PGDATA
set -e

: "${PGDATA:=/var/lib/postgresql/data/pgdata}"
: "${PRIMARY_HOST:=db}"
: "${PRIMARY_PORT:=5432}"
: "${REPLICATOR_PASSWORD:=replicator}"
: "${REPLICATION_SLOT:=zenodo_replica_slot}"

if [ ! -f "$PGDATA/standby.signal" ]; then
    echo "Replica data directory is empty, waiting for primary ($PRIMARY_HOST:$PRIMARY_PORT)..."
    until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -q; do
        sleep 2
    done
    echo "Primary is ready, running pg_basebackup..."
    mkdir -p "$PGDATA"
    chown -R postgres:postgres "$PGDATA"
    chmod 700 "$PGDATA"
    # shellcheck disable=SC2029
    PGPASSWORD="$REPLICATOR_PASSWORD" gosu postgres pg_basebackup \
        -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U replicator \
        -D "$PGDATA" -Fp -Xs -P -R -C -S "$REPLICATION_SLOT"
    echo "Base backup complete, starting replica."
fi

exec docker-entrypoint.sh "$@"
