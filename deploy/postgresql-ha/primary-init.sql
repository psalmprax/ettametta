CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'changeme';
CREATE ROLE pgbouncer WITH LOGIN PASSWORD 'changeme';

-- Create replication slot for each replica
SELECT pg_create_physical_replication_slot('replica1_slot');
SELECT pg_create_physical_replication_slot('replica2_slot');

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ettametta TO replicator;
GRANT ALL PRIVILEGES ON DATABASE ettametta TO pgbouncer;
