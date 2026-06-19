# HA PostgreSQL with Streaming Replication

High-availability PostgreSQL setup using streaming replication with optional Patroni for automatic failover.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Primary   │────▶│  Replica 1  │     │  Replica 2  │
│   :5432     │────▶│   :5433     │     │   :5434     │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  PgBouncer  │
│   :6432     │
└─────────────┘
```

## Quick Start

### 1. Start the Cluster

```bash
cd deploy/postgresql-ha

# Copy and edit environment
cp .env.example .env
# Edit .env with your passwords

# Start primary + replicas
docker compose -f docker-compose.ha.yml up -d
```

### 2. Initialize Replicas

```bash
# For each replica, run the init script
docker exec pg-replica-1 bash -c '
  PGPASSWORD=changeme pg_basebackup \
    -h pg-primary -p 5432 -U replicator \
    -D /var/lib/postgresql/data/pgdata \
    -Fp -Xs -P -R \
    --slot=replica1_slot --checkpoint=fast
  touch /var/lib/postgresql/data/pgdata/standby.signal
  chown -R postgres:postgres /var/lib/postgresql/data/pgdata
'
```

### 3. Verify Replication

```bash
# On primary
docker exec pg-primary psql -U ettametta -c "SELECT * FROM pg_stat_replication;"

# On replica
docker exec pg-replica-1 psql -U ettametta -c "SELECT pg_is_in_recovery();"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | ettametta | Database user |
| `POSTGRES_PASSWORD` | changeme | Database password |
| `POSTGRES_DB` | ettametta | Database name |

### PgBouncer

PgBouncer provides connection pooling on port 6432. Configure your application to connect to `localhost:6432` for connection pooling.

## Patroni Failover (Optional)

For automatic failover, deploy with Patroni + etcd:

```bash
docker compose -f docker-compose.ha.yml -f docker-compose.patroni.yml up -d
```

## Monitoring

```bash
# Check replication lag
docker exec pg-primary psql -U ettametta -c "
  SELECT client_addr, state, sent_lsn, replay_lag
  FROM pg_stat_replication;
"
```
