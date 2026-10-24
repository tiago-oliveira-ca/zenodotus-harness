---
name: business-requirements-standards
description: >
  Standards for Business Requirements Documents (BRD) based on BABOK, PMI, and ISO best
  practices. Use when capturing business intent, defining project scope, documenting
  stakeholders, or creating success criteria for any initiative. Trigger on: "write a BRD",
  "business requirements", "what are the requirements", "define project scope", "project
  objectives", "stakeholder analysis", "success criteria", "business case", or any document
  that establishes why a project exists and what business outcome it must achieve.
---

# Business Requirements Standards

Use this skill when creating or reviewing a BRD. The BRD should define business intent,
scope, success measures, and approval boundaries without drifting into technical design.

## Core Boundaries

- **BRD** answers why the initiative exists and what business outcome is required.
- **PRD / FSD** define product behavior in more detail.
- **TRD / SAD** define technical realization and constraints.

Do not let the BRD turn into architecture design or implementation planning.

## Required Inputs

- Business problem or opportunity
- Target outcomes and success metrics
- Stakeholders and decision-makers
- Scope boundaries and exclusions
- Risks, dependencies, and major assumptions

## Recommended BRD Structure

1. **Document Control**: version, authors, dates, status, approvals
2. **Executive Summary**: problem, objective, expected value
3. **Business Objectives**: SMART outcomes
4. **Scope**: in-scope and out-of-scope boundaries
5. **Stakeholders and Roles**
6. **Business Requirements**: uniquely identified needs
7. **Constraints, Assumptions, and Dependencies**
8. **Success Metrics and Acceptance Criteria**
9. **Traceability and References**

## Writing Rules

- Objectives should be SMART and outcome-oriented.
- Requirements should be uniquely identified and written clearly enough to trace forward.
- Avoid vague terms such as `improve`, `optimize`, or `user-friendly` unless paired with a
  measurable definition.
- Keep business language separate from technical design choices.

## Prioritization Guidance

Use an explicit prioritization method when the document is used for scope negotiation:

- MoSCoW for delivery prioritization
- Kano for feature value framing
- WSJF when economic sequencing is relevant

## SMART Objective Test

Every business objective should pass this test before inclusion:

| Letter | Check | Bad Example | Good Example |
|---|---|---|---|
| **S**pecific | Is the goal clearly defined? | "improve performance" | "reduce page load time" |
| **M**easurable | Can we prove success? | "more users" | "increase DAU by 20%" |
| **A**chievable | Is it realistic? | "eliminate all bugs" | "reduce P1 incidents by 50%" |
| **R**elevant | Does it align with business goals? | "add dark mode" | "increase mobile conversion" |
| **T**ime-bound | Does it have a deadline? | "eventually" | "by Q3 2026" |

## House IDs and traceability

Business requirements carry immortal `BR-NNN` IDs (grammar, linking rules, RTM format, and
the layer-proportionality table live in `../references/lifecycle.md` — read that section
before assigning IDs). The BRD is the root: it carries no upward trace; every PRD entry
below it declares `Trace: BR-NNN`.

## Review rules — good vs template-filled

- The document must justify the work with its solution section deleted: problem, user, and
  why-now come before any feature appears.
- Every success metric must be capable of failing — "improve engagement" cannot fail; "≥15%
  of failed-search buyers convert within 30 days, else the initiative is judged unsuccessful"
  can. A metric that would never trigger a rollback is decoration.
- Real constraints ("no new vendor this quarter") are recorded *as constraints*, labeled —
  never left for engineers to reverse-engineer from silence.
- Force the hardest question into the doc: require one "most likely way this fails" entry.
  Its absence is the surest template-fill tell.
- Acceptance is metric-based, not ship-based: the initiative is accepted when its metrics are
  live and trending, not merely when code ships.

## Worked exemplar (compact)

One fictional product (Lumen, a used-book marketplace) runs through BRD → PRD → FRD across
this skill family so the chain is visible end to end:

```markdown
# BRD — Buyer Re-engagement (Saved-Search Alerts initiative)
Control: v1.0 · Owner: Head of Marketplace · Status: Approved 2026-08-03

## Executive Summary
62% of buyers who search for an out-of-stock title never return. Sellers list ~900
books/day that would have matched a prior failed search. We lose the resale fee both times.

## Business Objectives (SMART)
- BR-001: Recover ≥15% of failed-search buyers into a completed purchase within 30 days of
  a matching listing, by end of Q4 2026. Baseline: 4% organic return (analytics, Jul 2026).
- BR-002: Increase listings sold within 7 days of posting from 31% to 40% by end of Q4 2026.

## Scope
In: automated buyer notification on matching supply; buyer notification controls.
Out: seller-side demand analytics (next initiative); price-drop alerts; ranking changes.

## Business Requirements
- BR-001 (Must): Buyers with unmet demand are brought back when matching supply appears,
  measured as failed-search→purchase conversion. Owner: Head of Marketplace.
- BR-003 (Should): Outbound notifications remain compliant with email consent regulation
  in all operating regions. Owner: Legal.

## Constraints, Assumptions, Dependencies
Constraint: no new notification vendor this quarter. Assumption (2026-08-01): ≥40% consent
grant rate when asked in context. Dependency: consent-management v2 ships before launch.

## Traceability
Downstream: PRD — Saved-Search Alerts (PRD-001..004). RTM: docs/requirements/rtm.md.
```

Note what makes it non-template: baselines with dates, an assumption that can be proven
wrong, an Out-list that kills repeat debates, and metric-gated acceptance.

## Anti-pattern quick reference

Catch these common BRD failures before they reach implementation:

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Solution masquerading as requirement | "The system shall use PostgreSQL" | State the need, not the design |
| Vague acceptance criteria | "The app shall be fast" | "P95 response time ≤ 200ms" |
| Missing exclusions | Scope grows uncontrolled | Explicitly list what is NOT in scope |
| No stakeholder sign-off | Unowned requirements | Assign owner and approval path per requirement |
| Single monolithic objective | Untestable, unranked | Break into discrete, prioritized requirements |
| Undated assumptions | Stale context | Date every assumption at capture |

## Review Workflow

1. Clarify the business problem and target outcome.
2. Separate business needs from implementation detail.
3. Validate scope boundaries and missing exclusions.
4. Confirm success metrics, acceptance criteria, and ownership.
5. Walk the document with sponsors before baseline approval.

## Pre-flight checklist — run before delivering any BRD

- [ ] Objectives are measurable and time-bound
- [ ] Scope and exclusions are both explicit
- [ ] Requirements can be traced to business outcomes
- [ ] Assumptions, dependencies, and risks are visible
- [ ] Approval and change-control expectations are clear
