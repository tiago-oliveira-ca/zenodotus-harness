---
name: zeno-database-migrations
description: >
  Database migration safety across PostgreSQL, MySQL, and common ORMs (Prisma, Drizzle,
  Kysely, Django, golang-migrate) — schema changes, backfills, rollbacks, and
  zero-downtime expand-contract deployments. Use when creating or altering a table,
  adding an index or column on a live table, planning a data backfill, or wiring up
  migration tooling for a new project. For the underlying SQL/index/schema patterns
  themselves see zeno-postgres-patterns; this skill covers how to roll a change out
  safely, not what the schema should look like. Trigger on: "write a migration", "add a
  column to this table", "zero-downtime schema change", "backfill this data",
  "rollback a migration", "expand-contract", "rename a column safely", "migration
  tooling".
---

# Database Migrations

Safe, reversible schema and data changes for production systems — across raw SQL and
the common ORM migration tools.

## When to reach for this skill

- Creating or altering a table
- Adding or removing a column or index on a table that already has production data
- Running a data migration (backfill, transform)
- Planning a zero-downtime schema change
- Setting up migration tooling for a new project

## Core principles

1. **Every change is a migration file** — never alter a production database by hand.
2. **Migrations are forward-only in production** — a rollback is a new forward
   migration that undoes the previous one, not an edit to history.
3. **Schema and data migrations are separate** — never mix DDL and DML in one file; a
   long-running data transform inside a schema-change transaction turns a fast DDL
   change into a multi-minute lock.
4. **Test against production-sized data** — a migration that's instant on 100 rows can
   lock a table for minutes on 10M.
5. **Migrations are immutable once deployed** — never edit a migration that has already
   run in production; environments drift the moment you do.

## Migration safety checklist

Before applying any migration:

- [ ] Has both an UP and a DOWN, or is explicitly marked irreversible
- [ ] No full-table lock on a large table (use concurrent operations)
- [ ] New columns are nullable or have a default (never add `NOT NULL` bare)
- [ ] Indexes on existing tables are created concurrently, not inline
- [ ] Data backfill is its own migration, separate from the schema change
- [ ] Tested against a copy of production-scale data
- [ ] Rollback plan is documented

## PostgreSQL patterns

```sql
-- GOOD: nullable column, no lock
ALTER TABLE users ADD COLUMN avatar_url TEXT;

-- GOOD: column with a default (Postgres 11+ does this instantly, no table rewrite)
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- BAD: NOT NULL with no default on an existing table — forces a full rewrite and locks
ALTER TABLE users ADD COLUMN role TEXT NOT NULL;
```

```sql
-- BAD: blocks writes on large tables
CREATE INDEX idx_users_email ON users (email);

-- GOOD: non-blocking, allows concurrent writes
-- Note: CONCURRENTLY cannot run inside a transaction block — most migration
-- tools need special handling to skip wrapping it in one
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);
```

**Renaming a column** — never rename directly in production; use expand-contract:

```sql
-- 1. Add the new column
ALTER TABLE users ADD COLUMN display_name TEXT;
-- 2. Backfill (separate migration)
UPDATE users SET display_name = username WHERE display_name IS NULL;
-- 3. Deploy application code that reads/writes both columns, then only the new one
-- 4. Once nothing reads the old column, drop it (separate migration)
ALTER TABLE users DROP COLUMN username;
```

**Large data migrations** — batch instead of updating every row in one transaction:

```sql
DO $$
DECLARE
  batch_size INT := 10000;
  rows_updated INT;
BEGIN
  LOOP
    UPDATE users
    SET normalized_email = LOWER(email)
    WHERE id IN (
      SELECT id FROM users
      WHERE normalized_email IS NULL
      LIMIT batch_size
      FOR UPDATE SKIP LOCKED
    );
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    EXIT WHEN rows_updated = 0;
    COMMIT;
  END LOOP;
END $$;
```

## ORM tooling reference

**Prisma:**
```bash
npx prisma migrate dev --name add_user_avatar   # create + apply in dev
npx prisma migrate deploy                        # apply pending in production
npx prisma migrate dev --create-only --name x     # empty migration for hand-written SQL
```
Prisma can't express `CREATE INDEX CONCURRENTLY` — write that SQL by hand inside a
`--create-only` migration.

**Drizzle:**
```bash
npx drizzle-kit generate   # generate migration from schema changes
npx drizzle-kit migrate    # apply migrations
npx drizzle-kit push       # push schema directly, dev only — no migration file
```

**Kysely (kysely-ctl):**
```bash
kysely migrate make add_user_avatar
kysely migrate latest
kysely migrate down
```
Migration files always type the database as `Kysely<any>`, never the app's typed DB
interface — a migration is frozen in time and must not depend on today's schema types.

**Django:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations --empty app_name -n description   # custom SQL/data
```
`SeparateDatabaseAndState` removes a field from the Django model without dropping the
database column in the same migration — useful for the "stop referencing, then drop"
sequence:
```python
migrations.SeparateDatabaseAndState(
    state_operations=[migrations.RemoveField(model_name="user", name="legacy_field")],
    database_operations=[],  # DB column stays until a later migration drops it
)
```

**golang-migrate:**
```bash
migrate create -ext sql -dir migrations -seq add_user_avatar
migrate -path migrations -database "$DATABASE_URL" up
migrate -path migrations -database "$DATABASE_URL" down 1
migrate -path migrations -database "$DATABASE_URL" force VERSION   # fix a dirty state
```

## Zero-downtime strategy: expand-contract

```
Phase 1: EXPAND
  - Add new column/table (nullable or with a default)
  - Deploy app that writes to BOTH old and new
  - Backfill existing rows

Phase 2: MIGRATE
  - Deploy app that reads from NEW, still writes to BOTH
  - Verify data consistency between old and new

Phase 3: CONTRACT
  - Deploy app that only uses NEW
  - Drop the old column/table in a separate, later migration
```

Example timeline for a status-field rename:

```
Day 1: Migration adds new_status column (nullable); deploy app v2 writes both columns
Day 2: Backfill migration runs for existing rows
Day 3: Deploy app v3 — reads from new_status only
Day 7: Migration drops the old status column
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Manual SQL run directly against production | Always go through a migration file — no audit trail otherwise |
| Editing a migration that already ran in production | Write a new migration; edited history causes environment drift |
| `NOT NULL` column added with no default | Add nullable, backfill, then add the constraint in a later migration |
| Inline `CREATE INDEX` on a large existing table | `CREATE INDEX CONCURRENTLY` |
| Schema change and data backfill in one migration | Split into separate migrations — different lock profiles, different rollback needs |
| Dropping a column before removing app code that reads it | Ship the code change first; drop the column in the following deploy |
| Renaming a column directly | Expand-contract: add new, backfill, cut over, drop old |

## Pre-flight checklist — run before delivering any database migration

- [ ] Migration file has both UP and DOWN, or is explicitly marked irreversible
- [ ] No full-table lock introduced on a table with production data
- [ ] New columns are nullable or carry a default — no bare `NOT NULL` add
- [ ] Indexes on existing tables are created concurrently
- [ ] Schema change and data backfill are separate migrations
- [ ] Tested against production-scale data, not a handful of rows
- [ ] Rollback plan is written down before this ships
- [ ] Column/table removal follows expand-contract, not a direct drop
