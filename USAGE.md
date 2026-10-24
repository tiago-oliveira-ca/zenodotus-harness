# Using Zenodotus

A practical operator's guide. For the philosophy and what's in the library, see `README.md`; for
licensing/provenance, `LICENSE` and `NOTICE.md`; for a dated, commit-referenced history of what changed,
`CHANGELOG.md`. This document is *how to actually use it day to day*.

---

## 1. What it is, in one paragraph

Zenodotus is a single, hand-owned Claude Code harness. Its heart is the **zeno loop** — every
non-trivial coding task runs **Scope → Route → Execution → Review**, tracked in one repo-root
`.zeno/` folder — a SAFe/Lean-governed backlog (`project.md` plus Epic/Feature/Story cards). Around
that sit method skills, a per-language standards library, documentation and graph tooling, and a
set of dev commands/agents. The ethos is **maximum discipline, fixed machinery**: one skill, one
command, one folder with a fixed layout — no agent fleets, no ad hoc phase directories.

The **source of truth** is the git repo at `<path-to-your-clone>`
(`github.com/tiago-oliveira-ca/zenodotus-harness`). The **installed copy** lives in `~/.claude`.
You edit the repo, then `./install.sh` to sync `~/.claude`.

---

## 2. Quick start

```sh
# install / update the harness into ~/.claude
cd <path-to-your-clone>
./install.sh
```
Then **restart Claude Code** (or `/clear`) so the SessionStart hook fires. You'll know it worked
when a new session behaves as below. That's it — there are no plugins to enable for Zenodotus.

**How a task flows** once it's installed — just describe the work:
> "Let's add rate-limiting to the login endpoint."

The loop engages automatically: it **Frames** the design with you, writes/updates `.zeno/`,
**Builds** through DDD→FDD→ATDD→BDD→TDD, and **Proves** the result before claiming done. You can
also drive it explicitly with `/zeno` (below).

---

## 3. The core: the zeno loop

Four gates, always on. Only genuinely trivial edits (typo, rename, one-line config) skip to Review.

| Gate | What happens | Method skill |
|---|---|---|
| **1. Scope** | Run the Architecture Council first (Lite: one card line when nothing architectural is in play; Full: answer blocking questions before options, or proceed with recorded assumptions when none block); agree the design before code; map the affected area; size the card — **smallest tier that fits, climbing only on named evidence** (ad hoc Story / Feature / Epic), tier + evidence recorded on the card; frame a Feature's domain (DDD); select the minimum sufficient specialist(s) from `agents/REGISTRY.md`; capture *Problem / Approach / Done looks like* | `zeno-council`, `zeno-insight`, `zeno-workflow/zeno-ddd` |
| **2. Route** | Create/update one repo-root `.zeno/` folder — `project.md` (state, goal, decisions, next step, proof) plus Epic/Feature/Story cards — and **fully plan the backlog before any coding**: a Feature's Story list, then every Story's acceptance criteria, scenarios, and Task breakdown | `zeno-workflow` (zeno-fdd/zeno-atdd/zeno-bdd) |
| **3. Execution** | A pure TDD implementation loop over the already-planned Task list; check a symbol's blast radius before editing it; diagnose bugs by root cause | `zeno-workflow/zeno-tdd`, `zeno-debug` |
| **4. Review** | Verify **goal-backward** (does it deliver *Done looks like*?), get an independent specialist pass for a registry-covered domain, exercise the real flow, record evidence, then you decide merge/PR/keep | `zeno-verify` + the matching `agents/REGISTRY.md` specialist |

### The `/zeno` command
| Command | Does |
|---|---|
| `/zeno start` | Begin a task: Scope → create `.zeno/` → stop at Execution for your go-ahead |
| `/zeno resume` | Pick a repo back up: prints Goal / State / Next step, re-enters at the right pipeline stage |
| `/zeno status` | Read-only snapshot of the Kanban board and active item |
| `/zeno review` | Jump to Review: exercise the change, record evidence, mark done |

### `.zeno/` — one folder, fixed layout
Lives at the **repo root**, committed with the code:

```
.zeno/
  project.md               # State / Goal / Decisions / Next step / Proof, + Kanban board
  docs/
    epics/EPIC-<slug>.md    # optional — epic-sized work only
    features/FEAT-<slug>.md # DDD notes + FDD Story list
    stories/STORY-<slug>.md # ATDD criteria + BDD scenarios + TDD proof
```

`project.md` is organized around five principles — **State**, **Goal**, **Decisions**, **Next step**,
**Proof** — governed as a SAFe/Lean backlog (Scrum + Kanban at team level), with a WIP limit of 1
item outside Backlog/Done. The SessionStart hook notes that it exists (no file text is injected) and `/zeno resume` reads it, so resume
is instant.

---

## 4. The method skills (they fire on their own, or invoke by name)

- **`zeno-council`** — the Architecture Council, first at Scope. Eight inline roles (Chief Architect,
  Business/Domain, Application, Data, Platform/Cloud, Security, SRE, Challenger) that question before
  they design. *Lite* when nothing architectural is in play; *Full* when the work adds a boundary, data
  store, integration, sensitive data, security posture or NFR (or is Feature/Epic tier): it asks up to 7
  questions per round (each with a recommended default). It stops for your answers only on *blocking*
  unknowns, meaning ones where a plausible answer would change which option wins or add a hard requirement
  (such as how card data is handled). Everything else becomes a recorded assumption with a revisit
  condition, so when you say the requirements are settled it goes straight to 2-3 options, a debate, and a
  recommendation with revisit triggers. *"which architecture", "monolith or microservices".*
- **`zeno-insight`** — the design gate. Explores context, asks the current frontier of clarifying
  questions one round at a time, weighs 2-3 approaches, gets your sign-off before code.
  *"let's design", "how should I approach".*
- **`zeno-workflow`** — the Execution-pipeline dispatcher, routing to five nested stages:
  - **`zeno-workflow/zeno-ddd`** — frames domain/architecture on the Feature card. *"bounded context",
    "what's the aggregate".*
  - **`zeno-workflow/zeno-fdd`** — decomposes a framed Feature into an ordered Story list (no plan files).
    *"break this down", "make a plan".*
  - **`zeno-workflow/zeno-atdd`** — writes business acceptance criteria per Story. *"acceptance criteria",
    "three amigos".*
  - **`zeno-workflow/zeno-bdd`** — translates each criterion into a Given/When/Then scenario. *"write the
    scenarios", "Gherkin".*
  - **`zeno-workflow/zeno-tdd`** — one red/green/refactor cycle per scenario; logs decisions; atomic
    commits. *"write a test", "TDD".*
- **`zeno-debug`** — root-cause-first debugging (no fix without investigation). *"why is this
  failing", "debug this".*
- **`zeno-verify`** — evidence-before-claims; goal-backward verification; stub check; finish menu.
  *"is it done", "verify", "prove it".*

You rarely name them — describing the work routes to the right one. The spine (`zeno`) orchestrates;
these own the methods.

---

## 5. Documenting code

- **`documenting-code`** skill — the discipline: generate docs from the source of truth, document
  only doc-worthy changes (API / architecture / dependency / setup), pick the right generator +
  docstring convention per stack, and defend against drift. Delivery documents (PRD/ADR/SAD) go to
  the `documentation` dispatcher instead.
- **`/docs-drift`** — on a diff, flags docs whose anchored code changed (stale) and changed public
  symbols with no docs (undocumented). `/docs-drift --fix` drafts updates as a reviewable diff.
- **`drift.lock`** (repo root) — binds doc sections to code symbols so drift is detectable. See
  `skills/documenting-code/references/drift-lock.md`.
- **PL/SQL** — JavaDoc `/** */` tags → Markdown via `ploc`/`plsql-md-doc`; see
  `references/plsql-docs.md`.

The Review gate runs a documentation check automatically **only** for doc-worthy changes.

---

## 6. Impact analysis (graph-assisted)

Before changing a shared/public symbol, the loop asks "who calls this / what's the blast radius?" —
using a **cheapest-first ladder**: `graphify query`/`path` *if a `graphify-out/` graph already
exists* → `docs/CODEMAPS/` → structural grep. It's **graph-assisted, never graph-required**; with no
graph it falls back to grep and costs nothing. See `skills/zeno/references/impact-analysis.md`.

- **`/graphify`** — build a queryable knowledge graph from code/docs/PDFs/etc. (needs the `graphifyy`
  tool: `uv tool install graphifyy` or `pip install graphifyy`). Then `graphify query "who calls X"`.
- **`/update-codemaps`** — token-lean architecture maps to `docs/CODEMAPS/`.

---

## 7. The rest of the library (routing)

`~/.claude/CLAUDE.md` is the arbitration doc — it maps each *lane* to a skill. Highlights:

- **Standards (how code is written):** the `code-standards` dispatcher routes by language/framework
  (Python, FastAPI, Go, Rust, Angular, Oracle/PL-SQL, R, Swift, RabbitMQ, Postgres…). Each carries a
  docstring standard too.
- **Delivery documents:** the `documentation` dispatcher (BRD → PRD → FRD → ADR → SAD).
- **Test specification docs:** the `testing` dispatcher. (Test *code* is `zeno-workflow/zeno-tdd` +
  `zeno-stack`'s `zeno-python-testing`/`zeno-react-testing`/`zeno-e2e-testing`/`zeno-browser-qa`.)
- **Stack/domain coverage:** `zeno-stack` — React, Python/FastAPI, Postgres, Redis, Docker, K8s,
  deployment, accessibility, security review, git/GitHub workflow, Jira backlog structure review, implementation guardrails — one `zeno-<name>` leaf each.
- **Diagrams:** `puml-diagrams`. **Architecture staging:** `software-architecture-progression`.
- **Harness upkeep:** `zeno-stack/zeno-config-gc`, `zeno-stack/zeno-context-budget`,
  `zeno-stack/zeno-skill-stocktake`, `zeno-stack/zeno-skill-comply`, `zeno-stack/zeno-find-skills`.
- **Dev commands** (22, all zeno-owned original content): `pr`, `quality-gate`, `python-review`,
  `react-review`/`react-build`/`react-test`, `fastapi-review`, `refactor-clean`, `test-coverage`,
  `build-fix`, `security-scan`, `update-docs`/`update-codemaps`, `harness-audit`, `checkpoint`,
  `save-session`/`resume-session`, `sessions`, `cost-report`, `model-route`, …
- **Dev agents** (24, all `zeno-` prefixed): bounded-domain specialists — reviewers/resolvers/
  analysts, plus 4 pipeline-stage guide agents (`zeno-ddd-guide`/`zeno-fdd-guide`/`zeno-atdd-guide`/
  `zeno-bdd-guide`, mirroring `zeno-tdd-guide`) — selected from **`agents/REGISTRY.md`** (minimum
  sufficient expertise at Scope, an independent pass at Review) or invoked directly by a matching
  command. Each has an explicit contract (`agents/_agent-template.md`): mission,
  non-responsibilities, tools, handoff rules, proof criteria. A few: `zeno-python-reviewer`,
  `zeno-typescript-reviewer`, `zeno-react-reviewer`,
  `zeno-security-reviewer`, `zeno-fastapi-reviewer`, `zeno-database-reviewer`, `zeno-doc-updater`,
  `zeno-refactor-cleaner`, `zeno-silent-failure-hunter`, …

Not sure what exists? Run **`zeno-stack/zeno-find-skills`**.

---

## 8. Maintaining Zenodotus

**The golden rule:** edit in the repo → `./install.sh` → `git push`. Both machines stay identical.

```sh
cd <path-to-your-clone>
# ...edit skills/agents/commands/CLAUDE.md...
./install.sh          # sync ~/.claude (backs up the old CLAUDE.md, re-registers the hook)
git add -A && git commit -m "..." && git push
```
After changing skills, **restart the session** — Claude Code caches the skill list at session start,
so edits (and especially additions/removals) only take effect in a fresh session.

**Adding a skill:** read `skills/_skill-template.md` first — it defines the shape (frontmatter with a
`Trigger on:` list under ~1000 chars; leaf skills carry `## Anti-pattern quick reference` + a closing
`## Pre-flight checklist`; discipline skills add an Iron Law + rationalization/red-flag tables).
Run `zeno-stack/zeno-find-skills` to avoid duplicating one. Nest tech skills under the matching dispatcher.

**Keep the inventory honest:** `CLAUDE.md`'s top table (skill/agent/command counts) is an invariant —
update it when you add or prune. `install.sh` prints the live counts and warns on drift.

---

## 9. Moving to another machine

```sh
git clone https://github.com/tiago-oliveira-ca/zenodotus-harness.git
cd Zenodotus
./install.sh
```
Then restart Claude Code. Optional dependencies (the core loop works without them):
- **Node/npm** — for `npx`-based skills (`ploc`, `madge`, some reviewers).
- **python3** — for the thread-aware SessionStart hook (it has a bash fallback, so not required).
- **`graphifyy`** — only if you want `/graphify` graph features.
- **Plugins/MCP** (context7, semgrep, playwright, obsidian…) are **not** in the repo — reinstall via
  the marketplace and set their `env` vars if you want them.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Edited a skill, no effect | Restart the session — the skill list is cached at session start |
| Session lists a skill you deleted | Stale session cache — restart; it reads from `~/.claude/skills` fresh |
| Hook errors at session start | Ensure `bash` works; `python3` is optional (bash fallback exists) |
| `/graphify` fails | Install the tool: `uv tool install graphifyy` (or `pip install graphifyy`) |
| A `zeno-stack` leaf's external tool is missing | Install Node (`npx`) or the named CLI; these aren't bundled |
| CLAUDE.md got overwritten | `install.sh` saved a `CLAUDE.md.bak-<timestamp>` in `~/.claude` |
| Counts look wrong | `ls ~/.claude/skills \| wc -l` and reconcile the `CLAUDE.md` inventory table |

---

## 11. One-line mental model

**Describe the work → the loop Frames it with you → it Builds test-first → it Proves the goal before
saying done → you decide the merge.** Everything else (standards, docs, graphs, reviewers) is a
helper the loop reaches for when the task calls for it.
