---
name: oracle-plsql
description: >
  Production Oracle SQL / PL-SQL code standards that hold across every supported Oracle version —
  naming, anchored types, exception handling, bind variables, bulk processing, cursors, packages —
  plus Oracle AI Database 26ai (AI Vector Search, RAG, OCI GenAI) and DDD / Clean Architecture on
  Oracle. Use when writing, reviewing, or designing Oracle PL/SQL, SQL, schemas, or migrations.
  Trigger on: "PL/SQL", "PL-SQL", "Oracle", "Oracle procedure", "Oracle package", "Oracle
  function", "Oracle query", "FORALL", "BULK COLLECT", "vector search Oracle", "DBMS_VECTOR",
  "AI Vector Search", "Oracle 26ai", "Oracle AI Database", "OCI GenAI", "HNSW", "IVF index",
  "RAG oracle", "oracle embeddings", "Oracle DDD", "Oracle Clean Architecture", "oracle
  repository", "utPLSQL", "SKIP LOCKED".
---

# Oracle PL/SQL Code Standards

When writing or reviewing SQL and PL/SQL for Oracle, follow these standards. They focus on
performance, maintainability, and safe database interactions. Everything in this file is
**version-agnostic PL/SQL language mechanics** — the practices below hold true across all supported
Oracle versions, from 11g through 26ai. Version- and product-tier-specific material lives in the
routed files below.

## Routing — which file to load

Load the core standards on this page for any Oracle PL/SQL task. Then reach for a routed file
**only** when its signal is present:

| Load | When |
|---|---|
| `frameworks/oracle-11g.md` | Only when the target system is **explicitly a legacy / pre-12c deployment**. Covers the genuinely 11g-scoped remainder: 11g-era diagnostic tooling, fine-grained (column-level) dependency tracking, and result-cache/deterministic framing. |
| `frameworks/oracle-26ai.md` | Only when a **vector / AI / GenAI / JSON-duality** signal is present — VECTOR columns, AI Vector Search, `DBMS_VECTOR`/`DBMS_HYBRID_VECTOR`, HNSW/IVF, RAG, OCI GenAI, ORDS-as-API, JSON-Relational Duality Views, `SKIP LOCKED` work queues. |
| `references/clean-architecture.md` | Clean Code, DDD, and Clean Architecture for Oracle — bounded contexts → schemas, aggregate mapping, repository-as-package, unit of work, read models, migration/testing/security strategy. |

There is **no default to 11g.** For new or unspecified work, the core content on this page — plus
`frameworks/oracle-26ai.md` if (and only if) a vector/AI/GenAI/JSON-duality signal is present — is
sufficient. Do not reach for `frameworks/oracle-11g.md` unless the deployment is explicitly a
legacy pre-12c one; most PL/SQL language mechanics below apply unchanged on any modern Oracle
version.

---

## 1. Guiding Principles

- **Let SQL do the work:** If you can achieve a result with a single SQL statement, do it. Only fall back to PL/SQL for complex procedural logic or multi-step processing that SQL cannot handle efficiently.
- **Minimize Context Switching:** The transition between the PL/SQL engine and the SQL engine is expensive. Use bulk processing (`FORALL`, `BULK COLLECT`) to minimize this overhead.
- **Write Secure Code:** SQL injection is a severe risk. **Always** use bind variables.
- **Design for Performance:** Understand execution plans, use appropriate indexes, and avoid applying functions to indexed columns in `WHERE` clauses.
- **Encapsulate Logic:** Never write standalone procedures or functions in production. Always group related subprograms into packages.

---

## 2. Naming Conventions

Consistent naming makes code self-documenting and easier to maintain.

### 2.1 General Rules
- Use deep, descriptive names.
- Avoid Oracle keywords (e.g., `SELECT`, `TABLE`, `DATE`).
- Do **not** use double quotes (`"MyTable"`) for object names to prevent case-sensitivity nightmares. Keep everything conceptually uppercase, written in lowercase or standard camelCase depending on your team's preference.

### 2.2 PL/SQL Identifiers (Prefixing)

Use standard prefixes to immediately identify the scope and nature of variables:

| Type | Prefix | Example |
|---|---|---|
| Local Variable | `L_` | `L_employee_id` |
| Global/Package Variable | `G_` | `G_max_retries` |
| Parameter (IN) | `I_` | `I_department_name` |
| Parameter (IN OUT) | `IO_` | `IO_status_code` |
| Parameter (OUT) | `O_` | `O_employee_id` |
| Constant | `C_` |  `C_status_active` |
| Record | `R_` | `R_employee_rec` |
| Collection/Table Type | `T_` | `T_employee_list` |
| Exception | `E_` | `E_invalid_department` |
| Cursor | `CUR_` | `CUR_active_employees` |

### 2.3 Object Naming
- **Packages:** Suffix with `_SQL` (e.g., `HR_MANAGEMENT_SQL`).
- **Views:** Prefix with `V_` (e.g., `V_ACTIVE_EMPLOYEES`).
- **Materialized Views:** Prefix with `MV_` (e.g., `MV_MONTHLY_SALES`).
- **Triggers:** Prefix with `TRG_` and indicate timing/event (e.g., `TRG_EMP_BI_ROW` for Before Insert Row).
- **Sequences:** Suffix with `_SEQ` (e.g., `employee_id_SEQ`).

---

## 3. PL/SQL Coding Standards

### 3.1 Anchored Declarations (`%TYPE` and `%ROWTYPE`)

**Always** anchor variables to database columns instead of hardcoding types. If the table definition changes (e.g., extending a `VARCHAR2` from 50 to 100), your PL/SQL code will automatically adapt without recompilation errors.

```sql
-- ✅ Correct
l_employee_name employees.first_name%TYPE;
r_employee      employees%ROWTYPE;

-- ❌ Wrong (Brittle if the column size changes)
l_employee_name VARCHAR2(50);
```

### 3.2 Proper Data Types
- Avoid initializing variables with `NULL` explicitly (they are `NULL` by default).
- Use `PLS_INTEGER` instead of `NUMBER` for simple integer arithmetic (loop counters, simple math) because it uses native machine arithmetic and is significantly faster.
- Use `SIMPLE_INTEGER` when the value is guaranteed `NOT NULL` and overflow wrapping is acceptable (even faster than `PLS_INTEGER`).

### 3.3 Avoid Implicit Conversions

Implicit conversions force the database to do extra work and can disable index usage.

```sql
-- ✅ Correct
IF l_hire_date > TO_DATE('2024-01-01', 'YYYY-MM-DD') THEN ...

-- ❌ Wrong (Implicit string to date conversion)
IF l_hire_date > '01-JAN-24' THEN ...
```

### 3.4 Exception Handling

- **Never** swallow exceptions silently with a bare `WHEN OTHERS THEN NULL;`.
- Catch specific exceptions first (`NO_DATA_FOUND`, `TOO_MANY_ROWS`).
- Use `RAISE_APPLICATION_ERROR` for custom application errors (range -20000 to -20999).
- Log errors to an audit table before raising them up the stack.

```sql
BEGIN
    SELECT salary INTO l_salary FROM employees WHERE employee_id = I_emp_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        pkg_logger.log_error('Employee ' || I_emp_id || ' not found.');
        RAISE_APPLICATION_ERROR(-20001, 'Invalid Employee ID provided.');
    WHEN OTHERS THEN
        pkg_logger.log_error('Unexpected Error: ' || SQLERRM);
        RAISE; -- Re-raise to caller; never suppress OTHERS silently
END;
```

**Common Built-In Exceptions Catalog:**

| Exception | ORA Code | When It Fires |
|---|---|---|
| `NO_DATA_FOUND` | ORA-01403 | `SELECT INTO` returns zero rows |
| `TOO_MANY_ROWS` | ORA-01422 | `SELECT INTO` returns more than one row |
| `DUP_VAL_ON_INDEX` | ORA-00001 | Unique constraint violation on INSERT/UPDATE |
| `VALUE_ERROR` | ORA-06502 | Type conversion failure or length overflow |
| `ZERO_DIVIDE` | ORA-01476 | Division by zero |
| `CURSOR_ALREADY_OPEN` | ORA-06511 | Opening an already-open cursor |
| `INVALID_NUMBER` | ORA-01722 | Cannot convert string to NUMBER in SQL |
| `ROWTYPE_MISMATCH` | ORA-06504 | Cursor variable row type mismatch |

**User-Defined Exception Pattern (declare once, reuse in package):**

```sql
-- Package specification
CREATE OR REPLACE PACKAGE pkg_exceptions AS
    -- Assign permanent error numbers to named constants
    e_employee_not_found   EXCEPTION;
    e_salary_below_minimum EXCEPTION;

    cur_employee_not_found   CONSTANT NUMBER := -20001;
    c_salary_below_minimum CONSTANT NUMBER := -20002;

    PRAGMA EXCEPTION_INIT(e_employee_not_found,   -20001);
    PRAGMA EXCEPTION_INIT(e_salary_below_minimum, -20002);
END pkg_exceptions;
```

```sql
-- Usage in any procedure
BEGIN
    UPDATE employees SET salary = I_salary WHERE employee_id = I_emp_id;
    IF SQL%ROWCOUNT = 0 THEN
        RAISE pkg_exceptions.e_employee_not_found;
    END IF;
EXCEPTION
    WHEN pkg_exceptions.e_employee_not_found THEN
        RAISE_APPLICATION_ERROR(pkg_exceptions.cur_employee_not_found,
                                'Employee not found: ' || I_emp_id);
END;
```

**Savepoint Pattern for Partial Rollback:**

```sql
PROCEDURE process_batch IS
BEGIN
    SAVEPOINT before_batch;
    -- ... batch DML ...
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO before_batch;   -- Only undo this procedure's work
        pkg_logger.log_error(SQLERRM, DBMS_UTILITY.FORMAT_ERROR_BACKTRACE);
        RAISE;
END;
```

---

## 4. PL/SQL Performance Best Practices

### 4.1 Bind Variables (CRITICAL)

**Always** use bind variables for dynamic SQL. They prevent SQL injection and allow Oracle's Shared Pool to cache the execution plan (Hard Parse vs Soft Parse).

```sql
-- ✅ Correct (Soft Parse, safe)
EXECUTE IMMEDIATE 'UPDATE employees SET salary = :1 WHERE dept_id = :2' 
    USING I_new_salary, I_dept_id;

-- ❌ Wrong (Hard Parse every execution, vulnerability)
EXECUTE IMMEDIATE 'UPDATE employees SET salary = ' || I_new_salary || 
                  ' WHERE dept_id = ' || I_dept_id;
```

### 4.2 Bulk Processing (`FORALL` and `BULK COLLECT`)

Replace row-by-row cursor loops (which cause excessive context switching) with bulk operations.

```sql
-- ✅ Correct: BULK COLLECT with LIMIT (prevents PGA memory exhaustion)
DECLARE
    CURSOR cur_emp IS SELECT employee_id, first_name, last_name
                    FROM employees WHERE department_id = 10;
    TYPE t_emp IS TABLE OF cur_emp%ROWTYPE;
    l_emps t_emp;
BEGIN
    OPEN cur_emp;
    LOOP
        FETCH cur_emp BULK COLLECT INTO l_emps LIMIT 1000;
        EXIT WHEN l_emps.COUNT = 0;
        
        -- FORALL for bulk DML
        FORALL i IN 1..l_emps.COUNT
            UPDATE employees SET salary = salary * 1.1 
            WHERE employee_id = l_emps(i).employee_id;
    END LOOP;
    CLOSE cur_emp;
END;
```

### 4.3 The `NOCOPY` Hint
For large collections or records passed as `OUT` or `IN OUT` parameters, use the `NOCOPY` hint. By default, Oracle passes these by value (making a copy). `NOCOPY` passes by reference, saving significant memory and CPU.

```sql
PROCEDURE process_large_data (IO_data_collection IN OUT NOCOPY t_large_table) IS ...
```

### 4.4 Explicit Cursors — only when procedural fetch control is needed

Set-based SQL and `BULK COLLECT`/`FORALL` (§4.2) come first — that rule wins whenever the two
collide. Reach for an **explicit cursor** only when the loop genuinely needs procedural fetch
control (early exit on a data condition, batched `FETCH ... LIMIT` over an unbounded set,
`%ISOPEN`-guarded cleanup in exception paths) — and even then, fetch in bulk, never row-by-row.
For a simple bounded iteration, the implicit cursor `FOR` loop is fine: it array-prefetches 100
rows and is both shorter and typically faster than a hand-rolled single-row `OPEN`/`FETCH`/`CLOSE`
loop.

```sql
-- ✅ Explicit cursor earning its keep: batched fetch over an unbounded set
DECLARE
    CURSOR cur_emp IS SELECT first_name, last_name FROM employees WHERE dept_id = 10;
    TYPE t_emp IS TABLE OF cur_emp%ROWTYPE;
    l_batch t_emp;
BEGIN
    OPEN cur_emp;
    LOOP
        FETCH cur_emp BULK COLLECT INTO l_batch LIMIT 500;
        EXIT WHEN l_batch.COUNT = 0;
        -- process l_batch (and stop early on a data condition if needed)
    END LOOP;
    CLOSE cur_emp;
END;

-- ✅ Also fine for simple bounded iteration (array-prefetches 100 rows)
FOR r_emp IN (SELECT first_name, last_name FROM employees WHERE dept_id = 10) LOOP
    -- process r_emp
END LOOP;

-- ❌ Avoid: hand-rolled single-row fetch loop — the row-by-row pattern §4.2 forbids
-- OPEN c; LOOP FETCH c INTO r; EXIT WHEN c%NOTFOUND; ... END LOOP; CLOSE c;
```

> Function-level performance features that were **introduced in 11g** but are safe on any later
> version — `RESULT_CACHE` and `DETERMINISTIC` — are documented in `frameworks/oracle-11g.md`
> alongside the other legacy-scoped notes. Modern query-plan and statistics tooling
> (`DBMS_XPLAN`, SQL Plan Management, `DBMS_STATS`) is covered in `references/clean-architecture.md`.

---

## 5. SQL Query Optimization

### 5.1 Efficient Index Usage
- Avoid applying functions to columns in `WHERE` clauses, as it ignores standard B-tree indexes.

```sql
-- ❌ Wrong (Ignores index on last_name)
SELECT employee_id, last_name FROM employees WHERE UPPER(last_name) = 'SMITH';

-- ✅ Solution A: Exact match if case isn't an issue
SELECT employee_id, last_name FROM employees WHERE last_name = 'Smith';

-- ✅ Solution B: Create a Function-Based Index
CREATE INDEX idx_emp_upper_last ON employees (UPPER(last_name));
```

### 5.2 Query Structure
- **Avoid `SELECT *`**: Ask only for the columns you need.
- **Use `UNION ALL` instead of `UNION`**: Unless you explicitly need Oracle to remove duplicates (which requires an expensive sort), `UNION ALL` is significantly faster.
- **Filter Early**: Drive queries from the table that filters out the most rows the fastest (the "driving table").
- **Avoid `OR` conditions on different columns**: They often confuse the optimizer and lead to full table scans. Use `UNION ALL` instead.

For diagnosing slow SQL: modern instances use `DBMS_XPLAN`, AWR, and SQL Plan Management (see
`references/clean-architecture.md` → Performance Engineering). On a true legacy 11g system, see
`frameworks/oracle-11g.md` for the tooling to reach for there specifically.

---

## 6. Architecture & Design

### 6.1 Package Encapsulation
Do not create loose procedures or functions. Everything must be grouped logically into packages.
- **Specification (`.pks`)**: The public interface. Declares types, constants, and public subprograms.
- **Body (`.pkb`)**: The private implementation. Hides complex business logic from the caller.

---

## 7. Core Architectural Principles (apply regardless of Oracle version)

These six principles govern any Oracle work — classic or 26ai — and sit above the routed files.

### 7.1 Isolate Oracle power behind stable contracts
Oracle's rich feature set (packages, materialized views, JSON-relational duality, vector indexes, SQL Firewall) should be concentrated behind boundaries — PL/SQL package specs, views, or repository interfaces — so storage and implementation changes don't ripple outward.

### 7.2 Treat the package spec as the interface
PL/SQL packages provide a native "interface vs implementation" split:
- **Package spec** = stable public contract (analogous to an interface or abstract class)
- **Package body** = private implementation (can change without breaking callers)
- Use `AUTHID DEFINER` for least-privilege, schema-scoped execution

```sql
CREATE OR REPLACE PACKAGE order_repo AUTHID DEFINER IS
  PROCEDURE create_order(p_order_id IN VARCHAR2, p_customer_id IN VARCHAR2, p_order_date IN TIMESTAMP);
  PROCEDURE add_line(p_order_id IN VARCHAR2, p_line_no IN NUMBER, p_sku IN VARCHAR2, p_qty IN NUMBER, p_unit_price IN NUMBER);
  PROCEDURE set_status(p_order_id IN VARCHAR2, p_new_status IN VARCHAR2, p_expected_version IN NUMBER);
  FUNCTION  get_order_json(p_order_id IN VARCHAR2) RETURN CLOB;
END order_repo;
/
```

### 7.3 Aggregate boundary = transaction boundary
Map DDD aggregates to Oracle transactions explicitly:
- One root table + child tables keyed by `(aggregate_id, child_key)`
- State transitions inside one stored procedure call or one application transaction
- **Optimistic locking**: `VERSION` column updated in `WHERE` clause; `SQL%ROWCOUNT = 0` = conflict
- **Pessimistic locking**: `SELECT ... FOR UPDATE [NOWAIT | WAIT n | SKIP LOCKED]`

```sql
-- Optimistic concurrency pattern
UPDATE orders
SET    status  = :new_status,
       version = version + 1
WHERE  order_id = :order_id
AND    version  = :expected_version;
-- If SQL%ROWCOUNT = 0 -> raise concurrency conflict exception
```

### 7.4 Vector retrieval is a first-class architectural concern
VECTOR columns live in 26ai tables — treat them as typed, versioned columns:
- Always store `embedding_model_version` alongside the vector
- Match distance metric in the index to the embedding model (`COSINE` for most models)
- Size the Vector Pool (SGA) before creating HNSW indexes in production

```sql
-- Canonical retrieval primitive: relational predicates + similarity in one query
SELECT doc_id,
       title,
       VECTOR_DISTANCE(embedding_vec, :query_vec, COSINE) AS score
FROM   documents
WHERE  tenant_id = :tenant_id
AND    is_active = 1
ORDER  BY score
FETCH  FIRST 10 ROWS ONLY;
```

Full vector-search, embedding-lifecycle, and OCI GenAI detail is in `frameworks/oracle-26ai.md`.

### 7.5 DDL is not transactional — plan for it
Oracle issues implicit commits **before and after** DDL statements. Migration scripts must be designed accordingly:
- Use forward-only changesets (Liquibase/Flyway) — one logical change per changeset
- Never mix DDL and DML in the same "rollbackable" unit
- For zero-downtime changes: use EBR (Edition-Based Redefinition) or `DBMS_REDEFINITION`

### 7.6 Prompts and embeddings are regulated data flows
For GenAI workloads, treat prompts + retrieved context + model outputs as data with compliance implications:
- Minimize PII entering the prompt (chunk and redact first)
- Apply OCI Guardrails (content moderation, PII handling, prompt injection defense) at the service boundary
- Use SQL Firewall allowlisting for any agent-generated SQL paths

---

## 8. Documentation & comments (PL/SQL)

Document the **package spec** (the published contract callers see), not the body. Use a JavaDoc-style
`/** … */` block above each public declaration — the de-facto PL/SQL convention, and the one the
Markdown generators consume. Tags: `@param <name> <desc>`, `@return <desc>`, `@throws <exc> <when>`,
`@example <snippet>`, `@author`, `@created` (and `@type` / `@constant` for documented vars/constants).

```sql
/**
 * Charge a customer's default payment method.
 *
 * @param  p_customer_id  ID of the customer to charge (IN)
 * @param  p_amount       Amount in minor units; must be > 0
 * @return the created payment's ID
 * @throws e_no_payment_method  when the customer has no default method
 * @example  l_id := billing_pkg.charge(p_customer_id => 42, p_amount => 1999);
 */
FUNCTION charge(p_customer_id IN NUMBER, p_amount IN NUMBER) RETURN NUMBER;
```

- File/object header: purpose, author, and a change log — keep the change log current.
- Comment the *why* of non-obvious SQL (hints, bulk/`FORALL` operations, autonomous transactions), not the syntax.
- Keep spec comments in sync with the body signature — the spec is the contract callers see.

Rendering to Markdown docs (drive `ploc` / `plsql-md-doc`), schema-doc tools, and the cross-cutting
doc discipline (drift, when to update): see `documenting-code` → `references/plsql-docs.md`.

## Anti-pattern quick reference

| Anti-pattern | Problem | Fix |
|---|---|---|
| Hardcoded variable types (`l_name VARCHAR2(50)`) | Brittle if the column size/type changes | Anchor declarations with `%TYPE` / `%ROWTYPE` |
| Implicit conversions (`l_hire_date > '01-JAN-24'`) | Extra work; disables index usage | Explicit `TO_DATE`/`TO_CHAR` with a format mask |
| Bare `WHEN OTHERS THEN NULL;` | Silently swallowed exceptions | Catch specific exceptions first, log, then `RAISE` / `RAISE_APPLICATION_ERROR` |
| Concatenating values into dynamic SQL | SQL injection + hard parse every run | Bind variables via `EXECUTE IMMEDIATE ... USING` |
| Row-by-row cursor loops for multi-row DML | Excessive context switching | `BULK COLLECT ... LIMIT` + `FORALL` |
| Hand-rolled single-row `OPEN`/`FETCH`/`CLOSE` loops | Row-by-row context switching — the §4.2 sin in explicit-cursor clothing | Set-based SQL or `BULK COLLECT ... LIMIT`; explicit cursors only for procedural fetch control (§4.4) |
| Functions on indexed columns in `WHERE` | Ignores standard B-tree indexes | Exact match on the raw column, or a function-based index |
| `SELECT *` in queries / view / package contracts | Breaks callers silently on column reorder | Explicit column lists |
| `UNION` when duplicates don't need removing | Forces an expensive sort | `UNION ALL` |
| `OR` conditions on different columns | Confuses the optimizer; full scans | Rewrite as `UNION ALL` |
| Standalone procedures/functions in production | No encapsulation boundary | Group related subprograms into packages (spec + body) |
| Double-quoted object names (`"MyTable"`) | Case-sensitivity nightmares | Unquoted identifiers |
| `NUMBER` for simple integer arithmetic / loop counters | Slower software arithmetic | `PLS_INTEGER` (or `SIMPLE_INTEGER` when `NOT NULL` and overflow wrap is acceptable) |
| Large collections passed as `OUT`/`IN OUT` by value | Wasted memory + CPU on the copy | The `NOCOPY` hint (pass by reference) |
| Physical schema exposed as API | Tight coupling; any table rename breaks callers | Expose PL/SQL package APIs or stable views |
| Domain logic in triggers | Hidden control flow; hard to test; can cascade unexpectedly | Move invariants to package body procedures |
| DDL mid-transaction assuming rollback | Oracle implicitly commits around DDL | Plan migrations with forward-only changesets |
| LOB write without locking the row first | `DBMS_LOB` modify calls require a prior row lock | `SELECT ... FOR UPDATE` before `DBMS_LOB.WRITE` |
| Embedding column without a model version | Cross-version similarity is meaningless | Add an `embedding_model_version VARCHAR2` column |
| Agent-generated SQL without SQL Firewall | Prompt injection can yield destructive SQL | Enable SQL Firewall allowlisting on agent schemas |
| ORM-generated SQL for `SKIP LOCKED` workloads | Most ORMs cannot express `SKIP LOCKED` cleanly | Use explicit SQL or a PL/SQL dequeue procedure |

---

## Pre-flight checklist — run before delivering any Oracle PL/SQL code

- [ ] **Modularity:** Is everything encapsulated in a package (spec + body)?
- [ ] **Naming:** Do variables use `l_`, `g_`, `I_`, `IO_`, `O_` prefixes? Are object names unquoted?
- [ ] **Data Types:** Are declarations anchored with `%TYPE` or `%ROWTYPE`?
- [ ] **SQL Injection:** Are bind variables used exclusively for dynamic SQL?
- [ ] **Performance (DML):** Are `FORALL` and `BULK COLLECT` (with `LIMIT`) used for multi-row processing instead of row-by-row cursors?
- [ ] **Performance (Params):** Is the `NOCOPY` hint used for `OUT`/`IN OUT` collections?
- [ ] **Cursors:** Do explicit cursors appear only where procedural fetch control is needed, always fetching in bulk (`BULK COLLECT ... LIMIT`) — never as hand-rolled single-row loops (§4.4)?
- [ ] **Exception Handling:** Are exceptions caught specifically, logged, and properly re-raised? No bare `WHEN OTHERS THEN NULL`?
- [ ] **SQL Quality:** Is `SELECT *` avoided? Is `UNION ALL` preferred over `UNION`?
- [ ] **Indexing:** Are `WHERE` clauses clean of functions that would negate B-tree index usage?
- [ ] **Contracts:** Is Oracle-specific power isolated behind package specs, views, or repository interfaces?
- [ ] **Concurrency:** Is the aggregate boundary the transaction boundary, with an optimistic or pessimistic locking strategy chosen deliberately?
- [ ] **Migrations:** Are changesets forward-only, never assuming DDL rollback? (See `references/clean-architecture.md` for the full strategy.)
- [ ] **Documentation:** Is the package spec documented with the JavaDoc `/** */` convention?
