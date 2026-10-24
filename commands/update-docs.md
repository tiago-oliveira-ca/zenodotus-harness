---
description: Sync documentation from source-of-truth files such as scripts, schemas, routes, and exports.
---

# /update-docs

Regenerates documentation from the files that are the actual source of truth for it, and flags what's gone stale.

## Step 1 — identify the sources of truth

| Source | Generates |
|--------|-----------|
| `package.json` scripts | Available commands reference |
| `.env.example` | Environment variable documentation |
| `openapi.yaml` / route files | API endpoint reference |
| Source code exports | Public API documentation |
| `Dockerfile` / `docker-compose.yml` | Infrastructure setup docs |

## Step 2 — generate the script reference

1. Read `package.json` (or `Makefile`, `Cargo.toml`, `pyproject.toml`, whichever applies).
2. Pull every script/command out along with its description.
3. Write it up as a table:

```markdown
| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Production build with type checking |
| `npm test` | Run test suite with coverage |
```

## Step 3 — generate the environment reference

1. Read `.env.example` (or `.env.template`, `.env.sample`).
2. Pull out every variable and what it's for.
3. Mark each required vs. optional.
4. Document the expected format and valid values.

```markdown
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgres://user:pass@host:5432/db` |
| `LOG_LEVEL` | No | Logging verbosity (default: info) | `debug`, `info`, `warn`, `error` |
```

## Step 4 — refresh the contributing guide

Update `docs/CONTRIBUTING.md` if it exists (if absent, report it as missing rather than
creating it — see Rules), covering:
- dev environment setup (prerequisites, install steps)
- available scripts and what they're for
- how to run and write tests
- code style enforcement (linter, formatter, pre-commit hooks)
- PR submission checklist

## Step 5 — refresh the runbook

Update `docs/RUNBOOK.md` if it exists (if absent, report it as missing rather than creating
it; runbook *structure* is owned by `documentation/operations-standards` — follow it when the
user does ask for one), covering:
- deployment procedure, step by step
- health check endpoints and monitoring
- common issues and their fixes
- rollback procedure
- alerting and escalation paths

## Step 6 — check for staleness

1. Find doc files untouched for 90+ days.
2. Cross-reference against recent source changes.
3. Flag anything that's likely gone stale for a human to review.

## Step 7 — summarize what changed

```
Documentation Update
──────────────────────────────
Updated:  docs/CONTRIBUTING.md (scripts table)
Updated:  docs/ENV.md (3 new variables)
Flagged:  docs/DEPLOY.md (142 days stale)
Skipped:  docs/API.md (no changes detected)
──────────────────────────────
```

## Rules

- **Generate from code, not by hand** — the source file is always the source of truth; never hand-edit a generated section directly.
- **Leave hand-written prose alone** — only touch the generated sections.
- **Mark what's generated** — wrap generated sections in `<!-- AUTO-GENERATED -->` markers.
- **Don't create files unprompted** — only start a new doc file if explicitly asked to; when a
  step above targets a file that doesn't exist, list it under "missing" in the report instead.
- **Lane boundaries** — README/API-reference/docstring drift discipline is owned by the
  `documenting-code` skill (`/docs-drift` for detection); delivery documents (runbooks, BRD→ADR)
  are owned by the `documentation` dispatcher. This command syncs from source-of-truth files; it
  doesn't replace either lane.
