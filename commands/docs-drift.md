---
description: Flag documentation that has drifted from changed code (via drift.lock anchors), and optionally draft the fixes.
argument-hint: "[--fix] [base..head]"
---

# /docs-drift

Detects production-code documentation that no longer matches the code, using the repo's `drift.lock`
anchors (see the `documenting-code` skill). Reports stale and undocumented items; with `--fix`,
drafts the updates as a reviewable diff. Load the `documenting-code` skill for the discipline.

## Resolve scope

- Repo root via `git rev-parse --show-toplevel` (fallback `pwd`). Read `<root>/drift.lock` if present.
- Change set: the working diff by default, or the range given as an argument (e.g. `HEAD~1..HEAD`,
  `main..`). Use `git diff --name-only <range>` and `git diff <range>` for changed files/symbols.

## Steps

1. **Changed symbols.** From the diff, list changed files and the public symbols they touch
   (functions, classes, types, exported members, route handlers).
2. **Stale anchors.** For each `drift.lock` entry whose `anchor` file is in the change set, recompute
   the normalized hash of the anchored symbol (per `documenting-code/references/drift-lock.md`).
   Entry hash differs → **STALE** (the doc describes code that changed).
3. **Undocumented changes.** A changed **public** symbol with no `drift.lock` anchor and no docstring
   → **UNDOCUMENTED**.
4. **Textual references.** Also grep `docs/`, `README*`, and `*.md` for the changed file paths,
   symbol names, or endpoints, and list any that mention them (candidate stale prose without an anchor).
5. **Report.** Print two lists — STALE (doc ↔ anchor) and UNDOCUMENTED (symbol) — plus the textual hits.

## `--fix`

For each STALE/UNDOCUMENTED item: draft the doc update via the `documenting-code` discipline
(generate from the current source; match the repo's docstring convention), then refresh the
`drift.lock` entry's `hash` + `updated`. Present everything as a **diff for human review — never
auto-commit.** Where intent is genuinely ambiguous, insert a `TODO(doc-drift: …)` instead of guessing.

## Rules

- Read-only without `--fix` (no writes). With `--fix`, write drafts + `drift.lock`, but do not commit.
- Never refresh a `drift.lock` hash without actually re-reconciling the prose against the code.
- If there is no `drift.lock`, still run steps 1/3/4 (undocumented + textual), and offer to create one.
