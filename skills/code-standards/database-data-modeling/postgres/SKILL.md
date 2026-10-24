---
name: postgres
description: >
  Production-grade PostgreSQL and data modeling standards. Use whenever designing, reviewing,
  or refactoring PostgreSQL schemas, SQL queries, or database migrations. Trigger on: "design
  a database", "create a table", "PostgreSQL schema", "data model", "index strategy", "SQL
  query review", "database migration", "normalize this schema", "postgres performance", RLS,
  RBAC, connection pooling, or any PostgreSQL or relational database design task.
---

# PostgreSQL & Data Modeling Standards

As an AI assistant, you must adhere strictly to the following PostgreSQL and data modeling best practices when generating, reviewing, or refactoring database schemas, migrations, and SQL code.

Anchored to **PostgreSQL 18** (current stable as of writing). Version-gated features (`uuidv7()`,
`VIRTUAL` generated columns, native temporal constraints, `OLD`/`NEW` in `RETURNING`, B-tree
skip scan) are flagged inline with the version they need — everything else applies back through
PG14. Re-verify version-specific claims against the docs for your installed minor release
before treating them as current.

For PL/pgSQL function/procedure/trigger internals (volatility, plan caching, exception-block
subtransactions, dynamic SQL safety, `SECURITY DEFINER` hardening) and the full `ALTER TABLE`
lock-level cheat sheet, see `frameworks/plpgsql.md` — load it before writing or
reviewing any PL/pgSQL code or a migration touching a table with live traffic.

Operational query patterns (index-type selection tables, slow-query diagnosis, RLS recipes,
connection/timeout configuration) live in `zeno-stack/zeno-postgres-patterns` — this skill
owns schema-design and SQL code standards and wins on those; that leaf owns the operational
side.

---

## 1. Guiding Principles

These principles should inform every database design and SQL decision:

```text
Clarity over cleverness.
Constraints are your safety net — use them liberally.
Normalize first, denormalize with justification.
Explicit is better than implicit.
Name things so a newcomer can understand the schema without a guide.
Measure before you optimize — use EXPLAIN ANALYZE.
Schema changes should be versioned and reversible.
Data integrity is non-negotiable.
Every table deserves a primary key.
Design for the queries you will run, not the ones you might.
```

---

## 2. Naming Conventions

Consistency throughout the entire schema is paramount. Follow these rules without exception:

| Object | Convention | Example |
|---|---|---|
| Tables | `snake_case`, plural nouns | `users`, `order_items` |
| Columns | `snake_case`, singular nouns | `user_id`, `created_at` |
| Primary Keys | `id` or `<table_singular>_id` | `id`, `user_id` |
| Foreign Keys | `<referenced_table_singular>_id` | `user_id`, `product_id` |
| Indexes | `idx_<table>_<columns>` | `idx_users_email` |
| Unique Indexes | `uq_<table>_<columns>` | `uq_users_email` |
| Sequences | `<table>_<column>_seq` | `users_id_seq` |
| Views | `v_<descriptive_name>` | `v_active_users` |
| Materialized Views | `mv_<descriptive_name>` | `mv_monthly_revenue` |
| Functions | `snake_case` verb phrases | `get_user_by_email`, `calculate_discount` |
| Triggers | `trg_<table>_<event>` | `trg_users_updated_at` |
| Constraints | `chk_<table>_<column>` | `chk_users_age` |
| Schemas | `snake_case` | `public`, `audit`, `payments` |

**Key Rules:**

- **Always use lowercase.** PostgreSQL folds unquoted identifiers to lowercase. Never rely on double-quoted mixed-case identifiers.
- **Never use reserved keywords** as names. Query reserved words via `SELECT * FROM pg_get_keywords() WHERE catcode = 'R';`
- **Maximum 63 bytes** for any identifier name (PostgreSQL hard limit).
- **Prefix boolean columns** with `is_`, `has_`, or `can_` — e.g., `is_active`, `has_verified_email`.
- **Avoid generic column names** like `value`, `data`, `info`. Be explicit: `invoice_amount`, `shipping_address`.

```sql
-- ✅ Correct
CREATE TABLE order_items (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      BIGINT NOT NULL REFERENCES orders(id),
    product_id    BIGINT NOT NULL REFERENCES products(id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10, 2) NOT NULL,
    is_returned   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ❌ Wrong: mixed case, ambiguous names, no constraints
CREATE TABLE OrderItem (
    ID    SERIAL,
    data  TEXT,
    value NUMERIC
);
```

---

## 3. Data Types

Choosing the right data type avoids unnecessary storage waste, type coercions, and logic bugs.

### Primary Key Strategy

```sql
-- ✅ Option A: BIGINT IDENTITY (Best for high-volume OLTP inserts)
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY

-- ✅ Option B: Native UUID v7 (Best for distributed systems, sequential-friendly)
-- PostgreSQL 18+ has uuidv7() natively (uuidv4() is now an alias for gen_random_uuid());
-- on PG14-17, use the pg_uuidv7 extension instead
id UUID NOT NULL DEFAULT uuidv7() PRIMARY KEY

-- ❌ Wrong: UUID v4 as PK in high-insert tables — causes index bloat and page splits
id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY

-- ❌ Wrong: SERIAL is legacy, prefer GENERATED ALWAYS AS IDENTITY
id SERIAL PRIMARY KEY
```

**Rule:** Use `BIGINT GENERATED ALWAYS AS IDENTITY` for most OLTP tables. Use time-ordered UUIDs (v7) when global uniqueness across services is required. **Never** use random UUIDv4 as a high-volume table's primary key — it degrades B-tree index performance due to random insertion order.

### Timestamps

```sql
-- ✅ Always use TIMESTAMPTZ — stores UTC internally, converts on read
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
deleted_at  TIMESTAMPTZ               -- NULL means not deleted (soft delete)

-- ❌ Wrong: TIMESTAMP without timezone causes ambiguity across timezone changes
created_at  TIMESTAMP NOT NULL DEFAULT NOW()
```

**Rule:** **Always** use `TIMESTAMPTZ`. Both `TIMESTAMP` and `TIMESTAMPTZ` occupy 8 bytes — there is zero storage benefit to dropping timezone awareness.

### Text & Characters

```sql
-- ✅ Use TEXT for variable-length strings; enforce length via CHECK if needed
email       TEXT NOT NULL CHECK (char_length(email) <= 254),
name        TEXT NOT NULL CHECK (char_length(name) BETWEEN 1 AND 255)

-- ❌ Wrong: VARCHAR(n) offers no storage benefit over TEXT and causes implicit casts
email       VARCHAR(254) NOT NULL
```

**Rule:** Prefer `TEXT` over `VARCHAR(n)`. Use `CHECK` constraints for length limits. `CHAR(n)` is almost never appropriate — it pads with spaces and wastes storage.

### Numbers

```sql
-- ✅ Money / financial amounts: NUMERIC for exact decimal arithmetic
price       NUMERIC(12, 2) NOT NULL   -- up to 9,999,999,999.99

-- ✅ Counters, IDs: BIGINT (INTEGER if values are guaranteed < 2.1B)
view_count  BIGINT NOT NULL DEFAULT 0

-- ✅ Scientific / approximate: DOUBLE PRECISION (FLOAT8) or REAL (FLOAT4)
latitude    DOUBLE PRECISION NOT NULL

-- ❌ Wrong: FLOAT for money — floating point arithmetic is imprecise
price       FLOAT NOT NULL
```

### JSONB

```sql
-- ✅ Use JSONB for semi-structured or dynamic fields
metadata    JSONB,
settings    JSONB NOT NULL DEFAULT '{}'

-- ❌ Wrong: JSON is stored as text and must be reparsed on every access
metadata    JSON

-- ✅ Index frequently queried JSONB keys with GIN
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);

-- ✅ Or use a functional B-tree index for a specific key
CREATE INDEX idx_products_sku ON products ((metadata->>'sku'));
```

**Rules:**

- Always use `JSONB` over `JSON`.
- Do **not** use `JSONB` for columns with a fixed, known structure — use proper relational columns instead.
- Index `JSONB` with `GIN` for containment queries (`@>`, `?`).
- Use expression indexes (`(metadata->>'key')`) for equality queries on specific keys.

### Enumerations

```sql
-- ✅ Use native ENUM for stable, small, rarely-changing sets
CREATE TYPE user_role AS ENUM ('admin', 'editor', 'viewer');

-- ✅ For evolving enumerations, a lookup table is more flexible
CREATE TABLE statuses (
    code        TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE
);
```

**Rule:** Use PostgreSQL native `ENUM` for simple, stable states. Use a lookup/reference table when the list grows frequently, needs ordering, needs extra attributes, or is managed by users.

### Generated Columns

```sql
-- ✅ STORED: computed on write, indexable, costs write time + storage
ALTER TABLE products ADD COLUMN search_text tsvector
    GENERATED ALWAYS AS (to_tsvector('english', name || ' ' || description)) STORED;

-- ✅ VIRTUAL (PostgreSQL 18+, and the default tier when unspecified): computed on read,
-- no storage, no write cost — but CANNOT be indexed
ALTER TABLE orders ADD COLUMN total_with_tax numeric
    GENERATED ALWAYS AS (subtotal * 1.0825) VIRTUAL;
```

**Rule:** Use `VIRTUAL` for cheap expressions on columns that are read far more often than
written, or where you don't need to index the result — it costs nothing to store and never
triggers a table rewrite when added. Use `STORED` when the expression is expensive relative to
read frequency, or when the result must be indexed (a `VIRTUAL` column cannot be). On
PostgreSQL 18+, `VIRTUAL` is the default tier if you omit `STORED`/`VIRTUAL` — be explicit
rather than relying on the default, since a reader on an older version will otherwise
misread the intent. Generated columns cannot reference other generated columns or call
non-immutable/user-defined functions; `STORED` generated columns can be logically replicated
as of PostgreSQL 18.

---

## 4. Schema Design & Data Modeling

### Normalization

- Aim for **Third Normal Form (3NF)** by default.
- Denormalize **only** when proven by `EXPLAIN ANALYZE` that a JOIN is a bottleneck.
- Document all intentional denormalization with a comment explaining the trade-off.

```sql
-- ✅ Correct: normalized, referenced via FK
CREATE TABLE addresses (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    street     TEXT NOT NULL,
    city       TEXT NOT NULL,
    country    TEXT NOT NULL
);

-- ❌ Wrong: denormalized city/country embedded in users — no referential integrity
ALTER TABLE users ADD COLUMN city TEXT, ADD COLUMN country TEXT;
```

### Constraints — Enforce Integrity at the Database Level

```sql
CREATE TABLE products (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku          TEXT NOT NULL,
    name         TEXT NOT NULL CHECK (char_length(name) > 0),
    price        NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    stock        INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category_id  BIGINT NOT NULL REFERENCES categories(id),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (sku)
);
```

**Rules:**

- Use `NOT NULL` on every column that must always have a value.
- Declare `CHECK` constraints inline for simple rules; use table-level constraints for multi-column rules.
- Always define `ON DELETE` behavior explicitly on foreign keys: `CASCADE`, `SET NULL`, `RESTRICT`.
- Never rely solely on application-layer validation for integrity — the database is the last line of defence.

### Soft Deletes

```sql
-- ✅ Use a nullable deleted_at column
deleted_at TIMESTAMPTZ DEFAULT NULL

-- Query only active rows via a partial index
CREATE INDEX idx_users_active ON users (id) WHERE deleted_at IS NULL;
```

### Audit Columns

Every entity table should include standard audit columns:

```sql
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
created_by  BIGINT REFERENCES users(id),
updated_by  BIGINT REFERENCES users(id)
```

Automate `updated_at` maintenance with a trigger:

```sql
CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
```

### Multi-Tenancy with Schemas

```sql
-- ✅ Schema-per-tenant for strong isolation
CREATE SCHEMA tenant_acme;
CREATE TABLE tenant_acme.orders ( ... );

-- ✅ Or RLS-based tenancy for shared table (see Security section)
```

---

## 5. Indexing Strategy

**Index-type selection** (B-tree vs GIN vs GiST vs BRIN, and when each wins) is owned by
`zeno-stack/zeno-postgres-patterns` — consult its quick-reference table there. This section owns
the *schema-design-time* indexing rules:

### Rules

```sql
-- ✅ Index foreign keys (PostgreSQL does NOT auto-index FKs)
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_order_items_product_id ON order_items (product_id);

-- ✅ Composite index — column order matters; most selective / most filtered first
CREATE INDEX idx_orders_user_status ON orders (user_id, status);

-- ✅ Partial index — reduces index size, speeds up common filtered queries
CREATE INDEX idx_users_unverified ON users (created_at)
    WHERE email_verified_at IS NULL;

-- ✅ Covering index — allows index-only scan (avoids heap access)
CREATE INDEX idx_orders_user_created ON orders (user_id)
    INCLUDE (total_amount, status, created_at);

-- ✅ Expression index — for case-insensitive lookups
CREATE INDEX idx_users_email_lower ON users (LOWER(email));

-- ✅ Full-text search
CREATE INDEX idx_articles_fts ON articles USING GIN (to_tsvector('english', title || ' ' || body));

-- ❌ Wrong: indexing a low-cardinality column alone is wasteful
CREATE INDEX idx_users_is_active ON users (is_active);

-- ❌ Wrong: over-indexing — every extra index slows down writes
```

**Core Rules:**

- **Always index foreign key columns** — PostgreSQL does not do this automatically.
- Use `CREATE INDEX CONCURRENTLY` in production to avoid locking tables.
- Monitor unused indexes with `pg_stat_user_indexes` and drop those where `idx_scan = 0`.
- Run `ANALYZE <table>` after bulk data loads to refresh planner statistics.
- Column order in composite indexes follows: most-filtered first → most-selective → included in `ORDER BY`.

---

## 6. Query & SQL Standards

### General Rules

```sql
-- ✅ Always use parameterized queries (never concatenate user input)
SELECT id, email FROM users WHERE id = $1;  -- application passes $1

-- ✅ Specify exact columns — never SELECT *
SELECT u.id, u.email, u.created_at
FROM users u
WHERE u.is_active = TRUE AND u.deleted_at IS NULL;

-- ❌ Wrong: SELECT * fetches unneeded data and prevents index-only scans
SELECT * FROM users;
```

### Pagination

```sql
-- ✅ Keyset (cursor-based) pagination — O(1), performant at any offset
SELECT id, name, created_at
FROM products
WHERE created_at < $1   -- last seen created_at from previous page
  AND id < $2            -- tiebreaker
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- ❌ Wrong: OFFSET-based pagination degrades as offset grows (O(n) scan)
SELECT id, name FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 10000;
```

### Upserts

```sql
-- ✅ Use INSERT ON CONFLICT for atomic upserts
INSERT INTO user_settings (user_id, key, value)
VALUES ($1, $2, $3)
ON CONFLICT (user_id, key)
DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
```

### Transactions & Locking

```sql
-- ✅ Always use explicit transactions for multi-statement operations
BEGIN;
UPDATE accounts SET balance = balance - $1 WHERE id = $2;
UPDATE accounts SET balance = balance + $1 WHERE id = $3;
COMMIT;

-- ✅ Use advisory locks for distributed coordination
SELECT pg_advisory_xact_lock(hashtext('import_job_' || $1::text));

-- ✅ Prefer SELECT FOR UPDATE SKIP LOCKED for queue-like processing
SELECT id, payload FROM jobs
WHERE status = 'pending'
ORDER BY created_at
LIMIT 10
FOR UPDATE SKIP LOCKED;
```

### Common Table Expressions (CTEs)

```sql
-- ✅ Use CTEs for readability on complex queries (PostgreSQL 12+ materializes only when beneficial)
WITH active_users AS (
    SELECT id, email FROM users WHERE is_active = TRUE AND deleted_at IS NULL
),
recent_orders AS (
    SELECT user_id, COUNT(*) AS order_count
    FROM orders
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT au.email, ro.order_count
FROM active_users au
JOIN recent_orders ro ON ro.user_id = au.id
ORDER BY ro.order_count DESC;
```

### Avoid N+1 Queries

```sql
-- ✅ Use JOINs or IN() to batch fetch related data
SELECT o.id, o.total_amount, u.email
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.status = 'pending';

-- ❌ Wrong: fetching user for each order in application code (N+1)
```

---

## 7. Migrations

### Migration Rules

- **One change per migration file** — atomic, focused, reversible where possible.
- **Never edit an applied migration** — create a new migration to fix it.
- **Store migrations in version control** alongside application code.
- **Test every migration in a staging environment** before production.
- **Design for backward compatibility** — use a phased approach for breaking schema changes (add → deploy → remove):

```text
Phase 1: Add new column (nullable or with default)
Phase 2: Migrate data; update application to write to both
Phase 3: Remove old column in a later migration
```

### Naming Convention

```text
V{version}__{description}.sql
V1__create_users_table.sql
V2__add_email_index_to_users.sql
V3__add_tenant_id_to_orders.sql
```

### Migration Template

```sql
-- Migration: V5__add_phone_to_users.sql
-- Description: Adds optional phone number column to users table
-- Author: dev@example.com
-- Date: 2024-03-01

BEGIN;

SET lock_timeout = '2s';  -- fail fast instead of queuing behind (and ahead of) other traffic

ALTER TABLE users ADD COLUMN phone TEXT;

-- ❌ Do not add a validated CHECK directly on a large/hot table — this takes
-- ACCESS EXCLUSIVE and does a full-table scan before the transaction can commit:
--   ALTER TABLE users ADD CONSTRAINT chk_users_phone
--       CHECK (phone IS NULL OR char_length(phone) BETWEEN 7 AND 20);

-- ✅ NOT VALID → VALIDATE instead (see below)
ALTER TABLE users ADD CONSTRAINT chk_users_phone
    CHECK (phone IS NULL OR char_length(phone) BETWEEN 7 AND 20) NOT VALID;

COMMIT;

-- Separate transaction/statement — VALIDATE takes a much weaker lock:
ALTER TABLE users VALIDATE CONSTRAINT chk_users_phone;

-- Rollback:
-- ALTER TABLE users DROP COLUMN phone;
```

### The `NOT VALID` → `VALIDATE` pattern — the single highest-leverage migration technique

This is the most-violated practice in real migration scripts, and the lock-level difference is
large enough to matter on any table with live traffic:

| Statement | Lock taken | Table scan? |
|---|---|---|
| `ADD CONSTRAINT ... CHECK (...)` (no `NOT VALID`) | `ACCESS EXCLUSIVE` — blocks all reads and writes | Yes, before commit |
| `ADD CONSTRAINT ... CHECK (...) NOT VALID` | `ACCESS EXCLUSIVE`, but instant — the lock level is the same, `NOT VALID`'s benefit is skipping the scan, not lowering the lock | No |
| `VALIDATE CONSTRAINT ...` (run after, as its own statement) | `SHARE UPDATE EXCLUSIVE` — does **not** conflict with normal reads/writes | Yes, but concurrently with live traffic |
| `ADD FOREIGN KEY ... NOT VALID` | `SHARE ROW EXCLUSIVE` on both child and parent | No |

Always split a constraint addition into two steps on any table that takes live traffic: add
`NOT VALID` inside your normal migration transaction (instant), then run `VALIDATE CONSTRAINT`
as a separate statement outside that transaction (scans the table, but only takes the weak
`SHARE UPDATE EXCLUSIVE` lock, so reads and writes continue throughout).

**The same trick applies to `NOT NULL`, and it's easy to miss:** a plain
`ALTER COLUMN ... SET NOT NULL` scans the whole table under `ACCESS EXCLUSIVE` — *unless* the
planner can prove the column is already non-null from an existing validated `CHECK`, in which
case it skips the scan entirely (this optimization has shipped since PostgreSQL 12). The
pre-18 pattern:

```sql
ALTER TABLE orders ADD CONSTRAINT orders_discount_code_not_null
    CHECK (discount_code IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT orders_discount_code_not_null;
ALTER TABLE orders ALTER COLUMN discount_code SET NOT NULL;  -- instant: reuses the validated CHECK
ALTER TABLE orders DROP CONSTRAINT orders_discount_code_not_null;  -- optional cleanup
```

**PostgreSQL 18 adds native `NOT NULL ... NOT VALID`**, making the CHECK workaround above
unnecessary going forward — verify the exact grammar against the `ALTER TABLE` reference for
your installed minor version before relying on it, since this is a newly-introduced surface.

### Zero-Downtime Schema Changes

```sql
-- ✅ Instead of locking the table on new NOT NULL column:
-- Step 1: Add nullable column
ALTER TABLE orders ADD COLUMN discount_code TEXT;

-- Step 2: Backfill in batches to avoid locking
UPDATE orders SET discount_code = '' WHERE discount_code IS NULL AND id BETWEEN 1 AND 100000;
-- (repeat in batches with LIMIT)

-- Step 3: Add NOT NULL via the NOT VALID → VALIDATE pattern above, then a default
ALTER TABLE orders ALTER COLUMN discount_code SET DEFAULT '';

-- ✅ Add index without locking
CREATE INDEX CONCURRENTLY idx_orders_discount_code ON orders (discount_code);
```

**A column default is not always metadata-only.** `ADD COLUMN ... DEFAULT` with a
**non-volatile** default (a literal, or `''` as above) is metadata-only since PostgreSQL 11 —
the default is stored in the catalog and materialized lazily, no rewrite. A **volatile**
default (`now()`, `gen_random_uuid()`, `random()`), a `STORED` generated column, or an identity
column forces a full table rewrite under `ACCESS EXCLUSIVE`. Never add a volatile-default
column to a large, live table in one step — add it nullable, backfill in batches, then set the
default. A `VIRTUAL` generated column (see Generated Columns below) never rewrites, by
construction.

For the full `ALTER TABLE` lock-level cheat sheet (which operations are metadata-only vs. force
a rewrite, and which lock level each takes), see
`frameworks/plpgsql.md`.

---

## 8. Security

### Role-Based Access Control (RBAC)

```sql
-- ✅ Principle of Least Privilege: dedicated roles per service
CREATE ROLE app_api LOGIN PASSWORD '...';  -- store password in secrets manager
GRANT CONNECT ON DATABASE mydb TO app_api;
GRANT USAGE ON SCHEMA public TO app_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_api;

-- Read-only role for reporting
CREATE ROLE app_reporting LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE mydb TO app_reporting;
GRANT USAGE ON SCHEMA public TO app_reporting;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reporting;

-- ❌ Wrong: application connecting as superuser or owner
```

### Row-Level Security (RLS)

**RLS recipes (policy patterns, `auth.uid()` wrapping, per-role policies, performance traps) are
owned by `zeno-stack/zeno-postgres-patterns`** — consult it when writing policies. The
schema-design-time rules that belong here: enable **and `FORCE`** RLS on multi-tenant tables
(`FORCE` stops the table owner bypassing policies), always index RLS-predicate columns, keep
policies simple, and test isolation rigorously (Role A must not see Role B's rows).

### Authentication

```sql
-- ✅ pg_hba.conf: require scram-sha-256 for all remote connections
# host  all  all  0.0.0.0/0  scram-sha-256

-- ❌ Wrong: trust authentication for non-localhost connections
# host  all  all  0.0.0.0/0  trust

-- ❌ Wrong: md5 is deprecated and cryptographically weak
# host  all  all  0.0.0.0/0  md5
```

**Authentication Rules:**

- Use `SCRAM-SHA-256` for all remote connections (set `password_encryption = scram-sha-256` in `postgresql.conf`).
- Require SSL/TLS (`ssl = on`, `ssl_cert_file`, `ssl_key_file`) for all non-localhost connections.
- Never expose the PostgreSQL port to the public internet without a firewall or VPN.
- Audit `pg_hba.conf` on every deployment.
- Rotate credentials via a secrets manager (Vault, AWS Secrets Manager). Never hardcode passwords.

### Data Encryption

```sql
-- ✅ Encrypt sensitive column data at rest using pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Store encrypted PII
INSERT INTO users (ssn_encrypted)
VALUES (pgp_sym_encrypt('123-45-6789', current_setting('app.encryption_key')));

-- Retrieve and decrypt
SELECT pgp_sym_decrypt(ssn_encrypted::bytea, current_setting('app.encryption_key'))
FROM users WHERE id = $1;
```

---

## 9. Performance & Query Analysis

### EXPLAIN ANALYZE

```sql
-- ✅ Always analyze slow queries before adding indexes or rewriting
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.email, COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.is_active = TRUE
GROUP BY u.email;

-- ✅ Wrap DML with EXPLAIN ANALYZE in a transaction to avoid side effects
BEGIN;
EXPLAIN ANALYZE UPDATE orders SET status = 'archived' WHERE created_at < NOW() - INTERVAL '1 year';
ROLLBACK;
```

**Slow-query diagnosis (reading plans, the signal→problem→solution table) and
`postgresql.conf`/connection/timeout tuning are owned by `zeno-stack/zeno-postgres-patterns`** —
take EXPLAIN output there. This section keeps only the code-standard: always `EXPLAIN (ANALYZE,
BUFFERS)` before adding an index or rewriting a query, and wrap DML analysis in a rolled-back
transaction as above.

### Maintenance

```sql
-- ✅ Run VACUUM ANALYZE after bulk imports
VACUUM ANALYZE orders;

-- ✅ Rebuild bloated indexes without locking
REINDEX INDEX CONCURRENTLY idx_orders_user_id;

-- ✅ Check table bloat
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ✅ Check unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
```

---

## 10. Connection Pooling with PgBouncer

Full detail (PgBouncer configuration, pooling-mode decision table, monitoring, and
`postgresql.conf` logging) is owned by `zeno-stack/zeno-postgres-patterns` — see its
"Connection pooling and logging" section. That is the same cession this skill's own boundary
statement makes for connection/timeout configuration; `references/operations.md` keeps only the
schema-design-relevant note.
Orientation: always put a pooler between the application and PostgreSQL (one backend
process per connection does not scale); `pool_mode = transaction` fits most web apps but
disallows session-level features; alert when `SHOW POOLS` reports waiting clients.

---

## 11. Observability & Monitoring

Full detail (key system views, monitoring metric thresholds, logging configuration) lives
in `references/operations.md` — load it before setting up monitoring or diagnosing a live
instance. Orientation: watch `pg_stat_activity` for long-running queries,
`pg_stat_statements` for the slowest ones, and dead-tuple ratios for autovacuum lag; log
statements over 1s, lock waits, and temp-file spills.

---

## 12. Stored Procedures & Functions

Full detail (a hardened `SECURITY DEFINER` transfer-funds example plus the function-writing
rules) lives in `references/operations.md` — load it before writing any function or
procedure. Deeper internals (volatility, plan caching, dynamic SQL safety, triggers, the
full `SECURITY DEFINER` hardening checklist, the `ALTER TABLE` lock-level cheat sheet)
stay in `frameworks/plpgsql.md`. Orientation: prefer `SECURITY INVOKER`; with
`SECURITY DEFINER` set `search_path = ''` and schema-qualify everything; keep functions
small — orchestration belongs in the application layer.

---

## 13. Tooling & CI Checklist

| Category | Recommended Tool | Purpose |
|---|---|---|
| Migrations | **Flyway** or **Liquibase** | Schema versioning, CI/CD integration |
| ORM (optional) | **SQLAlchemy**, **Diesel**, **Prisma** | Typed query building |
| Query analysis | **pgBadger**, **pg_stat_statements** | Slow query identification |
| Backup | **pg_dump**, **pgBackRest**, **Barman** | Full + incremental backups |
| Connection pooling | **PgBouncer** | Connection management |
| Schema linting | **squawk**, **pganalyze** | Automated migration review |
| Monitoring | **pg_prometheus**, **DataDog**, **Grafana** | Metrics & alerting |
| Replication | **Streaming replication + Patroni** | HA + failover |

### CI Gate Requirements

Every PR/deployment touching the database **must** pass:

- [ ] Migration script follows naming convention and has a rollback comment.
- [ ] `EXPLAIN ANALYZE` output reviewed for new queries touching tables > 10k rows.
- [ ] New indexes created with `CONCURRENTLY` flag.
- [ ] No `SELECT *` in production queries.
- [ ] No `trust` authentication in `pg_hba.conf`.
- [ ] All timestamps use `TIMESTAMPTZ`.
- [ ] All FK columns have a corresponding index.
- [ ] `squawk` or equivalent linter passed with no dangerous-migration warnings.
- [ ] Database created with `UTF-8` encoding, not `SQL_ASCII`.
- [ ] Transactions short-lived; `idle_in_transaction_session_timeout` configured.

---

## 14. SQL Style

Consistent SQL formatting improves readability and code review quality.

### Keyword Casing & Formatting

- Use **UPPERCASE** for all SQL keywords (`SELECT`, `FROM`, `WHERE`, `JOIN`, `CREATE TABLE`), and **lowercase `snake_case`** for identifiers (tables, columns, aliases). This keyword/identifier split is used consistently throughout every example in this skill.
- Indent with **4 spaces** (never tabs); keep lines to a maximum of **80 characters**.
- Place each major clause (`SELECT`, `FROM`, `WHERE`, `JOIN`, `GROUP BY`, `ORDER BY`) on its own line.

```sql
-- ✅ Correct — clean, readable formatting
SELECT
    u.id,
    u.first_name,
    COUNT(o.id) AS order_count
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
WHERE u.is_active = true
    AND u.created_at >= '2024-01-01'
GROUP BY u.id, u.first_name
ORDER BY order_count DESC
LIMIT 20;
```

### Alias Rules

- **Always** use the `AS` keyword for aliases — never implicit aliases.
- Use short but meaningful table aliases (`u` for `users`, `oi` for `order_items`).

```sql
-- ✅ Correct
SELECT p.name AS product_name FROM products AS p;

-- ❌ Wrong — implicit alias, no AS keyword
SELECT p.name product_name FROM products p;
```

### Join Style

- **Always** specify the join type explicitly (`inner join`, `left join`).
- **Never** use implicit joins (comma-separated tables in `FROM`).
- Place `ON` conditions on the next line, indented.

### Comments & Schema Qualification

- Use `--` for single-line comments; `/* ... */` for block comments.
- **Always** document tables and columns with `COMMENT ON`:

```sql
comment on table orders is 'Customer purchase orders.';
comment on column orders.total_amount is 'Total order amount in USD, excluding tax.';
```

- **Always** schema-qualify identifiers in shared codebases to avoid `search_path` ambiguity:

```sql
-- ✅ Correct
SELECT * FROM public.users;

-- ❌ Ambiguous (relies on search_path)
SELECT * FROM users;
```

---

## 15. Advanced: Partitioning & Isolation

Full detail (declarative range-partitioning DDL, the isolation-level table and rules)
lives in `references/operations.md` — load it when a table nears ~100 GB / time-series
scale or when choosing an isolation level. Orientation: partition tables over ~100 GB or
time-series data with declarative `RANGE` partitioning; default to `READ COMMITTED`,
escalate to `SERIALIZABLE` only for ledger-grade correctness; keep transactions short and
set `idle_in_transaction_session_timeout`.

---

## Anti-pattern quick reference

### Schema Anti-Patterns

| Anti-Pattern | Problem | Solution |
| --- | --- | --- |
| **God Table** — 50+ columns | Slow writes, sparse nulls, cache waste | Normalize into related tables |
| **EAV** — generic key-value | No type safety, complex queries, no FK integrity | Use relational columns or `jsonb` |
| **Storing everything as `text`** | No type validation, poor performance | Use specific types (`integer`, `boolean`, `timestamptz`) |
| **Uppercase identifiers** | Requires quoting everywhere | Always use lowercase `snake_case` |
| **Missing primary keys** | No row identity, replication breaks | Every table gets a PK |
| **`SQL_ASCII` encoding** | Silent data corruption, broken sorting | Always use `UTF-8` |

### Query Anti-Patterns

| Anti-Pattern | Problem | Solution |
| --- | --- | --- |
| **`SELECT *`** | Unnecessary I/O, breaks with schema changes | List columns explicitly |
| **`NOT IN` with nullable columns** | Returns unexpected empty results | Use `NOT EXISTS` |
| **`BETWEEN` for timestamps** | Includes both boundaries, off-by-one risk | Use `>=` and `<` |
| **Implicit joins** | Hard to read, easy to miss conditions | Use explicit `JOIN ... ON` |
| **`OFFSET` for deep pagination** | O(n) scan, degrades at scale | Use keyset pagination |
| **String concatenation in SQL** | SQL injection vulnerability | Use parameterized queries |

### Design Anti-Patterns

| Anti-Pattern | Problem | Solution |
| --- | --- | --- |
| **Soft deletes everywhere** | Every query needs `WHERE deleted_at IS NULL` | Use only when audit trail is legally required |
| **JSONB for structured data** | No FK integrity, no type checks | Model as proper relational tables |
| **No foreign keys** ("for performance") | Orphaned data, silent integrity loss | FKs are cheap — add them |

---

## Pre-flight checklist — run before delivering any PostgreSQL schema or query

1. Every item in the CI Gate Requirements list (§13) passes — naming/rollback comment on
   migrations, `EXPLAIN ANALYZE` reviewed, `CONCURRENTLY` indexes, no `SELECT *`,
   `TIMESTAMPTZ` everywhere, FK columns indexed, linter clean, UTF-8, short transactions.
2. No entry from the Anti-pattern quick reference tables appears in the delivered schema or query.
3. Naming follows §2's conventions; SQL formatted per §14's style rules.
4. Security posture checked: no `trust` auth, RLS/RBAC applied where the design calls
   for it.
5. Tables expected to exceed ~100 GB or hold time-series data have a partitioning plan
   (§15, detail in `references/operations.md`); isolation level chosen deliberately, not defaulted blindly.
