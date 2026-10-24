# PostgreSQL & Data Modeling — Operations

Extracted from `../SKILL.md`: connection pooling (§10), observability & monitoring
(§11), stored procedures & functions (§12), and advanced partitioning & isolation
(§15). Section numbers match the stubs in `SKILL.md`, so §-references resolve here.

---

## 10. Connection Pooling with PgBouncer

Connection pooling and its `pgbouncer.ini` configuration are **operational** concerns owned by
`zeno-stack/zeno-postgres-patterns` (see its "Connection pooling and logging" section) — this
skill's SKILL.md cedes connection/timeout configuration there explicitly. Kept here only as the
schema-design-relevant fact: PostgreSQL spawns a process per connection, so an unbounded
connection count degrades the server regardless of how well the schema is designed.

## 11. Observability & Monitoring

### Key System Views

```sql
-- Active queries (find long-running queries)
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < NOW() - INTERVAL '5 seconds'
ORDER BY duration DESC;

-- Terminate a runaway query
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE pid <> pg_backend_pid()
  AND query_start < NOW() - INTERVAL '30 minutes';

-- Table access statistics
SELECT relname, seq_scan, idx_scan, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;

-- Slowest queries (requires pg_stat_statements extension)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Recommended Monitoring Metrics

| Metric | Alert Threshold | Meaning |
|---|---|---|
| `pg_stat_activity.state = 'active'` > X | > 80% of `max_connections` | Connection saturation |
| Query duration | > 1s for OLTP, > 30s for OLAP | Slow query alert |
| `n_dead_tup` ratio | > 20% | Autovacuum not keeping up |
| Replication lag | > 10s | Replica falling behind |
| `pg_stat_bgwriter.buffers_backend` | Rising trend | Too many dirty page flushes |
| Lock waits (`pg_locks`) | Any long-held locks | Possible deadlock or contention |

### Logging Configuration

`postgresql.conf` logging settings are owned by `zeno-stack/zeno-postgres-patterns` ("Connection pooling and logging") — the same cession this skill's SKILL.md makes for connection/timeout configuration.

---

## 12. Stored Procedures & Functions

For function/procedure internals beyond this section — volatility (`IMMUTABLE`/`STABLE`/
`VOLATILE`), `PARALLEL`/`LEAKPROOF` labels, the plan-cache 6th-execution cliff, why exception
blocks in loops are dangerous, dynamic SQL safety, triggers, and the full `SECURITY DEFINER`
hardening checklist — read `../frameworks/plpgsql.md`. That file also has the
complete `ALTER TABLE` lock-level cheat sheet referenced in the Migrations section above.

```sql
-- ✅ Use LANGUAGE plpgsql for procedural logic; SQL for simple expressions
CREATE OR REPLACE FUNCTION fn_transfer_funds(
    p_from_account_id BIGINT,
    p_to_account_id   BIGINT,
    p_amount          NUMERIC(12, 2)
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER          -- runs with function owner's privileges
SET search_path = ''      -- empty + schema-qualify everything below: the safest option
AS $$
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive, got %', p_amount;
    END IF;

    UPDATE public.accounts SET balance = balance - p_amount
    WHERE id = p_from_account_id AND balance >= p_amount;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Insufficient funds or account % not found', p_from_account_id;
    END IF;

    UPDATE public.accounts SET balance = balance + p_amount
    WHERE id = p_to_account_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Destination account % not found', p_to_account_id;
    END IF;
END;
$$;
```

**Rules:**

- Use `SECURITY DEFINER` with **extreme care** — set `search_path = ''` and schema-qualify
  every reference (safest), and `REVOKE EXECUTE ... FROM PUBLIC` immediately after creation.
  See `../frameworks/plpgsql.md` for the full hardening checklist.
- Prefer `SECURITY INVOKER` (default) whenever possible.
- Keep functions small and focused. Complex orchestration belongs in the application layer.
- Use `RAISE EXCEPTION` with explicit error codes and messages for debugging.
- Never use `RAISE NOTICE` in production functions — use application-layer logging instead.

---

## 15. Advanced: Partitioning & Isolation

### Table Partitioning

Consider partitioning tables that exceed ~100 GB or contain time-series data. Use native **declarative partitioning** (PostgreSQL 10+):

```sql
-- Range partitioning by date (most common strategy)
CREATE TABLE events (
    id          bigint GENERATED ALWAYS AS IDENTITY,
    event_type  text NOT NULL,
    payload     jsonb,
    created_at  timestamptz NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_q1 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE events_2024_q2 PARTITION OF events
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

### Transaction Isolation Levels

Choose the isolation level appropriate for the workload:

| Level | When to Use |
| --- | --- |
| `READ COMMITTED` (default) | General-purpose OLTP — reads committed data at statement time |
| `REPEATABLE READ` | Needs a consistent snapshot across multiple statements within a transaction |
| `SERIALIZABLE` | Financial transactions requiring strict correctness (highest consistency, highest cost) |

**Key rules:**

- Keep transactions **short** — long-running transactions hold locks and cause table bloat.
- Set `idle_in_transaction_session_timeout` to automatically terminate stuck transactions.
- Prefer `READ COMMITTED` for most web applications; escalate to `SERIALIZABLE` only for ledger/accounting operations.
