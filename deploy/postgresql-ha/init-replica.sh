#!/usr/bin/env bash
set -euo pipefail

PRIMARY_HOST="${PRIMARY_HOST:-pg-primary}"
PRIMARY_PORT="${PRIMARY_PORT:-5432}"
REPLICA_SLOT="${REPLICA_SLOT:-replica1_slot}"
PGDATA="${PGDATA:-/var/lib/postgresql/data/pgdata}"

echo "==> Waiting for primary at ${PRIMARY_HOST}:${PRIMARY_PORT}..."
until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "${POSTGRES_USER:-ettametta}" -q; do
  sleep 2
done
echo "==> Primary is ready"

# If data directory is empty, run pg_basebackup
if [ -z "$(ls -A "$PGDATA" 2>/dev/null)" ]; then
  echo "==> Running pg_basebackup..."
  PGPASSWORD="${POSTGRES_PASSWORD:-changeme}" pg_basebackup \
    -h "$PRIMARY_HOST" \
    -p "$PRIMARY_PORT" \
    -U replicator \
    -D "$PGDATA" \
    -Fp \
    -Xs \
    -P \
    -R \
    --slot="$REPLICA_SLOT" \
    --checkpoint=fast

  echo "==> Configuring standby.signal and primary_conninfo..."
  cat > "$PGDATA/postgresql.auto.conf" <<EOF
primary_conninfo = 'host=${PRIMARY_HOST} port=${PRIMARY_PORT} user=replicator password=${POSTGRES_PASSWORD:-changeme} application_name=replica'
primary_slot_name = '${REPLICA_SLOT}'
EOF

  touch "$PGDATA/standby.signal"

  chown -R postgres:postgres "$PGDATA"
  chmod 0700 "$PGDATA"

  echo "==> Replica initialized from primary"
else
  echo "==> Data directory already exists, skipping base backup"
fi

echo "==> Starting PostgreSQL in standby mode..."
exec postgres -D "$PGDATA"
