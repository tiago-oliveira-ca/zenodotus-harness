# Specialist Registry

The routing table for `agents/` — the same role `code-standards/SKILL.md` and `zeno-stack/SKILL.md`
play for skills, applied to agents. This is the **one sanctioned way** to select a specialist:
bounded, table-driven selection, distinct from the "no agent fleet" ad hoc file/directory-sprawl
anti-pattern `skills/zeno/SKILL.md` warns against. That rule guards against scratch files and
second `.zeno/`-like structures; it was never a rule against invoking a bounded specialist.

See `agents/_agent-template.md` for the contract shape every row below implements.

## Selection

At the zeno **Scope** gate (`skills/zeno-insight/SKILL.md`), after the work is scoped and sized:
1. Identify which domain(s) the work actually touches (language, framework, review dimension).
2. Look up the matching row(s) below.
3. Select the **minimum sufficient** specialist(s) — not every agent whose domain is tangentially
   related. A one-file Python bugfix needs `zeno-python-reviewer`, not the whole reviewer roster.
4. Follow the Handoff column if the selected specialist's own boundary points elsewhere.

At the zeno **Review** gate (`skills/zeno-verify/SKILL.md`), the matching Advisor-tier reviewer(s)
provide an **independent** pass on the diff — a second opinion distinct from the same agent that
wrote the code self-reviewing. This does not change who approves: the human is still the sole
merge/PR/keep authority, per `zeno-verify`'s "never self-merge" Iron Law. No row in this registry
carries `Authority` tier — see "Why no Authority tier" below.

**What Advisor "read-only" covers:** repository and working-tree state, not just
files. Withholding `Write`/`Edit` is not sufficient on its own — the eight Advisors that hold
`Bash` (database-reviewer, fastapi-reviewer, pr-test-analyzer, python-reviewer, react-reviewer,
security-reviewer, silent-failure-hunter, typescript-reviewer) could otherwise switch branches or
stash through the shell, and a reviewer spawned at Review runs against a branch that usually has
uncommitted work on it (this happened: a reviewer subagent switched the caller's working directory
to `main` and stashed its in-flight work). Each of those agents now states the observation-only
limit in its `Constraints` field, and `_agent-template.md` requires it of any new Advisor. Running
the suite, linters, and `git diff`/`log`/`status` remains expected. Spawning an Advisor against a
dirty tree? Prefer `isolation: "worktree"`.

## Registry

| Domain | Specialist | Tier | Primary hand-off |
|---|---|---|---|
| General Python review (PEP 8, idiom, security, perf) | `zeno-python-reviewer` | Advisor | FastAPI-specific → `zeno-fastapi-reviewer` |
| FastAPI-specific review (async, DI, Pydantic, OpenAPI) | `zeno-fastapi-reviewer` | Advisor | General Python style → `zeno-python-reviewer` |
| General TS/JS review (types, async, Node security) | `zeno-typescript-reviewer` | Advisor | React-specific → `zeno-react-reviewer` |
| React/JSX review (hooks, RSC, a11y, render perf) | `zeno-react-reviewer` | Advisor | Non-React TS → `zeno-typescript-reviewer` |
| PostgreSQL query/schema/security review | `zeno-database-reviewer` | Advisor | Cross-layer profiling → `zeno-performance-optimizer` |
| Project-wide OWASP/secrets/injection audit | `zeno-security-reviewer` | Advisor | React-specific security stays with `zeno-react-reviewer` |
| WCAG 2.2 design-time accessibility, Web + Native | `zeno-a11y-architect` | Owner | React implementation depth → `zeno-stack/zeno-accessibility` |
| General TS/build error → green, minimal diffs | `zeno-build-error-resolver` | Owner | React/JSX/bundler → `zeno-react-build-resolver`; dead code → `zeno-refactor-cleaner`; new feature → `zeno-planner`; failing tests → `zeno-tdd-guide`; security → `zeno-security-reviewer`; architecture → `zeno-council` |
| React/JSX/bundler/hydration build failures | `zeno-react-build-resolver` | Owner | Post-fix quality → `zeno-react-reviewer` |
| Dead-code/duplication removal, verified | `zeno-refactor-cleaner` | Owner | (hand-off target, not source) |
| Cross-layer profiling-driven optimization | `zeno-performance-optimizer` | Owner | Deep SQL/indexing → `zeno-database-reviewer`; React render specifics → `zeno-react-reviewer` |
| Test-first (red/green/refactor) enforcement | `zeno-tdd-guide` | Owner | Framework mocking depth → `zeno-stack/zeno-python-testing` / `zeno-stack/zeno-react-testing` |
| Domain framing for a Feature (Bounded Context, subdomain, aggregates) before Story decomposition | `zeno-ddd-guide` | Owner | Story-list decomposition → `zeno-fdd-guide` |
| Feature → ordered, independently-verifiable Story list | `zeno-fdd-guide` | Owner | Domain framing → `zeno-ddd-guide`; Story Acceptance Criteria → `zeno-atdd-guide` |
| Story → collaborative, testable Acceptance Criteria (Example Mapping) | `zeno-atdd-guide` | Owner | Story pulling/sizing → `zeno-fdd-guide`; scenario translation → `zeno-bdd-guide` |
| Acceptance Criteria → Given/When/Then scenario(s) | `zeno-bdd-guide` | Owner | Criteria not yet written → `zeno-atdd-guide`; scenario implementation → `zeno-tdd-guide` |
| Browser-level E2E execution + flake management | `zeno-e2e-runner` | Owner | Config/POM depth → `zeno-stack/zeno-e2e-testing` |
| Doc/codemap reconciliation (Review-gate only) | `zeno-doc-updater` | Owner | (already wired — the one long-standing sanctioned exception) |
| Harness/config tuning (not product code) | `zeno-harness-optimizer` | Owner | Product-code fixes → hand back, out of scope |
| Feature/refactor → file-level implementation plan | `zeno-planner` | Advisor | (hand-off target, not source) |
| Post-hoc PR test-coverage review | `zeno-pr-test-analyzer` | Advisor | Execution-time test-first policy → `zeno-tdd-guide` |
| Inline comment accuracy/rot audit | `zeno-comment-analyzer` | Advisor | External docs → `zeno-doc-updater` |
| Swallowed-error/bad-fallback detection | `zeno-silent-failure-hunter` | Advisor | (deep-dive target for reviewers' error-handling sections) |
| Type/data-model invariant design quality | `zeno-type-design-analyzer` | Advisor | Surface type-safety lint stays with the language reviewers |

## Maturity tiers

- **Advisor** — read-only tools (`Read`/`Grep`/`Glob`[/`Bash`]), no `Write`/`Edit`. Recommends;
  never touches code. 11 of 24 agents.
- **Owner** — has `Write`/`Edit`, scope bounded by an explicit Constraints statement in its own
  file. Executes within its stated domain. 13 of 24 agents.
- **Authority** — deliberately unused. See below.

### Why no Authority tier

A specialist architecture commonly includes a 4th tier that can unilaterally approve or reject
work. Zenodotus doesn't grant it to any agent: `zeno-verify`'s Review gate has a pre-existing,
deliberate Iron Law — the human always makes the final merge/PR/keep call, never the agent. Adding
an Authority tier would contradict that constraint rather than extend it. Independent review
(a specialist's opinion distinct from the builder's self-review) still happens at Review — it just
feeds the human's decision instead of replacing it.

## Known adjacent-domain overlaps (resolved, not merged)

Eight overlap clusters were found by content (not name) when this registry was built — evidence
and the resolution applied to each pair are recorded in `CHANGELOG.md` ("Specialist agent
architecture formalized").
None were merge-worthy: each pair operates at a genuinely different altitude (design-time vs.
review-time) or timing (execution-time vs. review-time) once traced through actual file content. Two
were already cleanly negotiated before this registry existed (`zeno-react-reviewer` ↔
`zeno-typescript-reviewer`; `zeno-build-error-resolver` ↔ `zeno-react-build-resolver`) — those are
the model the other six now follow.

## Agent ↔ skill twins (arbitration)

Five agents share a domain with a same-purpose `zeno-stack` leaf that was authored as their Codex
fold home (`tools/codex/fold-map.toml`): `zeno-build-error-resolver` ↔ `zeno-build-resolver`,
`zeno-comment-analyzer` ↔ `zeno-comment-analysis`, `zeno-harness-optimizer` ↔
`zeno-harness-optimizer` (same name), `zeno-planner` ↔ `zeno-planning`, `zeno-refactor-cleaner` ↔
`zeno-refactor-cleanup`. The rule, stated reciprocally in all ten files: **load the
skill for inline work in the main thread; spawn the agent for a standalone, dedicated pass.**
`zeno-security-reviewer` ↔ `zeno-security-review` and `zeno-e2e-runner` ↔ `zeno-e2e-testing`
follow the same pattern with the agent additionally citing the skill as its depth source.
