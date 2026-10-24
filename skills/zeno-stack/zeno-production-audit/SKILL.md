---
name: zeno-production-audit
description: >
  Local-evidence production readiness audit — evaluates security/auth, data integrity,
  payments/webhooks, operations, and UX risk from repo state, CI, and (with permission) a
  deployed URL, without sending source or customer data to an external scanning service.
  Produces a ship/block score with named blockers and next actions. Use for "is this
  ready to ship" questions, pre-launch reviews, and post-merge risk passes. Trigger on:
  "is this production-ready", "what would break in prod", "audit this repo", "ready to
  ship", "pre-launch review", "post-merge risk check", "what did we miss before launch".
---

# Production Audit

Answer "is this ready to ship" with a scored, evidence-backed verdict — built entirely from
local and user-authorized evidence, never by uploading repo contents or calling an
unpinned external scanner.

**Production-readiness split** (CLAUDE.md lane row): this skill owns the pre-launch *judgement* — scoring whether a system is ready and naming what blocks launch. The *mechanics* it assesses (health checks, rollback strategy, deploy topology) are owned by `zeno-stack/zeno-deployment-patterns`; the *documents* that come out of readiness work (runbook, go-live checklist, postmortem) by `documentation/operations-standards`.

## When to use

- "Is this production-ready", "what would break in prod", "audit this repo", "ready to
  ship?"
- A feature just merged and needs a pre-deploy or post-merge risk pass.
- A public launch, demo, customer rollout, or investor walkthrough is imminent.
- CI is green but the ask is for production risk, not test status.

## When not to use

- Mid-implementation, where the right lens is line-level secure coding — use
  `zeno-security-review` instead.
- Pure libraries, templates, or docs-only repos, unless the ask is specifically packaging
  or release readiness.
- Formal compliance certification — this is engineering triage, not legal, financial,
  medical, or regulatory sign-off.
- When the only available evidence is a product idea with no repo, deployment, CI, or
  runtime surface to inspect.

## Method

Build the audit from local and user-authorized evidence only. Never run unpinned remote
code, upload repository contents to a third-party service, or invoke an external scanner
without the user explicitly approving that specific tool and data flow.

1. Establish the release surface (branch, deployed URL if any, PR in scope).
2. Read recent changes and current branch/CI state.
3. Inspect whichever risk boundaries actually exist in the repo — auth, data, payments,
   background jobs, AI/agent surfaces, deployment.
4. Check CI, tests, migrations, environment documentation, and rollback path.
5. Produce a scored ship/block recommendation with specific, named fixes.

### Evidence gathering

Cheap local signals first:

```bash
git status --short --branch
git log --oneline --decorate -20
git diff --stat origin/main...HEAD
```

Then the project-specific surface: package scripts, CI workflows, release scripts,
Dockerfiles/deployment manifests; API routes, webhooks, auth middleware, background
workers, cron jobs, migrations; env-var documentation and startup checks; observability
(error reporting, logs, health checks, dashboards); rollback/seed/backfill instructions;
E2E coverage for the paths that matter most.

If a deployed URL is in scope, use browser or HTTP checks against that URL only, and avoid
credentialed actions unless the user supplies a safe test account.

## Risk lenses

**Security and auth** — public/API/admin routes clearly separated; auth and authorization
enforced server-side; secrets kept out of client bundles, logs, and checked-in files; rate
limits, CSRF, CORS, and upload validation present where needed; any AI/agent surface
defended against prompt injection and untrusted content reaching privileged actions.

**Data integrity** — migrations run forward cleanly with a rollback/recovery plan;
destructive migrations, backfills, and imports staged safely; DB policies/grants match the
tenancy model; writes, jobs, and webhook handlers are idempotent under retry.

**Payments and webhooks** — signatures verified before parsing payload fields; every
payment/subscription/fulfillment webhook idempotent; replay, duplicate, and out-of-order
delivery handled; test-mode and live-mode credentials kept separate.

**Operations** — clean checkout starts from documented commands; required env vars are
named, validated, and fail fast; a health check proves dependencies are reachable;
deploy/rollback/incident-owner paths are documented; logs are useful without leaking
secrets or personal data.

**User experience** — launch-critical paths work on desktop and mobile; forms are usable
on mobile (no input-zoom, layout overlap, blocked submission); loading/empty/error/denied
states communicate what happened; there's a support or recovery path when a critical
operation fails.

## Scoring

Scores force prioritization — they are not a claim of mathematical certainty.

| Band | Score | Meaning |
|---|---|---|
| Blocked | 0-49 | Do not ship until the top risks are fixed |
| Risky | 50-69 | Ship only behind a small rollout or internal beta |
| Launchable with caveats | 70-84 | Ship if owners explicitly accept the listed risks |
| Strong | 85-100 | No obvious launch blockers from available evidence |

**Cap at 69** if any hold: auth missing on sensitive data; payment/fulfillment webhooks
not idempotent; required migrations can't run safely; secrets exposed in bundles/logs/
commits; no rollback path for a high-impact release.

**Cap at 84** if CI is not green, or the launch-critical path was not tested end to end.

## Output format

Lead with one sentence stating the score, band, and top risk:

```
Production audit: 76/100, launchable with caveats, with webhook idempotency and rollback
docs as the two risks to fix before public launch.
```

Then:
- **Blockers** — must-fix items before deploy.
- **High-value fixes** — next fixes to raise the score.
- **Evidence checked** — files, commands, CI, deployed URL, or PRs actually inspected.
- **Evidence missing** — what would raise confidence if supplied.
- **Next action** — one concrete fix or verification step, not a generic "let me know."

Keep strengths brief — the useful content is remaining risk and next action, not a
recap of what already works.

### Example

```
Production audit: 68/100, risky, because Stripe webhooks are verified but not idempotent
and there is no rollback note for the pending migration.

Blockers:
- Add idempotency for `checkout.session.completed` before fulfilling orders.
- Write and test the rollback path for `20260511_add_billing_state.sql`.

High-value fixes:
- Add a health check that verifies database and payment-provider reachability.
- Add one E2E path for upgrade, webhook fulfillment, and billing-page refresh.

Evidence checked:
- api/stripe/webhook.ts
- db/migrations/20260511_add_billing_state.sql
- GitHub Actions run for the release branch

Next action: Want me to patch webhook idempotency first?
```

## Related skills

`zeno-security-review` for line-level secure coding during implementation,
`zeno-deployment-patterns` for the deploy/rollback mechanics themselves, `zeno-e2e-testing`
for closing E2E coverage gaps this audit surfaces, `zeno-verify` for goal-backward proof
once fixes land.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Running `npx <package>@latest` or an unpinned remote scanner as the default path | Local/user-authorized evidence only; external tools require explicit per-tool approval |
| Uploading source, secrets, or customer data to an external audit service | Keep evidence gathering local; ask before any external data flow |
| Producing a score with no evidence list | Always name the files/commands/CI runs checked |
| Treating green CI as production readiness | CI green only removes the 84-point cap reason, it doesn't set the score |
| Ending with "let me know what you want to do" | End with one concrete next action |
| Auditing a docs-only repo as if it were a deployed app | Scope to packaging/release readiness instead, or decline |

## Pre-flight checklist — run before delivering any production audit

- [ ] Evidence gathering used only local/user-authorized sources — no unpinned remote execution
- [ ] All five risk lenses were considered for surfaces that actually exist in the repo
- [ ] Score respects the 69-cap and 84-cap trigger conditions where applicable
- [ ] Output leads with one sentence: score, band, top risk
- [ ] Blockers, high-value fixes, evidence checked, evidence missing, and next action are all present
- [ ] Next action is one concrete step, not a generic offer to help further
