---
name: functional-specification-standards
description: >
  Standards for Functional Requirements / Specification Documents (FRD / FSD). Use when
  writing or reviewing detailed system behavior specifications, user flows, acceptance
  criteria, or any document that bridges product intent to functional requirements. Trigger
  on: "write an FSD", "write an FRD", "functional spec", "functional specification",
  "functional requirements document", "define system behavior", "acceptance criteria",
  "user flows", "use cases", "feature specification", "what should the system do", or any
  document specifying how a system behaves from the user's perspective.
---

# Functional Specification Standards

Use this skill when defining or reviewing system behavior in detail. An FSD should turn
business intent into clear user-facing and system-facing behaviors without dropping into
implementation design.

## Core Boundaries

- **BRD / PRD** define business goals and product intent.
- **FSD** defines detailed behavior, flows, states, and acceptance criteria.
- **NFR** defines quality attributes (performance, security, availability) alongside FSD's
  functional behavior — use that skill when NFRs need their own document.
- **TRD / SAD** define technical realization, architecture, and platform constraints.

## Required Inputs

- Business goals or product scope
- Personas, actors, or user roles
- Features, workflows, and edge cases in scope
- Acceptance expectations and relevant NFRs
- Related designs, mockups, or story references

## Recommended FSD Structure

1. **Document Control**
2. **Purpose and Scope**
3. **Actors / Personas**
4. **Use Cases and Workflows**
5. **Functional Requirements**
6. **Acceptance Criteria**
7. **Non-Functional Considerations**
8. **Supporting Artifacts and References**
9. **Traceability**

## Writing Rules

- Give each requirement a unique ID.
- Prefer `The system shall...` style statements for mandatory behavior.
- Cover normal flow, alternate flow, validation, and failure states.
- Keep requirements atomic, testable, and unambiguous.
- Separate behavioral requirements from technical implementation notes.

## Acceptance Criteria Template

Use the Gherkin (Given/When/Then) pattern for complex behaviors:

```
FR-001: User Login

The system shall authenticate users with valid credentials.

Acceptance Criteria:
  GIVEN a registered user with valid credentials
  WHEN the user submits the login form
  THEN the system shall redirect them to the dashboard within 2 seconds

  GIVEN a user with an incorrect password
  WHEN the user submits the login form
  THEN the system shall display "Invalid credentials" and not reveal which field is wrong

  GIVEN a user who has failed 5 consecutive login attempts
  WHEN they attempt to log in again
  THEN the system shall lock the account for 15 minutes and notify by email
```

## House IDs and traceability

Functional requirements carry immortal `FR-NNN` IDs (qualities `NFR-NNN`), each declaring
`Trace: PRD-NNN` upward (grammar, RTM format, proportionality in
`../references/lifecycle.md`). **The paste-through convention is what makes the chain
cheap:** write each FR's acceptance criteria as declarative Given/When/Then blocks suffixed
`[FR-NNN]`, so they paste *unchanged* into the zeno story card's `## Scenarios (BDD)`
section, and the story card gains `**Implements:** FR-NNN` under its header. The story's
Proof section then doubles as test-level traceability — no separate test-case register.

## Review rules — good vs template-filled

- The happy path is never where launches bleed: an explicit Error & Edge States section is
  required, even if short — its absence is the most common senior-review bounce.
- Acceptance criteria are declarative business intent ("Given a logged-in buyer"), never UI
  clicks or internals ("Given the UserService returns a valid JWT") — imperative Gherkin
  hides the behavior and rots on every UI change.
- One behavior per scenario, one scenario per acceptance criterion, 1:1; a story needing ≥4
  criteria is usually two stories.
- Every quality adjective gets a fit criterion: Scale (unit) + Meter (measurement procedure)
  + Must (failure begins) + Plan (target). Latency/availability NFRs state percentile +
  threshold + window + load condition + breach consequence — "P95 ≤ 800ms" alone is
  template-fill.
- Run the orphan check both ways before approval: every FR answers "which PRD ID?", every
  Must-level FR appears in at least one story/scenario (grep — zero hits = unbuilt promise).

## Worked exemplar (compact)

Completes the Lumen / Saved-Search Alerts chain (BRD and PRD exemplars in the sibling
skills):

```markdown
# FRD — Saved-Search Alerts
Control: v1.0 · Owner: BA/PM · Status: Approved 2026-08-07 · Trace: PRD v1.1

## Functional Requirements
- FR-001  The system shall let an authenticated buyer save the active search (query +
  filters) under a name, max 20 saved searches per account. Trace: PRD-001
- FR-003  The system shall not alert the saved-search owner for listings they posted
  themselves. Trace: PRD-002
- FR-004  The system shall dispatch an instant alert (email + in-app) for each match to
  owners on instant cadence. Trace: PRD-002

## Acceptance Criteria (per FR — these become the story-card scenarios verbatim)
  GIVEN buyer Ana has saved search "1st-ed Pessoa" with instant cadence
  WHEN a listing matching that query is published by another user
  THEN Ana receives an in-app alert and an email within 5 minutes  [FR-004]

  GIVEN Ana posts a listing matching her own saved search
  WHEN the listing is published
  THEN no alert is sent to Ana  [FR-003]

## Error & Edge States
Save beyond 20 → reject with "limit reached", offer management view (FR-001). Listing
unpublished before dispatch → suppress. Hard email bounce → auto-pause email channel, keep
in-app, surface banner. Duplicate listing edit → no re-alert per listing ID.

## Non-Functional (fit-criterion style)
- NFR-002  Alert delivery: ≥99% of instant alerts delivered ≤5 min end-to-end, per calendar
  week; breach 2 consecutive weeks = stop-feature-work-and-fix. Trace: PRD-002

## Traceability
Up: PRD-001..004. Down: STORY-alert-dispatch (FR-002..004, NFR-002), STORY-alert-controls
(FR-006, NFR-003). RTM: docs/requirements/rtm.md.
```

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| "The system should be fast" | Untestable | "The system shall respond within 500ms at P95" |
| Combined requirements in one statement | Cannot trace or test independently | Split into atomic FR-NNN statements |
| Implementation leaking into behavior spec | Constraints FSD scope | Move technical choices to TRD/SAD |
| Missing error and edge-case flows | Gaps discovered in implementation | Explicitly document failure, empty, and boundary states |
| Acceptance criteria as prose narrative | Hard to test | Use structured Given/When/Then or table format |
| Orphan requirements | Not traceable to business need | Every FR must link to a BRD objective or user story |

## Review Workflow

1. Confirm scope and actors.
2. Walk core workflows end to end.
3. Check that every feature has explicit acceptance criteria.
4. Validate traceability back to BRD or PRD and forward to testing.
5. Flag missing states, unclear language, or hidden technical assumptions.

## Pre-flight checklist — run before delivering any FSD/FRD

- [ ] Scope, actors, and workflows are explicit
- [ ] Every requirement has a unique ID
- [ ] Acceptance criteria are measurable
- [ ] Edge cases and error states are covered
- [ ] Supporting designs or diagrams are linked where needed
- [ ] Traceability to higher-level requirements is preserved
