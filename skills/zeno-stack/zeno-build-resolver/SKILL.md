---
name: zeno-build-resolver
description: >
  Take a red TypeScript/JS build back to green with the smallest change the compiler/bundler
  actually demands — no architectural edits, no drive-by cleanup. Covers type errors,
  compile/transpilation failures, dependency/import errors, and tsconfig/webpack/Next.js config
  errors; React/JSX/bundler/hydration failures belong to the `zeno-react-build-resolver` agent
  (via `/react-build`) instead. Also
  covers the formatter-gate step (run the project's formatter, report or apply what changes).
  Trigger on: "build is failing", "type error", "tsc error", "fix the build", "build won't
  compile", "quality gate", "run the formatter", "implicitly has any type", "cannot find module".
---

# Build & Formatter Gate

When a build is red or a typecheck fails, get it back to green with the narrowest correct
change — never a chance to tidy up whatever file you happen to be in.

## Diagnose first

Run these before touching any file — the full error list, not just the first error:

```bash
npx tsc --noEmit --pretty
npm run build
npx eslint . --ext .ts,.tsx,.js,.jsx
```

Read every error message in full — the line/column and "expected vs actual" phrasing usually says
exactly what's wrong; guessing from the error name alone leads to fixes that miss the real cause.

## Working loop

1. **Inventory** — collect the complete error list, group by cause (missing types, bad imports,
   config drift, dependency mismatch), order by what's actually blocking the build.
2. **Fix one error at a time** — narrowest correct fix (an annotation, a null guard, an import
   path correction), then re-run `tsc` before moving to the next. Fixing several blind and
   re-checking once makes it hard to tell which change caused a new failure.
3. **Confirm no regressions** — a shrinking error count is good; a shifted or growing one means
   the last edit needs reconsidering, not layering over.

## Fix reference

| Error | Fix |
|-------|-----|
| `implicitly has 'any' type` | Add an explicit type annotation |
| `Object is possibly 'undefined'` | Optional chaining `?.` or an explicit guard |
| `Property does not exist` | Add the field to the interface, or mark it optional |
| `Cannot find module` | Check `tsconfig` path mappings, install the missing package, or correct the import |
| `Type 'X' not assignable to 'Y'` | Convert/parse the value, or correct the declared type |
| Generic constraint violation | Add `extends { ... }` to narrow the generic |
| `'await' outside async` | Mark the enclosing function `async` |

## In scope vs. out of scope

In scope: type annotations, null/undefined guards, import/export fixes, a genuinely missing
dependency, config actively causing the failure. Out of scope, even if tempting: refactoring code
the error didn't touch, renaming things unrelated to the cause, style/perf opinions. If a change
is justified by "this is better practice" rather than "this is what the error requires," stop —
that's a different task (`zeno-refactor-cleanup` or the Scope gate, not this).

## Escape hatches

When incremental fixes aren't converging, rule out cache/dependency corruption before assuming
the error is real:

```bash
rm -rf .next node_modules/.cache && npm run build
rm -rf node_modules && npm ci   # keeps the lockfile's pinned versions; never delete package-lock.json
npx eslint . --fix
```

## Formatter gate

Before handing a diff to Review, run the project's configured formatter against changed files and
report what it would change (or apply it directly when asked to `--fix`) — a build that compiles
but fails the project's own formatting check isn't actually green.

## Definition of done

`npx tsc --noEmit` exits 0; `npm run build` completes; the error count only decreased, never
shifted or grew; the diff is small relative to the file(s) touched; existing tests still pass.

**Agent counterpart:** `agents/zeno-build-error-resolver.md` — the spawned standalone pass over this same discipline (and this skill is its Codex fold home). Load this skill for inline fixes; spawn the agent for a dedicated build-fix run.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Fixing several errors blind, re-checking once at the end | Fix one, re-run `tsc`, then move to the next |
| "While I'm here" cleanup bundled into a build fix | Every change traceable to a specific error message; route cleanup to `zeno-refactor-cleanup` |
| Reaching for a rewrite when the cache is just stale | Try the escape hatches (cache clear, clean reinstall) first |
| Calling it done because `tsc` exits 0 | Also confirm the formatter gate and the existing test suite |
| A React/JSX/hydration failure fixed here | Hand off to the `zeno-react-build-resolver` agent (`/react-build`) — it owns that depth |

## Pre-flight checklist — run before delivering any build fix

- [ ] Full error list collected and grouped before the first edit, not fixed error-by-error blind.
- [ ] Every change traceable to a specific compiler/bundler/lint error message.
- [ ] `tsc`/`build` re-run after each fix; the error count only ever shrank.
- [ ] Diff is small relative to the files touched — no drive-by cleanup or renames.
- [ ] Formatter gate run (reported or applied) before handing off.
- [ ] Existing tests still pass.
