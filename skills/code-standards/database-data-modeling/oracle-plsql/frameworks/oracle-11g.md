# Oracle 11g — Legacy / Pre-12c Specifics

**Scope:** load this file **only** when the work explicitly targets a legacy, pre-12c Oracle
deployment (11g or earlier). General, version-agnostic PL/SQL practices — naming, anchored
declarations, exception handling, bind variables, bulk processing, `NOCOPY`, explicit cursors,
package encapsulation, and the core architectural principles — live in the parent `SKILL.md` and
apply on 11g too. This file only carries what is genuinely scoped to a true 11g system.

---

## 1. Diagnostic tooling on a true 11g system

When queries are slow on an actual 11g instance, reach for the tooling shipped with that era.
(These tools exist in later Oracle versions too — often extended — but the workflow below is what
to lean on when you are constrained to 11g specifically. On a modern instance, prefer the
`DBMS_XPLAN` / SQL Plan Management / `DBMS_STATS` workflow in `../references/clean-architecture.md`.)

1. **`EXPLAIN PLAN` / `DBMS_XPLAN.DISPLAY`** — check whether indexes are used, identify full table scans, and inspect join methods (Hash Join vs Nested Loops).
2. **Automatic Workload Repository (AWR)** — review reports to identify the top resource-consuming SQL across the instance.
3. **SQL Tuning Advisor** — pass a slow SQL ID to the advisor to get automated recommendations on missing indexes or restructured SQL.

---

## 2. Fine-grained (column-level) dependency tracking

Oracle 11g tracks dependencies at the **column level**, not the object level. If you add a column
to a table, procedures that don't reference that new column will **not** be invalidated. Use
explicit column lists in `INSERT` and `SELECT` statements to fully benefit from this — a practice
that is good hygiene on any version, and specifically rewarded by 11g's dependency model.

---

## 3. Result caching and deterministic functions

`RESULT_CACHE` and `DETERMINISTIC` were **introduced in 11g and are safe on any later version too**
— they are not an 11g-only novelty, and modern code should use them freely. They are noted here
because they first appeared in this release. If a function is called repeatedly with the same
inputs (especially inside SQL queries), leverage them:

- **`DETERMINISTIC`**: Tells the optimizer the function always returns the same result for the same input. Useful for function-based indexes.
- **`RESULT_CACHE`**: Oracle stores the function's result in the Shared Pool; subsequent calls retrieve the cached value instantly.

```sql
FUNCTION get_department_name(I_dept_id IN NUMBER) 
    RETURN VARCHAR2 RESULT_CACHE RELIES_ON(departments) IS ...
```
