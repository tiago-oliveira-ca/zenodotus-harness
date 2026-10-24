---
name: operations-standards
description: >
  Standards for runbooks, incident response, postmortems, and operational readiness. Use
  when writing or reviewing how a system is operated, supported, or recovered in production.
  Trigger on: "write a runbook", "runbook", "incident response", "postmortem", "post-incident
  review", "on-call", "SLO", "SLA", "error budget", "operational readiness", "go-live
  checklist", "production support", "escalation path", "rollback procedure", or any document
  defining how to operate, support, monitor, or recover a system once it's live.
---

# Operations Standards

Use this skill when creating or reviewing a runbook, incident response procedure, or
postmortem. These documents close the lifecycle loop — they turn what happens in production
back into input for the next design revision, rather than living only in an engineer's head.

**Production-readiness split** (CLAUDE.md lane row): this skill owns the *documents* — runbooks, go-live checklists, postmortems. Judging launch readiness is `zeno-stack/zeno-production-audit`; the deployment *mechanics* those documents describe (health checks, rollback strategy, topology) are owned by `zeno-stack/zeno-deployment-patterns`.

## Core Boundaries

- **Runbook**: How to operate, deploy, monitor, and recover a *specific* system —
  step-by-step, meant to be followed during an incident by someone who isn't its author.
- **Postmortem**: A retrospective analysis of an incident that already happened — what
  broke, why, and what changes result. Not a runbook, and not a blame record.
- **ADR**: Captures why an architectural decision was made. A runbook executes against the
  architecture; it doesn't re-argue it.
- **SAD / Blueprint**: Defines system structure. A runbook references it, never redefines it
  — if the runbook and the SAD disagree about topology, the SAD is stale and needs updating
  first (see Change Management in `../references/lifecycle.md`).

## Required Inputs

- System/component boundaries and ownership (from the SAD)
- Known failure modes and critical dependencies
- SLO/SLA and RTO/RPO targets (from the NFR)
- Escalation contacts, on-call rotation, and ownership
- Existing monitoring/alerting definitions

## Recommended Runbook Structure

1. **Document Control**: version, authors, dates, status, review cadence
2. **Service Overview & Ownership**: what it does, who owns it
3. **Architecture Summary**: link to the SAD — don't repeat it
4. **Dependencies & Failure Modes**: what this depends on, how each dependency fails
5. **Monitoring & Alerting**: every alert that can fire, and what it means
6. **Standard Operating Procedures**: routine tasks — deploy, scale, restart, rotate secrets
7. **Incident Response Procedures**: step-by-step response per known failure mode
8. **Escalation Path**: who's on call, secondary, and when to escalate further
9. **Rollback / Recovery Procedures**: how to restore service, and to what RTO/RPO
10. **Appendices**: dashboard links, log queries, related ADRs

## Recommended Postmortem Structure (Blameless)

1. **Incident Summary**: what happened, customer/business impact, duration
2. **Timeline**: detection through resolution, with timestamps
3. **Root Cause**: the actual mechanism, not just the symptom
4. **Contributing Factors**: what made this possible or worse than it needed to be
5. **What Went Well / What Went Poorly**
6. **Action Items**: owner + due date for each, fed back through Change Management if any
   imply an architecture or ADR change
7. **Lessons for the Runbook or Architecture**: what should change so this class of incident
   is faster to detect or recover from next time

## Writing Rules

- Every runbook step must be executable by someone unfamiliar with the system during an
  active incident — no tribal knowledge assumed, no "you'll know it when you see it."
- Every alert referenced anywhere must state what it means and the first action to take.
- Postmortems are blameless: describe systems and processes that allowed the failure, never
  individuals.
- Every postmortem action item needs an owner and a due date — an action item with neither is
  a wish, not a commitment.
- SLOs and error budgets are versioned and reviewed on a cadence (see Documentation
  Governance in `../references/lifecycle.md`), not set once at launch and forgotten.

## Runbook Readiness Test

Every runbook should pass this test before it's trusted during an incident:

| Check | Bad Example | Good Example |
|---|---|---|
| **Executable without the author** | "Restart the service" | "Run `systemctl restart order-svc` on host X; verify recovery via `/health` returning 200" |
| **Alert has a defined first action** | Alert fires with no accompanying note | "`OrderQueueAgeHigh` → check consumer lag via `kubectl logs ...`; escalate to secondary after 15 min" |
| **Escalation path is explicit** | "Ping the team" | Named on-call rotation, secondary, and manager escalation after N minutes |
| **Tied to an SLO/RTO** | No target stated | "Restore service within the RTO of 4h per NFR-012" |

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Runbook written once at launch, never updated | Drifts from reality, fails exactly when needed most | Review on the same cadence as the SAD it references |
| Tribal knowledge in one person's head | Bus factor of one; incidents stall when they're unavailable | Runbook must be independently executable by any on-call engineer |
| Blame-focused postmortem | Suppresses honest reporting, hides the real root cause | Blameless format — focus on systems and process, not people |
| Action items with no owner | Nothing gets fixed | Require an owner and due date, tracked like any other work item |
| Alerts with no corresponding runbook entry | On-call improvises mid-incident | Every alert must map to a documented procedure |
| Postmortem findings never reach the SAD/ADR | Same incident class recurs | Route architecture-relevant lessons through Change Management |

## Review Workflow

1. Confirm the runbook matches the *current* SAD — not a prior, since-changed architecture.
2. Walk every alert and confirm it maps to a documented first action.
3. Confirm escalation paths and on-call ownership are current, not stale contacts.
4. For postmortems: confirm timeline accuracy, root-cause depth (not just the symptom), and
   that every action item has an owner and due date.
5. Confirm any learning that implies an architecture change is routed through Change
   Management (`../references/lifecycle.md`) rather than fixed silently in code.

## Pre-flight checklist — run before delivering any runbook or operational document

- [ ] Runbook covers standard operations and every known incident response procedure
- [ ] Every alert maps to a documented first action
- [ ] Escalation path and on-call ownership are explicit and current
- [ ] SLO/RTO/RPO targets are referenced from the NFR, not invented ad hoc
- [ ] Postmortems are blameless and every action item has an owner and due date
- [ ] Document control, version, and review cadence match the governance model
- [ ] Learnings that imply an architecture change are routed through Change Management
