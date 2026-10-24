---
name: zeno-codebase-onboarding
description: >
  Analyze an unfamiliar codebase via reconnaissance (not full reads) and produce an
  onboarding guide plus a starter or enhanced CLAUDE.md — tech stack, architecture map,
  key entry points, conventions, and common tasks. Includes a greenfield gate: for a repo
  with no source yet, skip analysis and produce a minimal CLAUDE.md documenting what does
  NOT exist. Use when joining a new project, opening Claude Code in a repo for the first
  time, or asked to generate/update a project CLAUDE.md. Trigger on: "onboard me to this
  codebase", "help me understand this repo", "generate a CLAUDE.md", "create the CLAUDE.md"
  (including in an empty/greenfield repo), "walk me through this repo", "what's the
  architecture here", or first-time setup in an unfamiliar repository.
---

# Codebase Onboarding

Systematically reconnaissance an unfamiliar codebase — without reading every file — and
produce a scannable onboarding guide plus a starter or enhanced `CLAUDE.md`.

## When to use

- First time opening a project with Claude Code.
- Joining a new team or repository.
- "Help me understand this codebase", "onboard me", "walk me through this repo."
- Generating or updating a project's `CLAUDE.md`.

## Method

### Phase 0 — Greenfield gate

Before any analysis, check whether there is anything to analyze. If the repo has **no
source files and no package manifest** — only scaffolding like `.git/`, `.idea/`, a bare
README, or license files — the four phases below have no input: skip them entirely (no
plan-mode exploration, no reconnaissance fan-out) and produce a **minimal greenfield
CLAUDE.md** instead:

1. **State the repo's actual condition** — "this repository contains no source code yet" —
   so future sessions don't burn analysis effort rediscovering it.
2. **Document what does NOT exist, explicitly:** no build, test, lint, or run commands are
   defined yet, and none may be guessed or invented until code lands. Documenting the
   absence is high-value content — it is what prevents future hallucinated commands.
3. **Record durably any cross-repo or session-granted context** (an additional working
   directory pointing at design docs in a sibling repo, an agreed stack decision, a naming
   convention) — this is often the only real information a greenfield session holds, and it
   is recorded nowhere else.
4. **Instruct regeneration:** once source files exist, regenerate via `/init` or this
   skill's full four-phase flow, replacing the greenfield file.

An empty-input path that fabricates content or burns process overhead analyzing nothing is
the failure mode this gate exists to prevent.

### Phase 1 — Reconnaissance

Gather signals without reading every file. Use Glob/Grep, not blanket Read. Run these
checks (conceptually in parallel):

1. **Package manifest** — `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`,
   `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `mix.exs`, `pubspec.yaml`.
2. **Framework fingerprint** — `next.config.*`, `nuxt.config.*`, `angular.json`,
   `vite.config.*`, Django settings, Flask app factory, FastAPI `main`, Rails config.
3. **Entry points** — `main.*`, `index.*`, `app.*`, `server.*`, `cmd/`, `src/main/`.
4. **Directory structure** — top 2 levels, ignoring `node_modules`, `vendor`, `.git`,
   `dist`, `build`, `__pycache__`, `.next`.
5. **Config/tooling** — `.eslintrc*`, `.prettierrc*`, `tsconfig.json`, `Makefile`,
   `Dockerfile`, `docker-compose*`, `.github/workflows/`, `.env.example`, CI configs.
6. **Test structure** — `tests/`, `test/`, `__tests__/`, `*_test.go`, `*.spec.ts`,
   `*.test.js`, `pytest.ini`, `jest.config.*`, `vitest.config.*`.

### Phase 2 — Architecture mapping

From reconnaissance, identify: **tech stack** (languages/versions, frameworks, DB/ORM,
build tools, CI platform); **architecture pattern** (monolith, monorepo, microservices,
serverless; frontend/backend split or full-stack; REST/GraphQL/gRPC/tRPC); **key
directories** mapped to purpose; and **one traced request** — where it enters (router/
handler/controller), how it's validated (middleware/schemas/guards), where the business
logic lives (services/models/use cases), how it reaches the database (ORM/raw
queries/repositories).

### Phase 3 — Convention detection

Detect what the codebase already does, don't prescribe: file naming (kebab/camel/Pascal/
snake case), component/class naming, test file naming; error-handling style (try/catch,
Result types, error codes), DI vs direct imports, state-management approach, async
pattern (callbacks/promises/async-await/channels); and git conventions from recent branch
names and commit style — if history is absent or too shallow (e.g. a depth-1 clone), say
so explicitly rather than guessing.

### Phase 4 — Generate artifacts

**Onboarding Guide** (posted to the conversation): Overview (2-3 sentences), Tech Stack
table, Architecture description, Key Entry Points, Directory Map, Request Lifecycle,
Conventions, Common Tasks (dev/test/lint/migrate/build commands actually detected), and a
"Where to Look" table (task → path).

**Starter/enhanced `CLAUDE.md`** (written to the project root): Tech Stack summary, Code
Style (detected conventions), Testing (commands + coverage), Build & Run, Project
Structure, Conventions (commit style, PR workflow, error handling if detectable). If a
`CLAUDE.md` already exists, read it first, preserve its project-specific instructions, and
clearly mark what was added or changed rather than overwriting silently.

## Best practices

- Don't read everything — reconnaissance is Glob/Grep-driven; Read selectively only for
  genuinely ambiguous signals.
- Verify over guess — if config suggests one framework but the code uses another, trust
  the code.
- Respect an existing `CLAUDE.md` — enhance, don't replace; call out what's new.
- Stay scannable — the onboarding guide should read in under 2 minutes; details belong in
  the code.
- Flag unknowns — "could not determine test runner" beats a confident wrong answer.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Reading every file to build the guide | Glob/Grep reconnaissance; Read only ambiguous signals |
| Generating a 100+ line CLAUDE.md | Keep it focused on what shapes how code is written |
| Listing every dependency | Highlight only the ones that shape conventions |
| Explaining obvious directory names (`src/`) | Only annotate non-obvious structure |
| Overwriting an existing CLAUDE.md silently | Read first, preserve, mark additions/changes |
| Copying the README into the guide | Add structural insight the README doesn't have |
| Guessing git conventions from a shallow clone | State "git history unavailable" explicitly |
| Running full reconnaissance/analysis on an empty repo, or fabricating commands for it | Phase 0 greenfield gate: minimal CLAUDE.md that documents what does NOT exist and forbids guessing commands |

## Pre-flight checklist — run before delivering any onboarding guide or CLAUDE.md

- [ ] Reconnaissance used Glob/Grep, not a blanket read of every file
- [ ] Tech stack, architecture pattern, and one traced request are all captured
- [ ] Conventions are detected from actual code/history, not assumed from framework defaults
- [ ] Existing `CLAUDE.md` (if any) was read first and enhanced, not silently overwritten
- [ ] Onboarding guide is scannable in ~2 minutes and free of obvious/redundant detail
- [ ] Any undetectable convention is flagged as unknown rather than guessed
- [ ] Output matches the requested scope (full 4-phase, CLAUDE.md-only, or enhancement-only)
- [ ] Empty repo → Phase 0 taken: no analysis overhead, absences documented explicitly, session-granted context recorded, regeneration instruction included
