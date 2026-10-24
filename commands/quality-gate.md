---
description: Run the project's formatter against a single file and report what would change (or apply it with --fix).
---

# Quality Gate Command

A standalone, on-demand formatter check for one file. Zenodotus has no PostToolUse formatting
hook — this command runs the same check by hand, in the same message, so a file's formatting can
be verified without waiting on CI.

## Usage

```text
/quality-gate <path> [--fix]
```

- `<path>` — required, the file to check.
- `--fix` — apply the formatter's fixes instead of a check-only diff.

## How it works

1. **Detect the formatter for the file's extension**, preferring whatever the project already has
   configured (a `biome.json`/`.prettierrc*` for JS/TS, `pyproject.toml`'s `[tool.ruff]` for
   Python, a `go.mod` for Go) over assuming a default:
   - `.ts`/`.tsx`/`.js`/`.jsx`/`.json`/`.md` — `biome check <path>` if `biome.json` exists,
     else `prettier --check <path>` (or `--write` with `--fix`).
   - `.go` — `gofmt -l <path>` (or `gofmt -w <path>` with `--fix`).
   - `.py` — `ruff format --check <path>` (or `ruff format <path>` with `--fix`).
   - Any other extension — report that no formatter is configured for it and stop; don't guess.
2. **Run it and report the real output** — the diff or the list of files that would change, not a
   paraphrase.
3. With `--fix`, apply the fix, then re-run the check-only form once to confirm it's now clean.

This command only formats — it doesn't lint or typecheck. For the full build/type/lint/test sweep
before closing out a change, use the Review-gate "Full-repo phase check" in `zeno-verify` instead;
this command exists for the narrower case of checking one file's formatting on demand.

## Related

- `zeno-verify` — the full Review-gate phase check (build, types, lint, tests, secret scan, diff review).
- `/build-fix`, `/python-review`, `/react-review` — for actual code-quality issues beyond formatting.

## Arguments

$ARGUMENTS:
- `<path>` — required, the file to check
- `--fix` — optional, apply fixes instead of reporting a diff
