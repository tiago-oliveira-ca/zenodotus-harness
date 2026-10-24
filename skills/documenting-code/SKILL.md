---
name: documenting-code
description: >
  The discipline for documenting production code and keeping the docs accurate — docstrings, API
  reference, READMEs, architecture notes, and code walkthroughs. Generate docs FROM the source of
  truth, document only doc-worthy changes (public API / architecture / dependencies / setup), pick
  the right generator and docstring convention per stack, and defend against drift (doctests →
  drift.lock anchors → /docs-drift). Draft, then let a human approve; leave an explicit TODO when
  you can't reconcile. Orchestrates zeno-doc-updater, /update-docs, /update-codemaps, zeno-stack/zeno-code-tour.
  Trigger on: "document this", "write docstrings", "API docs", "generate docs", "update the README",
  "document the code", "keep docs in sync", "docs are stale", "documentation drift", "doc coverage".
---

# Documenting code — accurate docs, generated from the source of truth

When documenting production code, the goal is not "some prose exists" — it is **docs that match the
code and stay matched.** Documentation that lies is worse than none, because it is trusted.

**Iron Law: DOCS ARE GENERATED FROM THE SOURCE OF TRUTH AND VERIFIED — never hand-copied from code
you hope is current.** If a doc restates behavior, that behavior must be read from the code (or a
generator run over it) in this pass, not remembered.

**Scope boundary:** this skill owns *code-level* docs (docstrings, API reference, README, code
walkthroughs, drift). **Delivery documents** (BRD → PRD → FRD → ADR → SAD…) belong to the
`documentation` dispatcher — route "write a PRD/ADR/spec" there, not here.

This skill is the *discipline*. The mechanical work is done by tools it orchestrates (below); its
job is deciding **whether, what, when**, and keeping the result honest.

## 1. When to document (trigger table)

Document on a **doc-worthy** change; skip minor internal churn so docs don't turn to noise.

| Change | Document? |
|---|---|
| New public feature / command / endpoint | Yes |
| API / route / public signature change | Yes |
| Dependency added or removed | Yes (setup + README) |
| Architecture / data-flow change | Yes (codemap + notes) |
| Changed setup / build / run steps | Yes (README / getting-started) |
| Internal refactor, private helper, formatting | No |
| Bug fix with no interface change | No (unless it changes documented behavior) |

## 2. Document at the source

Prefer **docstrings / doc-comments at the definition** over prose files that re-state code — they
feed every generator, live next to what they describe, and survive refactors. Detect and **match the
repo's existing convention** (don't introduce Google-style docstrings into a NumPy-style codebase).
See the language `code-standards` sub-skill for that stack's docstring rules.

## 3. Pick the right generator + convention (drive it, don't reinvent extraction)

| Stack | Generator | Docstring / comment convention |
|---|---|---|
| Python | Sphinx + autodoc, or MkDocs + `mkdocstrings` | Google / NumPy / reST (match the repo) |
| TypeScript / JS | TypeDoc (TS), JSDoc | TSDoc / JSDoc tags |
| Swift | DocC | `///` markup |
| Go | godoc / pkg.go.dev | doc comments (sentence starts with the name) |
| Rust | rustdoc | `///` + doc-tests |
| C / C++ / multi-lang | Doxygen | Doxygen comments |
| Java | Javadoc | Javadoc tags |
| R | roxygen2 | `#'` tags |
| Oracle PL/SQL | `ploc` (npx → Markdown), or `plsql-md-doc` | JavaDoc `/** */` tags on the package spec — see `references/plsql-docs.md` |

For **Oracle PL/SQL**, the tag grammar, generator choice (`ploc` vs `plsql-md-doc`), and the separate
schema-doc tools (SchemaSpy, `DBMS_METADATA.GET_DDL`) are detailed in `references/plsql-docs.md`.
Author the docstrings per `code-standards/database-data-modeling/oracle-plsql/SKILL.md` §8.

Site tooling, when a docs site is wanted: default to **MkDocs Material** (low-friction, `mkdocstrings`
for API docs) unless the repo's stack dictates otherwise (Starlight/Docusaurus/Fumadocs). The
load-bearing pattern is **docs-as-code**: Markdown in the repo, built in CI, reviewed in the same PR
as the code. Do not bundle or install any of these — recommend per repo.

## 4. Role split — produce what's needed, not everything

Different jobs, invoked on demand: **reference** (what each symbol does — from docstrings),
**tutorial** (task walkthroughs — cite `zeno-stack/zeno-code-tour`), **API** (endpoints/signatures — from the
generator), **diagram** (architecture/flow — cite `puml-diagrams`). Don't generate all four for a
one-endpoint change.

## 5. Drift discipline (cheapest first — the core value)

The reason docs rot: code changes go through review, CI, and merge gates; docs go through nothing.
Put them behind the same gate, layered:

1. **Doctests first.** Prefer docstrings with runnable examples (Python `doctest`, Rust doc-tests) so
   an example that goes stale **fails CI** — zero extra infra.
2. **Anchor prose docs to code** in a repo-root **`drift.lock`** (see `references/drift-lock.md`):
   each prose claim about code is bound to the symbol it describes, with a hash. On any change, the
   agent asks *"which docs are anchored to the code I just touched?"* and reconciles them.
3. **`/docs-drift`** — on a diff, flag docs whose anchored code changed (stale) and changed public
   symbols with no doc anchor (undocumented). Draft the fix; refresh the anchors.

For repos that need hard guarantees, **recommend** (never bundle) external CI backstops: doctests,
Fiberplane `drift`, Doc Detective.

## 6. Draft → review; TODO on uncertainty

**Automation drafts; the human approves before publish.** Never silently overwrite docs. And when you
cannot confidently reconcile a doc to the code — the intent is genuinely ambiguous — leave an
explicit `TODO(doc-drift: <what's unclear>)` rather than guessing a plausible-but-wrong description.

## 7. Orchestrated tools (this skill decides; these do the work)

- `/update-codemaps` — structural/architecture maps → `docs/CODEMAPS/`.
- `/update-docs` — prose/README/guide sync from sources of truth.
- `zeno-doc-updater` agent — generation runs (jsdoc2md, dependency graphs, codemaps). This is the
  Review-gate's one hardcoded, always-available agent invocation (`zeno/SKILL.md`'s "sanctioned
  exception" to registry-only selection) — this skill is where that wiring actually lives.
- `zeno-stack/zeno-code-tour` — step-through `.tour` walkthroughs.

**Related, not orchestrated:** `zeno-comment-analyzer` — an Advisor-tier agent that audits inline
comments for rot. Select it from `agents/REGISTRY.md` like any other specialist when comment
quality is in scope; this skill doesn't invoke it automatically the way it does the four tools
above.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Hand-writing prose that restates code from memory | Generate from the source; read the code this pass |
| Documenting every internal change | Fire only on the trigger table (API / arch / deps / setup) |
| Prose files that duplicate what docstrings should hold | Document at the definition; generate reference from it |
| Introducing a new docstring style into the repo | Match the convention already in use |
| Publishing generated docs without review | Draft → human approves → publish |
| Guessing a description when intent is unclear | Leave an explicit `TODO(doc-drift:)` |
| Leaving docs out of the change's verification | Run `/docs-drift`; reconcile anchored docs |
| Bundling MkDocs/Docusaurus/Mintlify as a dependency | Recommend per repo; install nothing |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "The docs are probably still right" | "Probably" is how docs lie; read the code or run the generator |
| "It's a small change, skip the docs" | If it touched a public API, it's doc-worthy — check the trigger table |
| "I'll write the README from what I remember" | Memory drifts from code; generate from the source |
| "I'll just update the prose to match, roughly" | Roughly-right docs mislead; anchor + verify, or leave a TODO |

## Red flags — stop before you claim the docs are done

- You wrote a description without opening the code it describes.
- You changed a public signature and touched no doc.
- You're publishing generated docs no human has reviewed.
- A doc's claim is ambiguous and you're about to guess instead of leaving a TODO.

## Pre-flight checklist — run before delivering any documentation

- [ ] The change was checked against the trigger table; docs updated only if doc-worthy.
- [ ] Docs were generated from / verified against the current source, not memory.
- [ ] Docstrings match the repo's existing convention for the stack.
- [ ] Anchored docs reconciled via `drift.lock` / `/docs-drift`; examples are doctest-backed where possible.
- [ ] Any unreconcilable doc carries an explicit `TODO(doc-drift:)`.
- [ ] Generated docs are presented as a draft for human review, not auto-published.
