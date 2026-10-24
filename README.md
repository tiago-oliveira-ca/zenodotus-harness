# Zenodotus

A single, hand-owned operating system for an AI coding agent — named for the first librarian of
Alexandria, because the job is the same: **keep the thread, so nothing is lost between sessions.**

It is one library of skills, agents and commands, installed into **Claude Code** (`~/.claude`) and
**Codex CLI** (`~/.codex`) from the same source, on **macOS, Linux and Windows**. Its heart is an
always-on loop, **Scope → Route → Execution → Review**, tracked in one fixed `.zeno/` folder per repo.

> **Maximum discipline, minimum machinery.** One loop, near-zero moving parts.

**Where to go next:** [USAGE.md](USAGE.md) for day-to-day use · [CHANGELOG.md](CHANGELOG.md) for what changed ·
[CONTRIBUTING.md](CONTRIBUTING.md) to change it · [SECURITY.md](SECURITY.md) to report a problem.

## Quick start

```sh
git clone <this repo> && cd <the clone>
./install.sh                    # Claude Code (default)
./install.sh --target codex     # Codex CLI
./install.sh --target all       # both
```

On Windows, run the same thing from PowerShell: `.\install.ps1 --target all` (details below). Then restart
Claude Code or Codex so the SessionStart hook fires, and describe any piece of work. The loop engages by itself.

## Requirements

| | macOS | Linux | Windows |
|---|---|---|---|
| Shell | bash (built in) | bash | **Git for Windows** (provides Git Bash) — or WSL |
| Python | 3.8+ (`brew install python`) | 3.8+ | 3.8+ from python.org, on `PATH` |
| Codex target | Python **3.11+** | Python **3.11+** | Python **3.11+** |
| Entry point | `./install.sh` | `./install.sh` | `.\install.ps1` or `./install.sh` in Git Bash |

`git` is needed for the loop itself. Python is used by the installers and by the hooks; the SessionStart hook
falls back to a static payload without it, and the cost tracker becomes a no-op. The Microsoft Store `python3`
alias does not count: the installers execute every candidate and skip stubs.

## Install / update

```sh
./install.sh [--target claude|codex|all] [-- <extra args for install-codex.sh>]
```

- **`--target claude`** (default): copies `skills/`, `agents/`, `commands/` and the Claude-target `hooks/*.sh`
  into `~/.claude` (override with `CLAUDE_HOME`), installs `CLAUDE.md` (saving `CLAUDE.md.bak-<timestamp>`
  first if it differs), and registers the SessionStart and Stop hooks in `settings.json` through the two
  `*.fragment.json` files. Copy-only, idempotent, with a name-set drift warning for files that linger after a prune.
- **`--target codex`**: generates a Codex tree with `tools/codex/build_codex.py`, since Codex has no per-file
  subagent primitive and deprecated custom prompts. `agents/` and `commands/` are folded into the skill that owns
  them (`tools/codex/fold-map.toml`). Installs into `~/.codex` (override with `CODEX_HOME`), replaces only the
  skills it manages (tracked in a manifest) and leaves Codex's own `.system` and your own skills alone, and
  registers the SessionStart hook in `hooks.json` (Codex asks once to trust a new hook). The Stop hook is
  parked until its payload can be observed. Preview without installing:
  `./install.sh --target codex -- --dry-run --out <scratch-dir>`.
- **`--target all`**: both.

### Windows

`install.ps1` does not reimplement the installer. It finds Git Bash (skipping the WSL launcher in `System32`)
and runs `install.sh` with your arguments, so the platforms cannot drift apart. Claude Code's hooks need bash on
Windows anyway, which is why Git for Windows is a requirement.

- Windows blocks unsigned scripts by default. If `.\install.ps1` is refused, run
  `powershell -ExecutionPolicy Bypass -File .\install.ps1 --target all` (or `./install.sh` from Git Bash).
- Without Git Bash it stops and tells you to install Git for Windows.
- WSL works too (`./install.sh` inside WSL), but that installs into the **WSL** home, not your Windows profile.
- `.gitattributes` forces LF endings on shell scripts so a Windows checkout does not break `bash install.sh`.
- Codex on native Windows is the least-tested path: hook registration is written with a Windows-style path
  and needs the one-time trust approval inside Codex.

## The loop — four gates, always on

Every non-trivial task runs all four gates in order. Only genuinely trivial edits (a typo, a rename, a one-line
config) skip straight to Review.

| Gate | Fixes | Method skill |
|---|---|---|
| **1. Scope** | jumps to code too fast, or designs before the architecture questions are asked | `zeno-council` first — an Architecture Council (Lite: one card line; Full: blocking questions, options, debate, recommendation); then `zeno-insight` (design first, sign-off before code), plus `zeno-workflow/zeno-ddd` for a Feature's domain |
| **2. Route** | loses the thread across sessions | one repo-root `.zeno/` folder (`project.md` + Epic/Feature/Story cards) and a **fully planned backlog**: `zeno-fdd` (Story list), then `zeno-atdd` + `zeno-bdd` + a Task breakdown for every Story, before Gate 3 opens |
| **3. Execution** | — | a pure implementation loop: `zeno-workflow/zeno-tdd` (failing test → minimal code → refactor) over the planned Tasks; `zeno-debug` when things break; `zeno-stack/zeno-implementation-guardrails` stops architecture- or data-destructive steps |
| **4. Review** | skips verification | `zeno-verify` — goal-backward evidence, stub check, finish menu before "done" |

`zeno` owns the structure (loop, persistence, gating). The method skills own the methods.
`CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) are the arbitration documents that decide which skill wins
when two could handle a request.

## What's in the library

- **The zeno spine and methods** — `zeno`, `zeno-council`, `zeno-insight`, `zeno-workflow` (DDD → FDD → ATDD → BDD →
  TDD across gates), `zeno-debug`, `zeno-verify`.
- **`zeno-stack`** — 48 leaves, one per technology or domain: React, Postgres, Redis, Docker, Kubernetes, deployment,
  testing execution, accessibility, security review, git and GitHub workflow, Jira backlog structure review,
  implementation guardrails, context compaction, and the harness's own maintenance skills.
- **Other dispatchers** — `code-standards` (per-language), `documentation` (BRD → PRD → … → ADR), `testing`
  (test specification documents).
- **Standalone skills** — `puml-diagrams`, `software-architecture-progression`, `github-circleci-standards`,
  `graphify`, `documenting-code` (+ `/docs-drift`).
- **24 agents** — bounded-domain specialists with explicit contracts, selected through `agents/REGISTRY.md` at
  Scope and Review.
- **23 commands** — `/zeno`, `/docs-drift`, `/skill-evals`, plus dev and session tooling.
- **Hooks** — `zeno-session-start.sh` keeps the loop always-on and notes when a `.zeno/` thread exists
  (it injects no file text); `zeno-cost-tracker.sh` (Claude Code only) logs session cost to
  `~/.claude/metrics/costs.jsonl` for `/cost-report`.

## Using it

- `/zeno start` — begin a task: Scope → create `.zeno/` → stop at Execution.
- `/zeno resume` — pick a repo back up: prints goal / state / next step.
- `/zeno status` — read-only snapshot. `/zeno review` — exercise the change, record evidence, mark done.

Or just start working: the `zeno` skill triggers on build, fix and change requests.

`.zeno/` is working memory. Commit it to keep the backlog with your code, or add it to `.gitignore` to keep it
local (this repository does the latter).

## Repository layout

```
CLAUDE.md                  arbitration document for Claude Code (installs to ~/.claude/CLAUDE.md)
AGENTS.md                  arbitration document for Codex (installs to ~/.codex/AGENTS.md)
skills/  agents/  commands/  hooks/        the library; hooks/codex/ holds the Codex SessionStart hook
session-hook.fragment.json  cost-hook.fragment.json    canonical hook registrations merged by install.sh
install.sh                 the installer (macOS, Linux, WSL, Git Bash); --target claude|codex|all
install.ps1                Windows launcher: finds Git Bash and runs install.sh
install-codex.sh           the Codex engine install.sh calls (also runnable directly)
tools/install-common.sh    shared OS and Python detection
tools/codex/               Codex generator, fold map and tests
tools/test_install.sh      end-to-end installer test (both targets, idempotence)
tools/check_skills.py      skill frontmatter lint
tools/github-settings.sh   applies the repository's GitHub settings and rulesets with `gh` (idempotent)
docs/                      architecture and loop diagrams (PlantUML + SVG), proposals
README.md  USAGE.md  CHANGELOG.md  CONTRIBUTING.md  SECURITY.md  CODE_OF_CONDUCT.md  LICENSE
.github/                   CI, CodeQL, Dependabot, CODEOWNERS, issue and pull request templates
```

The repository is the source of truth. The installed copies are plain copies, not symlinks, so moving or deleting
your clone never breaks a running harness.

## Checks

```sh
bash -n install.sh install-codex.sh hooks/*.sh hooks/codex/*.sh
python3 tools/check_skills.py
python3 -m unittest discover -s tools/codex -p 'test_build_codex.py'
bash tools/codex/test_install_codex.sh
bash tools/test_install.sh
```

CI runs these on Ubuntu, macOS and Windows.

## Principles

1. **Discipline is uniform; machinery is fixed, not free-form.** Ceremony is not discipline.
2. **The thread is one folder, one fixed layout.** If resume is expensive, the system failed.
3. **Done means observed.** A green typecheck is not proof; exercising the flow is.
4. **Own structure, own methods.** One self-contained library, no borrowed dependencies.
5. **Reversible over destructive.** Removals are recorded, never silent.
