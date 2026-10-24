---
description: Safely identify and remove dead code with verification after each change.
---

# /refactor-clean

Finds dead code and removes it, verifying with the test suite after every single deletion so a
bad removal is caught immediately rather than discovered later.

> **Delegation:** for a standalone cleanup pass, spawn the `zeno-refactor-cleaner` agent — it
> runs this same job with the same tools under its own contract; the underlying doctrine lives
> in `zeno-stack/zeno-refactor-cleanup`. Use the inline steps below when working in the main
> thread on a scoped target.

## Step 1 — find dead code

Run whichever analyzer matches the project:

| Tool | Finds | Command |
|---|---|---|
| knip | Unused exports, files, dependencies | `npx knip` |
| depcheck | Unused npm dependencies | `npx depcheck` |
| ts-prune | Unused TypeScript exports | `npx ts-prune` |
| vulture | Unused Python code | `vulture src/` |
| staticcheck | Unused Go symbols (U1000) | `staticcheck ./...` |
| deptry | Unused/missing Python dependencies | `deptry .` |
| periphery | Unused Swift code | `periphery scan` |
| cargo-udeps | Unused Rust dependencies | `cargo +nightly udeps` |

If none of these are available, fall back to Grep: list exported symbols, then check each for any
importer.

## Step 2 — sort findings by risk

| Tier | Examples | Handling |
|---|---|---|
| **SAFE** | Unused utilities, test helpers, internal-only functions | Delete directly |
| **CAUTION** | Components, API routes, middleware | Confirm no dynamic import or external consumer first |
| **DANGER** | Config files, entry points, type definitions | Investigate before touching at all |

## Step 3 — delete SAFE items one at a time

For each:

1. Run the full test suite to establish a clean baseline.
2. Remove the dead code with a surgical edit.
3. Re-run the test suite.
4. If it fails, revert immediately with `git checkout -- <file>` and skip that item.
5. If it passes, move on to the next item.

## Step 4 — handle CAUTION items

Before deleting anything in this tier, check for:

- dynamic references (`import()`, `require()`, `__import__`)
- string-based references — route names or component names appearing in config
- export from a package's public API
- external consumers, if the code is published

Only delete once these come back clean.

## Step 5 — consolidate duplicates

With the dead code cleared, look for further cleanup opportunities:

- near-duplicate functions (roughly 80%+ similar) — merge them
- redundant type definitions — consolidate
- wrapper functions that add nothing — inline them
- pass-through re-exports — remove the indirection

## Step 6 — report

```
Dead Code Cleanup
──────────────────────────────
Deleted:   12 unused functions
           3 unused files
           5 unused dependencies
Skipped:   2 items (tests failed)
Saved:     ~450 lines removed
──────────────────────────────
All tests passing PASS:
```

## Rules

- Never delete before running the tests that establish a baseline.
- One deletion per step — atomic changes are easy to roll back.
- When in doubt, leave the code in place — dead code left behind is safer than production broken.
- This command removes code; it does not restructure what's left. Save reshaping the surviving
  code for a separate refactor pass.
