---
description: Scan project structure and generate token-lean architecture codemaps.
---

# /update-codemaps

Scans the codebase's structure and writes (or refreshes) a set of token-lean architecture codemaps.

## Step 1 — scan the project structure

1. Identify the project shape (monorepo, single app, library, microservice).
2. Locate the source directories (`src/`, `lib/`, `app/`, `packages/`).
3. Map the entry points (`main.ts`, `index.ts`, `app.py`, `main.go`, etc.).

## Step 2 — generate the codemaps

Write or update these under `docs/CODEMAPS/` — the single canonical location; the zeno loop's
impact analysis (`skills/zeno/references/impact-analysis.md`) reads only this path:

| File | Contents |
|------|----------|
| `architecture.md` | High-level system diagram, service boundaries, data flow |
| `backend.md` | API routes, middleware chain, service → repository mapping |
| `frontend.md` | Page tree, component hierarchy, state management flow |
| `data.md` | Database tables, relationships, migration history |
| `dependencies.md` | External services, third-party integrations, shared libraries |

### Codemap format

Optimize each codemap for AI context consumption — token-lean, not prose-heavy:

```markdown
# Backend Architecture

## Routes
POST /api/users → UserController.create → UserService.create → UserRepo.insert
GET  /api/users/:id → UserController.get → UserService.findById → UserRepo.findById

## Key Files
src/services/user.ts (business logic, 120 lines)
src/repos/user.ts (database access, 80 lines)

## Dependencies
- PostgreSQL (primary data store)
- Redis (session cache, rate limiting)
- Stripe (payment processing)
```

## Step 3 — check the diff before overwriting

1. If codemaps already exist, compute how much the new scan differs from them.
2. Above a 30% diff, show the diff and get approval before overwriting.
3. At or below 30%, update in place.

## Step 4 — stamp freshness metadata

Add a header to each codemap recording when and how it was generated:

```markdown
<!-- Generated: 2026-02-11 | Files scanned: 142 | Token estimate: ~800 -->
```

## Step 5 — write the analysis report

Save a summary to `.reports/codemap-diff.txt` covering:
- files added/removed/modified since the last scan
- new dependencies detected
- architecture changes (new routes, new services, etc.)
- staleness warnings for docs untouched for 90+ days

## Notes

- Optimize for **high-level structure**, not implementation detail
- Prefer **file paths and signatures** over pasting full code blocks
- Keep each codemap under roughly **1000 tokens** so it loads cheaply into context
- Use ASCII diagrams for data flow rather than long prose descriptions
- Re-run this after major feature work or a refactoring pass
