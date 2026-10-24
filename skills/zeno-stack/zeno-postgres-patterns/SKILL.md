---
name: zeno-postgres-patterns
description: >
  Operational PostgreSQL patterns — index-type selection, slow-query diagnosis, Row Level
  Security recipes, and connection/timeout configuration. Schema design and SQL code
  standards are owned by code-standards/database-data-modeling/postgres (it wins on those);
  for schema-change rollout safety (migrations, zero-downtime changes) see
  zeno-database-migrations. Trigger on: "which index should I use", "slow query",
  "EXPLAIN output", "Row Level Security", "RLS policy", "composite index", "GIN index",
  "UPSERT", "cursor pagination", "queue table in Postgres", "Postgres connection limits",
  "table bloat", "postgres timeout".
---

# PostgreSQL Patterns

Query and schema patterns for PostgreSQL, covering index selection, data types, common
query shapes, anti-pattern detection queries, and production configuration defaults.
For how to *ship* a schema change safely, hand off to `zeno-database-migrations`.

**Split with `code-standards`:** `code-standards/database-data-modeling/postgres` owns
schema-design and SQL code standards (modeling, normalization, migration style, PL/pgSQL);
this leaf owns operational query patterns (index choice, slow-query diagnosis, RLS recipes,
connection/timeout config). On a schema-design-standards question, `code-standards` wins.

## When to reach for this skill

- Writing a query or designing a table schema
- Picking an index type for a query pattern
- Diagnosing a slow query or table bloat
- Implementing Row Level Security
- Setting connection, timeout, or memory configuration

## Index selection

| Query pattern | Index type | Example |
|---|---|---|
| `WHERE col = value` | B-tree (default) | `CREATE INDEX idx ON t (col)` |
| `WHERE col > value` | B-tree | `CREATE INDEX idx ON t (col)` |
| `WHERE a = x AND b > y` | Composite | `CREATE INDEX idx ON t (a, b)` |
| `WHERE jsonb @> '{}'` | GIN | `CREATE INDEX idx ON t USING gin (col)` |
| `WHERE tsv @@ query` | GIN | `CREATE INDEX idx ON t USING gin (col)` |
| Time-series range scans | BRIN | `CREATE INDEX idx ON t USING brin (col)` |
| Geometric/spatial, range types, nearest-neighbour | GiST | `CREATE INDEX idx ON t USING gist (col)` |
| Hierarchical or sparse structures | SP-GiST | `CREATE INDEX idx ON t USING spgist (col)` |
| Equality-only, never ordered | Hash | `CREATE INDEX idx ON t USING hash (col)` — rarely beats B-tree; prefer B-tree unless measured |

```sql
-- Composite index: equality columns first, then range columns
CREATE INDEX idx ON orders (status, created_at);
-- Serves: WHERE status = 'pending' AND created_at > '2024-01-01'

-- Covering index: avoids a table lookup for the listed columns
CREATE INDEX idx ON users (email) INCLUDE (name, created_at);

-- Partial index: smaller, faster, only covers the rows that matter
CREATE INDEX idx ON users (email) WHERE deleted_at IS NULL;
```

## Data types

Data-type selection is a schema-design standard owned by
`code-standards/database-data-modeling/postgres` §3 (bigint IDs, text over varchar(255),
timestamptz, numeric for money) — consult it there rather than here.

## Common query patterns

```sql
-- RLS policy: wrap auth.uid() in a SELECT so the planner caches it per statement
-- instead of re-evaluating per row
CREATE POLICY policy ON orders
  USING ((SELECT auth.uid()) = user_id);

-- Multi-tenant isolation: the policy reads a per-transaction setting, so the
-- application must establish it at transaction start (SET LOCAL, not SET —
-- SET would leak the tenant across pooled connections).
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;   -- the owner does not bypass policies
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
SET LOCAL app.tenant_id = '42';

-- UPSERT
INSERT INTO settings (user_id, key, value)
VALUES (123, 'theme', 'dark')
ON CONFLICT (user_id, key)
DO UPDATE SET value = EXCLUDED.value;

-- Cursor pagination — O(1) per page, unlike OFFSET which is O(n)
SELECT * FROM products WHERE id > $last_id ORDER BY id LIMIT 20;

-- Queue processing: claim one pending row, skip rows other workers already locked
UPDATE jobs SET status = 'processing'
WHERE id = (
  SELECT id FROM jobs WHERE status = 'pending'
  ORDER BY created_at LIMIT 1
  FOR UPDATE SKIP LOCKED
) RETURNING *;
```

## Finding problems

### Reading an EXPLAIN plan

Always `EXPLAIN (ANALYZE, BUFFERS)` before adding an index or rewriting a query — and wrap DML in
a rolled-back transaction so the analysis has no side effects.

| Signal in the plan | Problem | Fix |
|---|---|---|
| `Seq Scan` on a large table | Missing index | Add a targeted index |
| `Nested Loop` with a large outer set | Cartesian-join risk | Check join conditions; index the FK |
| Estimated rows ≪ actual rows | Stale statistics | `ANALYZE <table>` |
| `Buffers: shared hit=0` | Cold cache / poor locality | Tune `shared_buffers`, review access patterns |
| `Sort` with `external merge` | `work_mem` too small for the sort | Raise `work_mem` for the session |

```sql
BEGIN;
EXPLAIN (ANALYZE, BUFFERS) UPDATE orders SET status = 'archived'
  WHERE created_at < NOW() - INTERVAL '1 year';
ROLLBACK;
```


```sql
-- Unindexed foreign keys — every FK should usually have a supporting index
SELECT conrelid::regclass, a.attname
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
    SELECT 1 FROM pg_index i
    WHERE i.indrelid = c.conrelid AND a.attnum = ANY(i.indkey)
  );

-- Slow queries (requires pg_stat_statements)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY mean_exec_time DESC;

-- Table bloat — dead tuples piling up without vacuum keeping pace
SELECT relname, n_dead_tup, last_vacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

## Production configuration baseline

```sql
-- Connection limits (tune to available RAM)
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET work_mem = '8MB';

-- Timeouts — a stuck client should not be able to hold locks or a connection forever
ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
ALTER SYSTEM SET statement_timeout = '30s';

-- Monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Security defaults — nobody gets schema access just by being a role
REVOKE ALL ON SCHEMA public FROM public;

SELECT pg_reload_conf();
```

Memory, write and planner settings — the other half of what a production baseline covers:

```ini
# Memory
shared_buffers = 25%_of_RAM          # e.g. 4GB on a 16GB host
effective_cache_size = 75%_of_RAM    # planner hint about OS cache
# work_mem is set once, above (ALTER SYSTEM SET work_mem = '8MB'). Raise it per-session for
# a known-heavy query (SET LOCAL work_mem = '64MB') rather than globally — it is allocated
# PER sort/hash operation, so a global bump multiplies by concurrent operations.

# Write path
wal_buffers = 64MB
checkpoint_completion_target = 0.9
synchronous_commit = on              # 'off' only for genuinely non-critical async workloads

# Planner — defaults assume spinning disks
random_page_cost = 1.1               # SSD; leave at 4.0 for rotational
effective_io_concurrency = 200       # SSD; 2 for rotational

# Autovacuum — more aggressive on write-heavy tables
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.02
```

## Connection pooling and logging

Always use a connection pooler between application and PostgreSQL. PostgreSQL spawns a process per connection — unbounded connections degrade performance.

### PgBouncer Configuration (`pgbouncer.ini`)

```ini
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
pool_mode = transaction            # recommended for most web applications
max_client_conn = 1000             # max connections PgBouncer accepts
default_pool_size = 20             # server connections per db/user pair
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

server_reset_query = DISCARD ALL   # clean state on connection return
server_tls_sslmode = require       # enforce TLS to PostgreSQL
client_tls_sslmode = require       # enforce TLS from application

log_connections = 1
log_disconnections = 1
```

### Pooling Mode Decision

| Mode | When to Use | Caveat |
|---|---|---|
| `transaction` | Most web apps with stateless requests | No session-level features (advisory locks, `SET LOCAL`, prepared statements) |
| `session` | Long-lived connections, session state required | Less efficient; one server conn per client |
| `statement` | Rarely needed; single-statement transactions only | Disallows multi-statement transactions |

### Monitoring PgBouncer

```sql
-- Connect to pgbouncer admin database
SHOW POOLS;    -- active, idle, waiting clients per pool
SHOW STATS;    -- request rates and durations
SHOW CLIENTS;  -- connected clients

-- Alert when cl_waiting > 0 for extended period (pool exhaustion)
```

---

### Logging Configuration

```ini
# postgresql.conf

log_min_duration_statement = 1000   # log queries taking > 1s
log_checkpoints = on
log_connections = off               # avoid log flood in high-traffic apps
log_disconnections = off
log_lock_waits = on
log_temp_files = 0                  # log all temp file usage (unexpected disk spills)
log_autovacuum_min_duration = 250   # log slow autovacuum runs
```


## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `OFFSET`-based pagination on large tables | Cursor pagination (`WHERE id > $last_id`) |
| Unwrapped `auth.uid()` in an RLS policy | Wrap in `(SELECT auth.uid())` so it's evaluated once per statement, not per row |
| Foreign key with no supporting index | Add one — every FK is a join or cascade-delete candidate |
| `float` for money | `numeric(10,2)` |
| No `statement_timeout` / `idle_in_transaction_session_timeout` | Set both so a stuck client can't hold locks indefinitely |
| Random UUID as primary key on a hot table | `bigint` identity, or a time-sortable UUID variant, for index locality |
| Adding an index without checking the query's actual `WHERE`/`ORDER BY` shape | Match the index type to the query pattern (see table above) |

## Pre-flight checklist — run before delivering any PostgreSQL schema or query change

- [ ] Every new foreign key has a supporting index
- [ ] Index type matches the query pattern it's meant to serve (B-tree/GIN/BRIN/composite/partial)
- [ ] Money uses `numeric`, timestamps use `timestamptz`, IDs use `bigint`
- [ ] Any RLS policy wraps per-row function calls (`auth.uid()`, etc.) in a `SELECT`
- [ ] Pagination on a potentially large result set uses a cursor, not `OFFSET`
- [ ] `statement_timeout` and `idle_in_transaction_session_timeout` are set for production
- [ ] Schema changes are routed through `zeno-database-migrations`, not applied by hand
