# PL/pgSQL Internals & Locking — Functions, Procedures, Triggers, and ALTER TABLE Lock Levels

Read this file before writing or reviewing a PL/pgSQL function/procedure/trigger, before
choosing `SECURITY DEFINER`, or before running a migration on a table with live traffic. Facts
below are version-gated where PostgreSQL behavior changed; verify against the docs for your
exact minor release when a claim is flagged as version-sensitive — this corner of PostgreSQL
moved meaningfully in PG12–PG18.

## Functions vs. procedures — transaction control

Functions run inside the calling statement's transaction and **cannot** issue `COMMIT`/
`ROLLBACK`. Procedures (`CREATE PROCEDURE`, invoked with `CALL`) can — but only under specific
conditions:

- Transaction control works only when the procedure is called from the top level via `CALL`/
  `DO`, or through a nested chain of `CALL`/`DO` with **no intervening non-`CALL` command**.
  `CALL proc1() → CALL proc2()` allows control in `proc2`; `CALL proc1() → SELECT func2() →
  CALL proc3()` does **not**, because the `SELECT` establishes an atomic context.
- If `CALL` runs inside an explicit transaction block (`BEGIN; CALL ...;`), the procedure
  **cannot** commit/rollback — you get `invalid transaction termination`. Autocommit-off
  clients (which wrap everything in an implicit `BEGIN`) silently disable in-procedure
  transaction control — a common source of "why doesn't my procedure commit" bugs.
- **A transaction cannot be ended inside a block that has an `EXCEPTION` handler**
  (`cannot commit while a subtransaction is active`) — the exception handler *is* a
  subtransaction. You cannot both catch errors and commit in the same block.
- PL/pgSQL does not support `SAVEPOINT` directly; use exception-handler blocks instead.
  `COMMIT AND CHAIN` / `ROLLBACK AND CHAIN` preserve transaction characteristics across the
  implicit new transaction.
- **Cursor-loop gotcha:** `FOR r IN SELECT ... LOOP ... COMMIT; END LOOP` converts the cursor to
  a **holdable** cursor on the first `COMMIT` — it becomes fully materialized at that point, and
  any row/table locks held by the cursor query are released. Don't assume a loop like this
  holds a consistent lock across iterations once a `COMMIT` appears inside it.

## Volatility markers — promises the planner trusts without checking

`VOLATILE` (default) / `STABLE` / `IMMUTABLE` are **promises**, not hints. PostgreSQL does not
verify them and will produce wrong answers if you lie.

| Marker | Meaning | Consequence of mislabeling |
|---|---|---|
| `IMMUTABLE` | Same output forever for the same inputs; can be constant-folded at plan time; **required for expression indexes** | Labeling a function immutable when it isn't can let it be folded to a stale constant during planning — reused across later executions of the same prepared plan. Classic bug: a function whose result depends on a GUC like `TimeZone` marked `IMMUTABLE` instead of `STABLE`. |
| `STABLE` | Constant within one statement; uses the calling query's snapshot | Correct default for lookup functions. Can be used in an index *scan* at runtime, but not to build an index (that needs `IMMUTABLE`). |
| `VOLATILE` | Re-evaluated every row; required for anything with side effects (`nextval`, `random`, `clock_timestamp`) | Mislabeling something volatile as stable/immutable risks stale or wrong results; leaving something stable marked volatile is only a performance cost, not a correctness one — but the cost is real: a documented benchmark found a volatile function on a 1M-row scan ran ~240× slower than the equivalent immutable function, because the immutable version was evaluated once and used to probe an index while the volatile one ran once per row. |

**`PARALLEL {SAFE|RESTRICTED|UNSAFE}`** (default `UNSAFE`): a single `PARALLEL UNSAFE` function
anywhere in a query forces the whole query to a serial plan. Anything that writes DB state,
uses sequences, changes settings, or touches session/cursor state must be `RESTRICTED` or
`UNSAFE`. Mislabeling as `SAFE` when it isn't can produce wrong answers or errors under a
parallel plan, not just a performance issue.

**`LEAKPROOF`** (superuser-only): asserts the function reveals nothing about its arguments
except via its return value, and raises no argument-dependent errors. The planner may push a
leakproof qualifier below a security-barrier view or row-level-security policy; a non-leakproof
function is held back specifically to avoid leaking protected data through error messages or
timing. Marking something leakproof that can actually error on specific argument values is a
real information-disclosure vector, not just a technicality.

## Plan caching: the sixth-execution cliff

For parameterized prepared statements — including the implicit ones PL/pgSQL generates
internally — PostgreSQL runs the **first 5 executions with custom plans** (built and costed
per actual parameter values), then on the **6th execution** builds a generic plan and compares
its estimated cost against the average custom-plan cost. If the generic plan isn't
meaningfully worse, PostgreSQL switches to it **for the rest of the session**.

**The failure mode: skewed data.** A generic plan estimates selectivity as roughly
`1/ndistinct`, ignoring actual value frequency. On a column where one value covers 99.9% of
rows and another covers 0.1%, custom plans correctly choose different strategies per value —
but the generic plan, once adopted, applies one strategy to both, and can be dramatically wrong
for the common value (e.g., doing hundreds of thousands of random index lookups where a
sequential scan was correct). **On partitioned tables the failure looks different:** a generic
plan can't do plan-time partition pruning and may reference every partition, which can exhaust
memory on tables with hundreds of partitions.

**Controls:**
- `plan_cache_mode = auto | force_custom_plan | force_generic_plan` — settable per-session or
  per-function. Force `force_custom_plan` for a function called with wildly skewed parameter
  distributions if you observe the generic-plan regression.
- Diagnose with `EXPLAIN EXECUTE`: a generic plan shows `$1`-style placeholders; a custom plan
  shows substituted literal values.
- Force a replan with `DEALLOCATE` (or a new connection).
- `EXPLAIN (GENERIC_PLAN)` (PG16+) inspects the generic plan without executing anything.

## Exception blocks: subtransactions, WAL cost, and the 64-subxact cliff

Every `BEGIN ... EXCEPTION WHEN ... END` block starts a **subtransaction** (an implicit
savepoint) on entry — whether or not an exception actually fires.

- If the block modifies rows, it **consumes a subtransaction XID** and forces WAL writes for
  the savepoint, even on success. A documented benchmark found wrapping each iteration of a
  loop in an exception block ran 3–5× slower and generated substantially more WAL than the
  equivalent without exception handling, even for entirely successful inserts.
- PostgreSQL caches at most **64 subtransaction XIDs** per session
  (`PGPROC_MAX_CACHED_SUBXIDS`). Beyond that, a session's snapshot is marked "suboverflowed,"
  and every other backend checking visibility against that snapshot must consult the on-disk
  `pg_subtrans` SLRU instead of the in-memory cache — a documented source of
  `SubtransSLRU`/`SubtransControlLock` contention that degrades non-linearly (reports of 50–100×
  slowdowns) and can affect unrelated sessions, not just the one running the loop. The
  characteristic symptom is a workload that's fine at low concurrency and collapses under load.
- **Therefore: never use exception blocks as flow control in a loop.** For "insert or skip
  duplicates," use `INSERT ... ON CONFLICT DO NOTHING`. For "insert or update," use
  `ON CONFLICT ... DO UPDATE` or `MERGE`. Validate data before inserting rather than catching a
  per-row constraint violation.
- A block with an exception handler that never actually modifies a row doesn't consume a
  subtransaction XID — it's XID *consumption*, not merely entering the block, that's expensive.
  But you still pay the block-entry overhead, and the "don't loop with an exception handler"
  rule holds regardless.

## Set-based SQL over row-by-row PL/pgSQL

Prefer one set-based statement over a cursor loop whenever the logic allows it. Native tools:
CTEs (note: since PG12, a CTE is **not** an optimization fence unless written as
`WITH x AS MATERIALIZED (...)`), `INSERT ... ON CONFLICT`, `RETURNING`, and `MERGE` (PG15+).
**PostgreSQL 18 adds `OLD`/`NEW` aliases inside `RETURNING`** for `INSERT`/`UPDATE`/`DELETE`/
`MERGE`, letting a single DML statement return both before- and after-values — eliminating a
common historical reason to reach for a procedure at all. `MERGE` gained `RETURNING` support
with `merge_action()` in PG17, and works against updatable views.

## Dynamic SQL safety

- Pass **data values** as parameters via `EXECUTE ... USING $1, $2`. This avoids the run-time
  cost of converting values to text and back, and is far less prone to SQL injection since
  there's no quoting/escaping involved. Parameters only work for data values in optimizable
  statements (`SELECT`/`INSERT`/`UPDATE`/`DELETE`/`MERGE`) — not for identifiers, and not in
  utility statements.
- Build **identifiers** with `format()`: `%I` quotes an identifier (equivalent to
  `quote_ident`, errors on `NULL`); `%L` quotes a literal (equivalent to `quote_nullable`,
  renders `NULL` as the SQL keyword `NULL`); `%s` inserts raw, unescaped text — **never use `%s`
  for untrusted input.**
- Combine both correctly: `EXECUTE format('UPDATE %I SET %I = $1 WHERE key = $2', tbl, col)
  USING newval, keyval;` — identifiers via `%I`, values via `USING`. This is more efficient
  than converting everything to text and quoting via `%L`, and keeps values in their native
  type.
- `quote_literal` is strict (returns `NULL` on `NULL` input, which silently poisons the whole
  constructed string); use `quote_nullable` when a value may legitimately be `NULL`.

## Error handling

Raise with an explicit `SQLSTATE`: `RAISE EXCEPTION USING ERRCODE = '23505'`, or a custom
5-character SQLSTATE in the user-defined range to avoid colliding with standard error classes.
Retrieve structured context inside a handler with `GET STACKED DIAGNOSTICS v_state =
RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT, v_ctx = PG_EXCEPTION_CONTEXT`. Reserve `RAISE NOTICE`
for debugging — it respects `client_min_messages`, but don't leave chatty notices in hot paths.

## Triggers

- **Row-level** (`FOR EACH ROW`) vs. **statement-level** (`FOR EACH STATEMENT`). For auditing,
  prefer `AFTER ... FOR EACH STATEMENT` with **transition tables**
  (`REFERENCING OLD TABLE AS ... NEW TABLE AS ...`, PG10+) over a row-level trigger — a
  documented benchmark measured roughly 10× faster statement-level auditing versus row-level on
  a 100k-row statement, because the trigger fires once and performs one set-based insert instead
  of once per row (single-benchmark figure; directionally reliable, magnitude workload-dependent).
- **`BEFORE` trigger gotchas:** a `BEFORE ROW` trigger can modify `NEW` and change what actually
  gets written; returning `NULL` silently skips the row entirely; `BEFORE` triggers fire before
  constraints are checked and can observe states that later fail validation.
- **Trigger ordering** for multiple triggers on the same event/timing is alphabetical by trigger
  name — name triggers deliberately if execution order matters.
- **PostgreSQL 18 change:** `AFTER` triggers now execute as the role that was active when the
  trigger event was *queued*, not the role active at commit time — relevant if a transaction
  switches roles mid-flight before committing.

## `SECURITY DEFINER` hardening — the full pattern

A `SECURITY DEFINER` function runs with its **owner's** privileges. An attacker who can create
objects in any schema on the function's `search_path` can hijack an unqualified reference
(function, operator, type) inside the function body and get it to execute arbitrary code as the
owner — this is a real, named escalation class, not a theoretical concern.

```sql
CREATE OR REPLACE FUNCTION fn_transfer_funds(
    p_from_account_id BIGINT,
    p_to_account_id   BIGINT,
    p_amount          NUMERIC(12, 2)
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''         -- safest: empty, forces schema-qualification below
AS $$
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Transfer amount must be positive, got %', p_amount;
    END IF;

    UPDATE public.accounts SET balance = balance - p_amount   -- schema-qualified
    WHERE id = p_from_account_id AND balance >= p_amount;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Insufficient funds or account % not found', p_from_account_id;
    END IF;

    UPDATE public.accounts SET balance = balance + p_amount
    WHERE id = p_to_account_id;
END;
$$;

REVOKE EXECUTE ON FUNCTION fn_transfer_funds(BIGINT, BIGINT, NUMERIC) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION fn_transfer_funds(BIGINT, BIGINT, NUMERIC) TO app_transfer_role;
```

**The full hardening checklist, in order of impact:**

1. **`SET search_path = ''`** on the function, then schema-qualify every object reference
   inside it (`public.accounts`, not `accounts`). This is the safest option. If you must
   reference multiple trusted schemas, list them explicitly and put `pg_temp` **last** —
   never let a session-controlled schema resolve before your trusted ones.
2. **`REVOKE EXECUTE ... FROM PUBLIC`** immediately after creation — functions are executable
   by `PUBLIC` by default, which is almost never what you want for a `SECURITY DEFINER`
   function. Grant explicitly to the roles that actually need it.
3. **`REVOKE CREATE ON SCHEMA public FROM PUBLIC`** at the database level, removing untrusted
   users' ability to create objects anywhere on a plausible search path in the first place.
   This has been the default for the `public` schema since PostgreSQL 15 — verify it wasn't
   re-granted, don't assume the default holds on an upgraded-from-older-version database.
4. Prefer `SECURITY INVOKER` (the default) whenever the function doesn't specifically need to
   run with elevated privileges. Reach for `SECURITY DEFINER` only when the privilege
   escalation is the actual point (e.g., a controlled, audited funds-transfer function), not as
   a convenience to avoid granting table privileges properly.

## Schemas as namespacing — there is no package construct

PostgreSQL has no package/module construct for PL/pgSQL. Use **schemas** to group related
functions and tables and to create a privilege boundary: a "hard shell" API schema where
callers get `EXECUTE` on functions but no direct table grants. Manage `search_path`
deliberately per role and per function — don't rely on a database-wide default that every
function silently inherits.

## Testing, debugging, and when to skip PL/pgSQL entirely

- **`plpgsql_check`** — static analysis for PL/pgSQL: unused variables, type mismatches, dead
  code, and some classes of SQL errors, plus a profiler.
- **pgTAP** — a TAP-output unit-testing framework for functions and schema.
- **`auto_explain`** — logs execution plans; enable
  `auto_explain.log_nested_statements` to see plans for queries running *inside* a function.
- **Skip PL/pgSQL for a pure expression or single query.** A plain **SQL function**
  (`LANGUAGE sql`) can be **inlined** by the planner for simple cases, avoiding the PL/pgSQL
  executor entirely. Prefer **SQL-standard function bodies** (`LANGUAGE sql BEGIN ATOMIC ...
  END`, PG14+) over the traditional string-body (`AS $$ ... $$`) form: the body is parsed at
  creation time — catching syntax errors immediately instead of at first call — and, more
  importantly, PostgreSQL records real **dependencies** on the objects referenced inside, so
  `DROP ... CASCADE` and rename-tracking work correctly. Caveat: the semicolons inside
  `BEGIN ATOMIC` have broken some older database-driver SQL-splitters (older Npgsql/PgJDBC
  versions) — verify your driver handles it before adopting broadly.

## `ALTER TABLE` lock levels and rewrite triggers — the full cheat sheet

PostgreSQL DDL is **transactional** — a real strength for migrations, since multiple DDL
statements inside `BEGIN; ... COMMIT;` either all apply or all roll back cleanly. The exception:
`CREATE/DROP/REINDEX ... CONCURRENTLY` and some `ALTER TYPE ... ADD VALUE` forms **cannot** run
inside a transaction block at all.

| Operation | Lock | Rewrites table? |
|---|---|---|
| `ADD COLUMN` (no default, or non-volatile default, PG11+) | `ACCESS EXCLUSIVE`, but instant — metadata-only | No |
| `ADD COLUMN ... DEFAULT <volatile expr>` (`now()`, `gen_random_uuid()`, `random()`) | `ACCESS EXCLUSIVE` | **Yes, full rewrite** |
| `ADD COLUMN` as `STORED` generated, or as an identity column | `ACCESS EXCLUSIVE` | **Yes, full rewrite** |
| `ADD COLUMN` as `VIRTUAL` generated (PG18+) | `ACCESS EXCLUSIVE`, but instant | No — never rewrites, by construction |
| `DROP COLUMN` | `ACCESS EXCLUSIVE`, but instant — metadata-only | No |
| `SET NOT NULL` (no prior validated CHECK proving it) | `ACCESS EXCLUSIVE` | Scans, doesn't rewrite |
| `SET NOT NULL` (with a prior validated `CHECK (col IS NOT NULL)`, PG12+) | `ACCESS EXCLUSIVE`, but instant | No — planner reuses the validated CHECK, skips the scan |
| `ALTER COLUMN TYPE` (general case) | `ACCESS EXCLUSIVE` | **Yes, table + indexes** |
| `ALTER COLUMN TYPE` — `varchar(n)` widening, `varchar`→`text`, `numeric(p,s)`→`numeric` | `ACCESS EXCLUSIVE`, but instant | No — metadata-only exceptions |
| `ADD CONSTRAINT ... CHECK (...)` (no `NOT VALID`) | `ACCESS EXCLUSIVE` | Scans, doesn't rewrite, but blocks everything while scanning |
| `ADD CONSTRAINT ... CHECK (...) NOT VALID` | `ACCESS EXCLUSIVE`, but instant | No |
| `VALIDATE CONSTRAINT ...` | `SHARE UPDATE EXCLUSIVE` — does not conflict with normal reads/writes | Scans, concurrently with live traffic |
| `ADD FOREIGN KEY ...` (with or without `NOT VALID`) | `SHARE ROW EXCLUSIVE` on child **and** referenced parent | No; `NOT VALID` skips the validation scan, not the lock |
| `RENAME` (table/column) | `ACCESS EXCLUSIVE`, but instant — metadata-only | No |
| `SET STORAGE` | `ACCESS EXCLUSIVE`, but instant — metadata-only | No |

**Practical rules that follow from the table:**
- Verify empirically whether a given `ALTER` rewrote the table by comparing
  `pg_relation_filenode('tbl')` before and after — a changed filenode means a rewrite happened.
- Always set `lock_timeout` before running DDL on a table with live traffic, so a blocked
  `ACCESS EXCLUSIVE` acquisition fails fast instead of queuing behind — and blocking — every
  other statement that arrives after it.
- Never add a volatile-default or `STORED`-generated column to a large, live table in a single
  step. Add it nullable (or `VIRTUAL`) first, backfill in batches if needed, then add the
  default/constraint via the `NOT VALID` → `VALIDATE` pattern described in the main skill file.
