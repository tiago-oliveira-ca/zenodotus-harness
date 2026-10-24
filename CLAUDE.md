# Global Claude Code configuration — Zenodotus

> **Reference configuration.** This is the author's own arbitration document, published as a working
> example. `install.sh` copies it over `~/.claude/CLAUDE.md` (the old file is backed up first). Before
> installing, adapt the **Plugins** section and the plugin row of the inventory to your own setup; the
> plugin names and counts below describe the author's machine, not a requirement.

This file is the **single arbitration document** for the harness. The skill/agent/command
library is one hand-owned system, **Zenodotus**: source of truth at
`<path-to-your-clone>`, installed into `~/.claude` (`./install.sh`, copy-only; `--target all` also installs the Codex target; `install.ps1` on Windows).
Every skill, agent, and command is zeno-owned original content — no vendored or unattributed
third-party content remains anywhere in the repo, and every de-vendoring pass is fully resolved
(nothing outstanding; the one sanctioned external dependency is `graphify`'s wrapped `graphifyy`
PyPI engine, attributed in that skill and NOTICE.md). When two components could handle the same request, the rules here decide —
not recency, not description-match strength, not which skill "feels" closer. Provenance and the
decommission history (superpowers/GSD/ECC) are summarized in `NOTICE.md`; the rollback
snapshot path is below in Config maintenance.

## Inventory

| Location | Count | Notes |
|---|---|---|
| `~/.claude/skills/` | re-derive via `find` | top-level dirs + `_skill-template.md` |
| `~/.claude/agents/` | 24 | + `_agent-template.md` and `REGISTRY.md` (reference files, not agents) |
| `~/.claude/commands/` | 23 | |
| `~/.claude/hooks/` | 2 | `zeno-session-start.sh` (SessionStart), `zeno-cost-tracker.sh` (Stop) |
| plugins | re-derive via `claude plugin list` | the author runs about 25; enable state is app-held and drifts — don't trust a hand-typed split |

Top-level `skills/` roles: the `zeno` spine + 4 flat method skills (`zeno-council`, `zeno-insight`,
`zeno-debug`, `zeno-verify`); the `zeno-workflow` and `zeno-stack` dispatchers (nested leaves not counted at top
level); the `code-standards`, `documentation`, `testing` dispatchers; and the standalone skills
(`documenting-code`, `puml-diagrams`, `software-architecture-progression`,
`github-circleci-standards`, `graphify`). Re-derive the exact count with
`find ~/.claude/skills -maxdepth 1 -mindepth 1 -type d ! -name '.*' | wc -l` rather than trusting
a hand-typed number. Keep this table's *shape* accurate — a stale claim mis-routes work silently.

---

## Precedence: one loop, one library

The model is single-source. Resolution order for any non-trivial coding task:

1. **`zeno` governs the lifecycle.** Every non-trivial task runs the always-on loop
   **Scope → Route → Execution → Review**, tracked in one repo-root `.zeno/` folder — a SAFe/Lean
   backlog (`project.md` + Epic/Feature/Story cards). Invoke the `zeno` skill (or `/zeno`) at the
   start of any build/fix/change, before writing code. Only genuinely trivial edits (typo, rename,
   one-line config) skip to Review.
2. **The zeno method skills supply the gates' methods** — `zeno-council` (Scope step 0: the
   Architecture Council, always first — Lite for work with no architecture impact, Full otherwise;
   questions before any architecture is proposed), `zeno-insight` (Scope / design; also runs
   Gate 1's DDD framing via `zeno-workflow/zeno-ddd` and Epic→Features enumeration), the
   `zeno-workflow` dispatcher (the DDD→FDD→ATDD→BDD→TDD pipeline, now split across gates: Gate 2
   fully plans a Feature's Story list and every Story's Acceptance Criteria/Scenarios/Task
   breakdown via `zeno-workflow/zeno-fdd` + `zeno-workflow/zeno-atdd` + `zeno-workflow/zeno-bdd`
   before Gate 3 opens; Gate 3 loops `zeno-workflow/zeno-tdd` over the already-planned Task list),
   `zeno-debug` (root-cause-first debugging), `zeno-verify` (Review / goal-backward evidence).
3. **Custom dispatchers govern the artifact** — once the approach is set, *what gets written*
   comes from `code-standards/`, `documentation/`, `testing/`, and the standalone skills.
4. **`zeno-stack` fills stack/production coverage** — React, Docker, K8s, Redis, testing execution,
   security, deployment, etc. — one zeno-owned leaf per technology/domain, routed the same way
   `code-standards` routes for code-writing standards. One owner per technology: Python and
   FastAPI live solely in `code-standards` (test code stays with `zeno-stack`'s testing leaves).
   Only Postgres keeps leaves
   in both — `code-standards` owns schema/SQL standards and wins on those, `zeno-postgres-patterns`
   owns operational diagnosis, with reciprocal cross-references. React splits between
   `typescript-code-standards` (Angular-flavored TS) and the `zeno-react-*` leaves. Angular
   splits the same way: TS/code style → `typescript-code-standards` (`frameworks/angular.md`);
   framework API, version features, and tooling → `zeno-stack/zeno-angular-developer` —
   reciprocal cross-references in both.

These compose; they don't compete. "Let's build X" → `zeno`: **Gate 1**, `zeno-council` → `zeno-insight` (Scope) +
`zeno-workflow/zeno-ddd` + `code-standards/*` (DDD) → **Gate 2**, `zeno-workflow/zeno-fdd` +
`zeno-workflow/zeno-atdd` + `zeno-workflow/zeno-bdd` (FDD/ATDD/BDD, planning every Story fully
before any coding starts) → **Gate 3**, the relevant `zeno-stack/*` leaf + `zeno-workflow/zeno-tdd`
looping the already-planned Task list → **Gate 4**, `zeno-verify` (Review) — all recorded in
`.zeno/`.

---

## Lane ownership

**Each lane maps to a Zenodotus skill.** A lane owner wins even if another skill has a
closer-matching name.

| Lane | Owner |
|---|---|
| Process / methods | `zeno-council` · `zeno-insight` · `zeno-workflow` (zeno-ddd/zeno-fdd/zeno-atdd/zeno-bdd/zeno-tdd) · `zeno-debug` · `zeno-verify` |
| Project lifecycle | `zeno` (Scope → Route → Execution → Review) |
| Delivery documents (BRD → PRD → FRD/NFR → TRD → SAB → SAD → ADR) | `documentation` |
| Documenting production code (docstrings / API ref / README / drift) | `documenting-code` (+ `/docs-drift`) |
| How code is written, per technology | `code-standards` |
| Test **specification documents** | `testing` |
| Test **code** and execution | `zeno-stack/zeno-python-testing`, `zeno-stack/zeno-react-testing`, `zeno-stack/zeno-e2e-testing`, `zeno-stack/zeno-browser-qa` |
| Stack/production coverage beyond code style | `zeno-stack`'s leaves |
| Diagrams | `puml-diagrams` |
| Jira backlog structure review (Epic/Story/Task/Bug/Sub-task hierarchy; review and propose, structural changes need approval) | `zeno-stack/zeno-jira-structure-review` |
| Execution tripwires (new service/DB/broker, destructive migration, breaking API change, conflicting sources of truth) | `zeno-stack/zeno-implementation-guardrails` (decisions → `zeno-council`) |
| Context compaction and session handoff (what to keep, compress, drop; Task-State summary) | `zeno-stack/zeno-context-compaction` |
| CI/CD pipelines | `github-circleci-standards` (CircleCI — the house CI standard) · `zeno-stack/zeno-deployment-patterns` (GitHub Actions mechanics, plus strategy/rollback/readiness on any platform) |
| Production readiness | `zeno-stack/zeno-production-audit` (the pre-launch *judgement* — is this ready?) · `zeno-stack/zeno-deployment-patterns` (the *mechanics* — health checks, rollback strategy, deploy topology) · `documentation/operations-standards` (the *documents* — runbook, go-live checklist, postmortem) |
| Design tokens | `zeno-stack/zeno-design-system` (token architecture) · `documentation/developer-handoff-standards` (handoff packaging) · `zeno-stack/zeno-frontend-design` (visual direction) · `code-standards/typescript-code-standards/ui-style` (this house's Angular SCSS `--mac-*` values) |
| Architecture staging (which style, when) | `software-architecture-progression` |
| Skill discovery | `zeno-stack/zeno-find-skills` (local), `zeno-stack/zeno-skill-scout` (external) |
| Harness self-maintenance | `zeno-stack/zeno-config-gc`, `zeno-stack/zeno-context-budget`, `zeno-stack/zeno-skill-stocktake`, `zeno-stack/zeno-skill-comply`, `zeno-stack/zeno-security-scan`, `zeno-stack/zeno-harness-optimizer` (measure → smallest change → re-measure loop over `/harness-audit`) |
| Specialist agent selection (invoked from Scope + Review) | `agents/REGISTRY.md` (contract shape: `agents/_agent-template.md`) |

The `testing` split trips people up: the `testing` dispatcher owns test **documents** (its
sub-skill is `software-test-specification`); writing actual test **code** belongs to the
testing-execution skills above. Complementary, not competing.

Dispatchers (`code-standards/`, `documentation/`, `testing/`, `zeno-stack/`) each carry a routing
table in their `SKILL.md`. Load the dispatcher first, then follow its table into the specific
leaf (some nest three levels deep) before generating or reviewing anything.

### Creating new skills

**The canonical process — frontmatter rules, dispatcher-vs-leaf shape, enforcement sections,
description ceiling — lives in `~/.claude/skills/_skill-template.md`. Read it before creating or
restructuring any skill.** Two placement rules worth repeating: nest new technology/artifact
skills under the matching dispatcher (top-level only when no dispatcher fits), and every
zeno-family skill's name starts with `zeno-`. Check `zeno-stack/zeno-find-skills` for overlap
first, `zeno-stack/zeno-skill-scout` before adopting anything external; new skills go through the
`zeno` loop like any other work.

---

## Plugins

Plugins update through Claude Code's plugin/marketplace mechanism. **Don't normalize their
skills/agents into the Zenodotus structure, and don't hand-edit their files** — local edits are
lost on update. Routing facts that matter:

- **context7** owns library/framework docs. Prefer it over web search *and* over training recall
  for any library API question.
- **semgrep** owns SAST/secrets/supply-chain. `/security-review` must call its MCP tools rather
  than rely on manual reading.
- **Name ownership:** `code-review` owns `/code-review`; `feature-dev` owns the
  `code-architect` / `code-explorer` / `code-reviewer` agents; `code-simplifier` owns that agent
  name. Never recreate these locally.
- **playwright vs `claude-in-chrome` MCP** — Playwright for scripted E2E, claude-in-chrome for
  interactive inspection of a live page.
- **obsidian-second-brain** requires `OBSIDIAN_VAULT_PATH` in the `env` block (see invariant 3).
  Vault: wherever your Obsidian vault lives.
- **Disabled locally** — one toggle from returning. The author disables `frontend-design` because the
  Zenodotus skill owns that name, plus plugins that overlap other lanes. Decide yours the same way:
  disable any plugin whose skill name collides with a Zenodotus skill (invariant 2).

**Overlap resolutions:** inside the zeno loop `zeno-council` owns architecture questioning and
recommendation — it wins over the `engineering:architecture` / `engineering:system-design` plugin
skills, and consults `software-architecture-progression` for the staging model; `code-standards` is authoritative for languages it routes
(`qodo-get-rules` supplements for gaps, alongside not instead); `simplify` for inline cleanup in
the current conversation vs the `code-simplifier` agent for larger standalone passes;
`find-skills` for the local library vs `skill-scout` before adopting anything external.

---

## graphify

`~/.claude/skills/graphify/SKILL.md` — any input to knowledge graph. When the user types
`/graphify`, use the installed graphify skill before doing anything else. The zeno loop consults
`graphify` (when a `graphify-out/` graph exists) and `/update-codemaps` for impact/blast-radius
analysis at Scope and Execution — **read-only queries, never a required build step**; with no
graph it falls back to codemaps then grep. See `skills/zeno/references/impact-analysis.md`.

---

## Skill-invocation discipline

Never batch a `Skill` invocation speculatively into a parallel tool block alongside unrelated
calls. Loading a skill is cheap to issue but unboundedly expensive to receive, and the context
cost is irreversible once paid — it is a deliberate, task-scoped decision made *before* a
batch, not an opportunistic addition to one. If you cannot state in one sentence why the skill
applies to the task at hand, do not invoke it. The same discipline applies to redundant work more
broadly: before re-searching, re-reading a file, or re-invoking an agent for information already
surfaced earlier in this conversation, check what's already there first — every repeat pays the
same irreversible context cost as a speculative skill load.

---

## Config maintenance

The harness maintains itself with `zeno-stack`'s meta-skills:

| Need | Use |
|---|---|
| "my config is bloated", "too many skills" | `zeno-stack/zeno-config-gc` (human-in-the-loop, confirm each) |
| token overhead per component | `zeno-stack/zeno-context-budget` |
| actual dollar spend, by day/model/week | `/cost-report` |
| which model tier fits a task (shape × risk × budget) | `/model-route` |
| quality audit of skills/commands | `zeno-stack/zeno-skill-stocktake` |
| are the rules actually *followed*? | `zeno-stack/zeno-skill-comply` |
| cross-cutting principles that should become a `CLAUDE.md` rule | `zeno-stack/zeno-rules-distill` |
| checklist-based harness scorecard | `/harness-audit` |
| iterate on the scorecard (measure → smallest change → re-measure) | `zeno-stack/zeno-harness-optimizer` (skill inline; agent of the same name for a dedicated pass) |
| reduce permission prompts | `fewer-permission-prompts` (built-in) |

**Invariants to preserve.** Check on any bulk install or prune:

1. **Plugin enable-state is not in a tracked `~/.claude` file** — `installed_plugins.json` lists
   what's installed; the enabled/disabled split is app-held. Re-confirm via `/plugin`.
2. No name appears in both `~/.claude/{skills,agents,commands}/` and an **enabled** plugin
   (`comm -12` the two name sets).
3. **Enabled ≠ configured.** Marketplace install doesn't run a plugin's `setup.sh` — for each
   enabled plugin, check declared MCP `env` vars are actually set.
4. **No vendored skills, agents, or commands.** No vendored or unattributed third-party content
   remains anywhere in the repo (provenance in `NOTICE.md`). No unreviewed bulk file-copy
   of plugin content in `~/.claude/`, ever.
5. `<path-to-your-clone>` is the **source of truth**; `~/.claude` is the
   installed copy. Real backups are a dated snapshot kept outside the repo — a mirror is not a backup.
6. The inventory table at the top of this file matches reality.
