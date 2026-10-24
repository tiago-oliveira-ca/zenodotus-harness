---
name: product-requirements-standards
description: >
  Standards for Product Requirements Documents (PRD). Use when defining product vision,
  target users, user stories, prioritized features, or success metrics for a product or
  major feature area. Trigger on: "write a PRD", "product requirements", "product
  requirements document", "user personas", "user stories", "product vision", "feature
  prioritization", "non-goals", "what should the product do", or any document that
  translates business intent into what the product will deliver for users.
---

# Product Requirements Standards

Use this skill when creating or reviewing a PRD. The PRD should turn business intent into
product vision, target users, and prioritized features — without dropping into the detailed
system behavior or technical requirements that come next in the lifecycle.

## Core Boundaries

- **BRD** defines why the initiative exists and what business outcome is required.
- **PRD** defines what the product delivers: vision, users, stories, features, and metrics.
- **FSD / FRD** defines detailed system behavior, flows, and acceptance criteria.
- **NFR / TRD** define quality attributes and technical realization.

Do not let the PRD drift into detailed workflows, UI states, or technical design — that
belongs in the FSD/FRD.

## Required Inputs

- BRD objectives and approved scope
- Target users, personas, or customer segments
- Market or competitive context, if relevant
- Prioritization constraints (timeline, capacity, dependencies)

## Recommended PRD Structure

1. **Document Control**: version, authors, dates, status, approvals
2. **Product Vision and Problem Statement**
3. **Target Users and Personas**
4. **User Stories / Jobs-to-Be-Done**
5. **Features and Requirements**: prioritized, uniquely identified
6. **Success Metrics and KPIs**
7. **Non-Goals**: explicitly out of scope
8. **Assumptions, Constraints, and Dependencies**
9. **Release Criteria**
10. **Traceability to BRD**

## Writing Rules

- Write user stories as: `As a <persona>, I want <capability>, so that <benefit>`.
- Prioritize every feature explicitly (e.g. MoSCoW, Kano, or a numbered rank) — an
  unprioritized feature list is not a PRD.
- State non-goals as clearly as goals; scope creep usually starts as an unstated assumption.
- Tie every success metric back to a BRD objective — a metric with no business owner is a
  vanity metric.
- Keep the PRD free of implementation detail, UI copy, and technical constraints.

## INVEST Test for User Stories

Every user story should pass this test before inclusion:

| Letter | Check | Bad Example | Good Example |
|---|---|---|---|
| **I**ndependent | Can it ship without waiting on unrelated stories? | "Redesign onboarding" (bundles 6 features) | Split into one story per capability |
| **N**egotiable | Is it a conversation starter, not a fixed contract? | Fully speced UI mockup as the story | "As a user, I want to reset my password" |
| **V**aluable | Does it deliver value to a user or the business? | "Refactor internal service" as a user story | Frame the user-facing outcome, not the refactor |
| **E**stimable | Can the team size it? | "Improve search" | "Add typo-tolerant search for product names" |
| **S**mall | Fits in a single iteration? | "Build the marketplace" | "Add seller rating display on product page" |
| **T**estable | Has clear pass/fail acceptance criteria? | "Make checkout better" | "Checkout completes in ≤ 3 steps with saved payment" |

## House IDs and traceability

Product capabilities carry immortal `PRD-NNN` IDs, each declaring `Trace: BR-NNN` upward
(grammar, linking rules, RTM format in `../references/lifecycle.md`). Downstream, a zeno
Feature card links back with `**Implements:** PRD-NNN`. A `Won't` row with a reason (e.g.
"PRD-005 (Won't, this release) Price-drop alerts — recorded to kill repeat asks") is part of
the contract, not filler.

## Review rules — good vs template-filled

- Problem before solution: the PRD must survive losing its feature list and still justify
  the work.
- No implementation prescriptions: "use PostgreSQL" belongs downstream — state the need. But
  record real constraints explicitly, labeled as constraints.
- Every success metric is falsifiable, has an owner and a cadence, and traces to a BR ID.
- Non-goals get the same care as goals: name the recorded-and-rejected items so the same
  debate doesn't recur every quarter.
- Every user story maps to a PRD-ID'd capability; release criteria name which IDs must ship
  and which may trail.

## Worked exemplar (compact)

Continues the Lumen / Saved-Search Alerts chain from the BRD exemplar
(`../business-requirements-standards/`):

```markdown
# PRD — Saved-Search Alerts
Control: v1.1 · Owner: PM Marketplace · Status: Approved 2026-08-05 · Trace: BRD v1.0

## Vision & Problem
Buyers who don't find a book today have no reason to return tomorrow. Saved-Search Alerts
turns a failed search into a standing order. Buyer success is "I stopped checking manually."

## Target Users
P1 The Hunter — collector searching for specific editions weekly (interviews n=14, Jun 2026).
P2 The Student — needs one title before term, price-sensitive. Non-persona: sellers.

## User Stories
- US-1 As a Hunter, I want to save my current search with one action, so that Lumen keeps
  looking after I leave.  → PRD-001
- US-3 As a Student, I want a daily digest instead of instant alerts, so that I'm not
  spammed.  → PRD-003

## Features (prioritized)
- PRD-001 (Must)  Save current search as a named alert. Trace: BR-001
- PRD-002 (Must)  Instant notification on new matching listing. Trace: BR-001, BR-002
- PRD-004 (Must)  Pause/delete saved searches; one-tap unsubscribe. Trace: BR-003
- PRD-005 (Won't, this release) Price-drop alerts — recorded to kill repeat asks.

## Success Metrics
- ≥40% of failed searches convert to a saved search (owner: PM, weekly) → BR-001
- Unsubscribe rate <5%/month of alert users (owner: PM, monthly) → BR-003

## Non-Goals
No seller analytics. No ranking changes. No push-notification mobile work. No ML matching.

## Release Criteria
PRD-001, PRD-002, PRD-004 shipped with metrics instrumented; PRD-003 may trail one release.
```

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Feature list with no priority | Everything looks equally urgent | Rank explicitly (MoSCoW, Kano, or numbered) |
| Success metric with no owner | No one is accountable for the outcome | Assign a metric owner and a measurement cadence |
| PRD written as a spec | Duplicates FSD/FRD content, drifts out of sync | Keep PRD at vision/feature level; detail lives in FSD |
| Personas without evidence | Assumed users instead of researched ones | Cite research, interviews, or usage data |
| Missing non-goals | Scope grows silently during implementation | List explicit non-goals alongside goals |
| Metrics disconnected from BRD | Product optimizes for the wrong outcome | Trace every metric to a BRD objective |

## Review Workflow

1. Confirm the PRD traces back to an approved BRD objective.
2. Validate personas and user stories are evidence-based, not assumed.
3. Check every feature is prioritized and every non-goal is explicit.
4. Confirm success metrics are measurable and owned.
5. Validate downstream readiness: can an FSD/FRD be written from this without guessing?

## Pre-flight checklist — run before delivering any PRD

- [ ] Product vision and problem statement are explicit
- [ ] Personas and user stories are evidence-based
- [ ] Features are prioritized, not just listed
- [ ] Success metrics are measurable and traced to BRD objectives
- [ ] Non-goals are explicit
- [ ] Traceability to the BRD is preserved
