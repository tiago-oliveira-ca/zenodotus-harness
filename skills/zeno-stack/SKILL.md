---
name: zeno-stack
description: >
  Stack-and-domain coverage dispatcher for the zeno loop. Routes to the correct
  infra/tooling/domain leaf for the technology in use; how code is written per language
  belongs to `code-standards`. Use whenever a task needs React, Postgres
  operations, Redis, Docker, Kubernetes, deployment (cloud or self-hosted),
  testing-execution, accessibility, security review, git workflow, or harness-maintenance
  guidance. Trigger on: any mention of React, Next.js, Angular, Postgres, Redis, Docker,
  Kubernetes, Playwright, pytest, accessibility/a11y, API design, error handling, rate limiting,
  security review, git branching, GitHub PR/issue automation, Jira backlog structure, destructive migrations, /compact, design systems, motion/animation,
  codebase onboarding, or Claude Code harness maintenance (skill audits, context budget, config
  cleanup). Also routes build-error resolution, comment-rot audits, performance profiling,
  implementation planning, dead-code cleanup, cost reporting, and model-tier routing.
---

# Zeno Stack Dispatcher — stack & domain coverage

When a task needs stack-specific or cross-cutting domain guidance, identify the technology/domain
and load the matching nested leaf below before writing or reviewing anything. Every leaf here
starts with `zeno-`, per the zeno-family naming rule.

## Routing Table

| Technology / Domain | Leaf to load |
|---|---|
| React component/state/hook patterns | `zeno-react-patterns/SKILL.md` |
| React/Next.js performance (memoization, code splitting, bundle size) | `zeno-react-performance/SKILL.md` |
| React component testing (RTL, Vitest/Jest) | `zeno-react-testing/SKILL.md` |
| Accessibility (WCAG 2.2, cross-platform + React/Next.js implementation) | `zeno-accessibility/SKILL.md` |
| Angular | `zeno-angular-developer/SKILL.md` |
| Design tokens / design-system audits | `zeno-design-system/SKILL.md` |
| Building actual UI with deliberate visual design | `zeno-frontend-design/SKILL.md` |
| Animation / motion patterns | `zeno-motion-ui/SKILL.md` |
| REST API design (resources, status codes, pagination, versioning) | `zeno-api-design/SKILL.md` |
| Error handling (typed errors, retries, circuit breakers) | `zeno-error-handling/SKILL.md` |
| Python idioms, PEP 8, type hints | `code-standards/python` — route there |
| FastAPI | `code-standards/python/frameworks/fastapi.md` — route there |
| Python testing (pytest, fixtures, mocking) | `zeno-python-testing/SKILL.md` |
| Redis (caching, distributed locks, **rate limiting — the one source of truth**) | `zeno-redis-patterns/SKILL.md` |
| PostgreSQL / relational data modeling | `zeno-postgres-patterns/SKILL.md` |
| Schema/data migrations | `zeno-database-migrations/SKILL.md` |
| Docker / Compose | `zeno-docker-patterns/SKILL.md` |
| Kubernetes | `zeno-kubernetes-patterns/SKILL.md` |
| Deployment / CI-CD / rollback strategy | `zeno-deployment-patterns/SKILL.md` |
| Self-hosted / home-lab deployment topology (NAT'd targets, single-host Compose) | `zeno-self-hosted-deployment/SKILL.md` |
| End-to-end testing (Playwright specs, CI) | `zeno-e2e-testing/SKILL.md` |
| Live/interactive browser QA | `zeno-browser-qa/SKILL.md` |
| Application security review (SQLi, XSS, CSRF, secrets, auth) | `zeno-security-review/SKILL.md` |
| Claude Code harness/config security scan | `zeno-security-scan/SKILL.md` |
| Git branching, commits, merge/rebase | `zeno-git-workflow/SKILL.md` |
| GitHub issue/PR/release automation | `zeno-github-ops/SKILL.md` |
| Jira backlog hierarchy review (Epic/Story/Task/Bug/Sub-task structure) | `zeno-jira-structure-review/SKILL.md` |
| Execution tripwires: new service/DB/broker/dependency, destructive migration, breaking API change, conflicting sources | `zeno-implementation-guardrails/SKILL.md` |
| Compacting or handing off a long session (keep/compress/drop, Task-State summary) | `zeno-context-compaction/SKILL.md` |
| Pre-launch / post-merge production readiness audit | `zeno-production-audit/SKILL.md` |
| Multi-source web research | `zeno-deep-research/SKILL.md` |
| Onboarding to an unfamiliar codebase | `zeno-codebase-onboarding/SKILL.md` |
| Guided code walkthroughs (CodeTour) | `zeno-code-tour/SKILL.md` |
| Harness skill-library cleanup | `zeno-config-gc/SKILL.md` |
| Harness context/token-cost audit | `zeno-context-budget/SKILL.md` |
| Skill quality audit (keep/improve/retire/merge) | `zeno-skill-stocktake/SKILL.md` |
| Skill/rule compliance visualization | `zeno-skill-comply/SKILL.md` |
| Cross-skill rule extraction | `zeno-rules-distill/SKILL.md` |
| Per-response token-depth selection | `zeno-token-budget-advisor/SKILL.md` |
| Local skill-library discovery | `zeno-find-skills/SKILL.md` |
| External (marketplace/GitHub) skill discovery | `zeno-skill-scout/SKILL.md` |
| TS/build error resolution + formatter gate | `zeno-build-resolver/SKILL.md` |
| Inline comment accuracy/rot audit | `zeno-comment-analysis/SKILL.md` |
| Harness reliability/cost/throughput tuning | `zeno-harness-optimizer/SKILL.md` |
| Cross-layer, profiling-driven performance work | `zeno-performance-profiling/SKILL.md` |
| File-level implementation planning | `zeno-planning/SKILL.md` |
| Dead-code/duplication cleanup | `zeno-refactor-cleanup/SKILL.md` |
| Local cost-tracking report | `zeno-cost-report/SKILL.md` |
| Model-tier recommendation | `/model-route` command owns the heuristic; `zeno-model-route/SKILL.md` is a thin router (and the Codex fold home) |
| Session save/resume/list/alias (repos with no tracked `.zeno/`) | `zeno-sessions/SKILL.md` |

## Instructions

1. Identify the technology or domain from the request or the codebase's existing imports/config.
2. Load and apply **only** the matching leaf above. Each carries its own complete standards and
   both required enforcement sections (Anti-pattern quick reference, Pre-flight checklist) — this
   dispatcher holds routing only.
3. If multiple technologies are in scope (e.g. a FastAPI backend + React frontend), apply each
   relevant leaf to its own layer.
4. For rate limiting specifically, always defer to `zeno-redis-patterns` — it is the single source
   of truth; no other leaf should carry its own rate-limiter implementation.
5. For local-vs-external skill discovery, `zeno-find-skills` covers what's already installed;
   `zeno-skill-scout` covers marketplace/GitHub search and itself delegates local search to
   `zeno-find-skills` rather than duplicating it.
6. If the technology isn't listed above, apply general clean-code/SOLID principles and say so —
   don't force-fit an unrelated leaf.
