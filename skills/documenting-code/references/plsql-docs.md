# Documenting Oracle PL/SQL

How to document PL/SQL (packages, procedures, functions, triggers) as **Markdown, docs-as-code** —
the convention to write and the generator to drive. Nothing here is bundled; recommend per repo.

## Convention — JavaDoc `/** … */` tags on the package spec

Document the **package spec** (the published contract callers see), not the body. Put a JavaDoc-style
block above each public declaration. This is the de-facto PL/SQL convention (from PLDoc, reused by
the Markdown tools below). **Match the repo's existing style if one is already in use.**

Tag set (from `OraOpenSource/plsql-md-doc`):

| Tag | Use |
|---|---|
| `@param <name> <desc>` | one per parameter (note mode in the desc if not obvious) |
| `@return <desc>` | for functions |
| `@throws <exception> <when>` | raised exceptions the caller must handle |
| `@example <snippet>` | a runnable call example (fenced ```` ```sql ```` renders directly) |
| `@author` / `@created` | provenance |
| `@type <type>` | for documented variables / columns |
| `@constant` | for package constants |

Example (in the `.pks` spec):

```sql
/**
 * Charge a customer's default payment method.
 *
 * @param  p_customer_id  ID of the customer to charge (IN)
 * @param  p_amount       Amount in minor units; must be > 0
 * @return the created payment's ID
 * @throws e_no_payment_method  when the customer has no default method
 * @example
 *   l_id := billing_pkg.charge(p_customer_id => 42, p_amount => 1999);
 * @author  T. Oliveira
 * @created 2026-08-05
 */
FUNCTION charge(p_customer_id IN NUMBER, p_amount IN NUMBER) RETURN NUMBER;
```

## Generators (both output Markdown → commit next to the code, review in the same PR)

- **`ogobrecht/ploc`** (default drive target) — MIT, maintained (2024), run with **`npx ploc`** (needs
  only Node). Authoring is **Markdown inside `/** … **/`** blocks after a `PACKAGE`/`FUNCTION`/
  `PROCEDURE`/`TYPE`/`TRIGGER` keyword (note the closing `**/`); auto-generates TOC, signatures, and
  renders fenced examples. Best fit for docs-as-code and the safest maintenance bet.
- **`OraOpenSource/plsql-md-doc`** (when the repo wants the strict JavaDoc tag grammar above) — MIT,
  `node app <project>`, Handlebars templates. Defines the canonical tag set; code is stale (last
  shipped 2020) but stable — prefer it only if a repo already standardizes on these tags.

Pick per repo: strict JavaDoc tags already in the codebase → `plsql-md-doc`; greenfield / prefer
Markdown-in-comments → `ploc`.

## Schema / DDL docs — a *separate* need (not PL/SQL logic)

Documenting tables, relationships, and DDL is a different job — don't conflate it with logic docs:

- **SchemaSpy** — active, LGPL; HTML + ER diagrams (GraphViz) over JDBC. Best human-facing schema map.
- **`DBMS_METADATA.GET_DDL`** — built into Oracle, zero install; extracts exact source-of-truth DDL
  (incl. package source) as SQL. Use when you want authoritative DDL rather than rendered docs.
- **SchemaCrawler** — scriptable schema dumps/diffs/lint for CI.

## Skip / landscape (do not drive)

- **PLDoc classic** (SourceForge) — HTML-only, unmaintained since 2019. Historically defined the
  javadoc-tag convention; that lineage is all that survives.
- **Doxygen + PL/SQL input-filter / HyperSQL** — brittle, HTML-oriented (Doxygen has no native PL/SQL
  parser).
- **SQL Developer "DB Doc" / Toad / PL/SQL Developer / Quest** — GUI/commercial, HTML/RTF, not
  scriptable or headless.
- **utPLSQL** — a testing framework, not a doc generator.

## Drift

PL/SQL docs obey the same discipline as any stack: fire on doc-worthy changes (trigger table), anchor
prose to the spec in `drift.lock`, and reconcile via `/docs-drift`. Because docs are generated from
the spec, a spec-signature change is exactly what should flag the doc stale.
