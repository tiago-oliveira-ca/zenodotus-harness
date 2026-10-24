# Zenodotus

A single, hand-owned operating system for an AI coding agent — named for the first librarian of
Alexandria, because the job is the same: **keep the thread, so nothing is lost between sessions.**

Zenodotus began as a lean workflow drawing ideas from
[obra/superpowers](https://github.com/obra/superpowers) (process discipline as skills) and
[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) (persistent project state).
It has since become the **entire** harness: superpowers, GSD, and ECC were decommissioned and
their useful parts folded in, leaving **one library** built on one principle:

> **Maximum discipline, minimum machinery.** One always-on loop, near-zero moving parts.

**→ For how to actually use it day to day, see [USAGE.md](USAGE.md). For a history of what
changed and when, see [CHANGELOG.md](CHANGELOG.md).**

## The loop — four gates, always on

Every non-trivial task runs all four gates in order. Only genuinely trivial edits (a typo, a
rename, a one-line config) skip straight to Review.

| Gate | Fixes | Method skill |
|---|---|---|
| **1. Scope** | jumps to code too fast, or designs before the architecture questions are asked | `zeno-council` first — an Architecture Council that asks before it designs (Lite: one card line; Full: question rounds, options, debate, recommendation); then `zeno-insight` — design first, sign off before code; enumerates an Epic's Features and runs `zeno-workflow/zeno-ddd` (domain framing) for a Feature, before this gate closes |
| **2. Route** | loses the thread across sessions | one repo-root `.zeno/` folder — a SAFe/Lean backlog (`project.md`: state, goal, decisions, next step, proof; plus Epic/Feature/Story cards) — and fully plans it: `zeno-workflow/zeno-fdd` (Story list), then `zeno-atdd` (acceptance criteria) + `zeno-bdd` (scenarios) + a Task breakdown for **every** Story, before Gate 3 opens |
| **3. Execution** | — | a pure implementation loop: `zeno-workflow/zeno-tdd` (test-first: failing test → minimal code → refactor) over the already-planned Task list; `zeno-debug` — root-cause first when things break |
| **4. Review** | skips verification | `zeno-verify` — goal-backward evidence, stub-check, finish menu before "done" |

`zeno` owns the **structure** (the loop, the persistence, the gating). `zeno-council`, `zeno-insight`, the
`zeno-workflow` dispatcher, `zeno-debug`, and `zeno-verify` own the **methods**. Everything is
self-contained — no external plugin dependency.

## What's in the library

- **The zeno spine + methods** — `zeno`, `zeno-council`, `zeno-insight`, `zeno-workflow` (the DDD→FDD→ATDD→BDD→TDD
  planning-and-implementation dispatcher, split across gates: `zeno-ddd` in Gate 1; `zeno-fdd`,
  `zeno-atdd`, `zeno-bdd` in Gate 2; `zeno-tdd` alone in Gate 3), `zeno-debug`, `zeno-verify`.
- **`zeno-stack`** — the stack/domain-coverage dispatcher: React, Python/FastAPI, Postgres, Redis,
  Docker, K8s, deployment, testing execution, accessibility, security review, git/GitHub workflow, Jira backlog structure review, implementation guardrails,
  and the harness's own self-maintenance meta-skills. One `zeno-<name>` leaf per technology/domain
  — originally vendored (formerly ECC), now fully rewritten as original, zeno-owned content (see
  `CHANGELOG.md` for what changed).
- **Other dispatchers** — `code-standards`, `documentation`, `testing` (deeply nested sub-skills).
- **Standalones not yet folded into a dispatcher** — `puml-diagrams`, `software-architecture-progression`,
  `github-circleci-standards`, `graphify`, and `documenting-code`.
- **`documenting-code` + `/docs-drift`** — the discipline for documenting production code and keeping
  it accurate: source-of-truth generation, per-stack docstrings, and a `drift.lock` anchor convention
  that flags docs whose code changed. Wired into the zeno Review gate for doc-worthy changes.
- **24 agents** (all `zeno-<name>`) — 20 originally vendored (formerly ECC), now fully rewritten as
  original, zeno-owned content, same as `zeno-stack` (see `CHANGELOG.md`); plus 4 pipeline-stage
  guide agents (`zeno-ddd-guide`/`zeno-fdd-guide`/`zeno-atdd-guide`/`zeno-bdd-guide`, mirroring
  `zeno-tdd-guide`) that were never vendored — registry-selectable specialists for the same
  discipline `zeno-workflow`'s DDD/FDD/ATDD/BDD stages carry inline, for direct invocation or
  bulk/subagent delegation. Each is a bounded-domain specialist with an explicit contract (mission,
  non-responsibilities, tools, handoff rules, proof criteria — `agents/_agent-template.md`),
  selected via `agents/REGISTRY.md` at Scope (minimum sufficient expertise) and Review (an
  independent pass) rather than invoked ad hoc.
- **23 commands** (`zeno`, `docs-drift`, `skill-evals` + dev/session tooling) — originally vendored (formerly
  ECC), now fully rewritten as original, zeno-owned content, same as `zeno-stack` and the agents
  (see `CHANGELOG.md`). One formerly-vendored command, `project-init.md`, was discarded rather
  than rewritten — its multi-harness installer premise didn't map onto this repo's single-harness
  `install.sh` model.
- **2 hooks** — `zeno-session-start.sh`, a thread-aware SessionStart bootstrap that keeps the loop
  always-on and surfaces the active `.zeno/project.md` on resume; `zeno-cost-tracker.sh`, a Stop
  hook that appends each session's usage/cost to `~/.claude/metrics/costs.jsonl` for `/cost-report`.

```
Zenodotus/
  CLAUDE.md                    # the single-source arbitration document (installs to ~/.claude/CLAUDE.md)
  skills/    <top-level dirs + _skill-template.md — re-derive count with find, don't trust a stale number>
  agents/    <24 — all zeno-<name> (20 removed-and-rewritten + 4 never-vendored guide agents), plus REGISTRY.md + _agent-template.md>
  commands/  <23 — all removed and rewritten as original content; project-init.md discarded>
  hooks/     zeno-session-start.sh, zeno-cost-tracker.sh
  session-hook.fragment.json   # canonical SessionStart registration (merged by install.sh)
  cost-hook.fragment.json      # canonical Stop registration (merged by install.sh)
  install.sh                   # idempotent: mirrors into ~/.claude, self-wires both hooks, backs up CLAUDE.md
  LICENSE                      # MIT
  NOTICE.md                    # provenance: inspirations and removed third-party content
  README.md
  USAGE.md                     # day-to-day operator's guide
  CHANGELOG.md                 # dated, commit-referenced record of what changed, per delivery
```

This directory is the **source of truth / backup**. The live copies run from `~/.claude`
(copied, not symlinked, so an unmounted external drive never breaks the harness).

## Install / update

```sh
./install.sh
```

Idempotent. Copies `skills/`, `agents/`, `commands/`, `hooks/` (Claude-target `*.sh` only —
`hooks/codex/` belongs to `install-codex.sh`), and `CLAUDE.md` into `~/.claude` (copy-only, no
`--delete`, with a name-set drift warning naming any file that lingers after a source prune or
rename). It also self-wires both hooks — SessionStart and the Stop cost-tracker — idempotently
into `~/.claude/settings.json` via the two `*.fragment.json` files (never `settings.local.json`,
which Claude Code ignores at the global path).

### Codex CLI target

```sh
./install-codex.sh
```

A second, generated target for OpenAI's Codex CLI, installed into `~/.codex` — since Codex has no
per-file tool-scoped subagent primitive and deprecated its custom-prompt mechanism in favor of
Skills, `agents/` and `commands/` are folded into their domain-owning skill rather than mirrored
1:1 (mapping: `tools/codex/fold-map.toml`; generator: `tools/codex/build_codex.py`). `install.sh`
and the `~/.claude` target are untouched by this — `AGENTS.md` is Codex's own arbitration
document, parallel to `CLAUDE.md`. `./install-codex.sh --dry-run --out <dir>` previews the
generated tree without touching `$CODEX_HOME`. Hook registration is per-event: `SessionStart` is ported and registered
(`hooks/codex/zeno-session-start.sh`, verified against Codex 0.147.0; needs a one-time in-Codex
hook-trust approval), while `Stop` remains parked pending Codex usage quota to observe its real
payload (see `.zeno/docs/stories/STORY-codex-hooks-port.md`). A Gemini CLI
target is planned but not yet built.

## Using it

- `/zeno start` — begin a task: Scope (`zeno-council`, then `zeno-insight`) → create `.zeno/` → stop at Execution.
- `/zeno resume` — pick a repo back up: prints goal / state / next step, re-enters at the right gate.
- `/zeno status` — read-only snapshot of the thread.
- `/zeno review` — exercise the change, record evidence (`zeno-verify`), mark done.

Or just start working — the `zeno` skill auto-triggers on build/fix/change requests, and the
SessionStart hook reminds every new session of the loop.

## Principles

1. **Discipline is uniform; machinery is fixed, not free-form.** Ceremony ≠ discipline.
2. **The thread is one folder, one fixed layout.** If resume is expensive, the system failed.
3. **Done means observed.** A green typecheck is not proof; exercising the flow is.
4. **Own structure, own methods.** One self-contained library, no borrowed dependencies.
5. **Reversible over destructive.** Everything removed was archived first.
