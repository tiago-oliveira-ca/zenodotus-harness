---
name: development-planning-standards
description: >
  Standards for breaking Solution Architecture Documents into Epics, Stories, and Tasks —
  the Development Planning stage between architecture and implementation. Use when creating
  or reviewing an Epic, writing a Story, splitting a Story into Tasks, or checking whether
  work is ready to pull into a sprint. Trigger on: "write an epic", "break this down into
  stories", "story breakdown", "sprint planning", "definition of ready", "definition of
  done", "story splitting", "is this story too big", "task breakdown", "backlog grooming",
  or any request to turn an architecture component or requirement into actionable
  development work.
---

# Development Planning Standards

Use this skill when turning a SAD component or FRD/NFR requirement into Epics, Stories, and
Tasks. This is the bridge between architecture (intent) and implementation (code) — get the
breakdown wrong and either scope silently drifts from the design, or engineers reverse-engineer
scope from the SAD themselves, sprint by sprint, without anyone deciding it deliberately.

## Core Boundaries

- **Epic**: One architecture component or capability from the SAD. Too large to implement or
  estimate as a single unit; exists to group related Stories, not to be "done" itself.
- **Story**: One user-facing or system behavior, small enough to fit in a single sprint and
  to be independently valuable. Traces to exactly one Epic and one FRD/NFR requirement.
- **Task**: A concrete implementation step inside a Story (a migration, a producer, a test).
  Tasks are not independently valuable and don't need their own acceptance criteria — the
  Story they belong to does.
- **Acceptance Criteria**: Per-Story conditions that must hold for the Story to be accepted.
  Different from a Story's Definition of Done, which applies to every Story regardless of
  content (see below).
- This skill governs **development-level** Stories (sprint-ready, engineering-facing). It is
  not the same granularity as the user stories in `../product-requirements-standards` (a PRD
  Story is a product narrative; a development Story is what a PRD Story or SAD component
  becomes once it's ready to build). Apply the INVEST test from that skill to development
  Stories too — it still applies, just at a finer grain.
- **Jira vocabulary differs.** This skill's *Task* (a step inside a Story) maps to a Jira
  **Sub-task**; in Jira, Stories and Tasks are peers under an Epic. Reviewing or fixing an actual Jira
  hierarchy belongs to `../../zeno-stack/zeno-jira-structure-review/SKILL.md`, which wins on Jira
  issue types and parent rules.
- This skill sits **below** `../feature-planning-standards/SKILL.md`: where a Feature List
  exists, an Epic should trace to a Feature ID from it, not just a SAD component — a Feature
  there typically becomes one or more Epics/Stories here.

## Required Inputs

- The SAD component or capability this Epic covers
- The FRD/NFR requirement(s) each Story must satisfy
- Team capacity and sprint length, for sizing
- Existing Definition of Ready / Definition of Done conventions, if the team already has them

## Recommended Epic Structure

1. **Title**: names the architecture component or capability, not an activity (`Order
   Processing Service`, not `Build order stuff`)
2. **Architecture Link**: which SAD component and ADRs this Epic implements
3. **Business Link**: which BRD objective or PRD feature this Epic ultimately serves
4. **Success Criteria**: what must be true for the Epic to be considered done — usually "all
   child Stories accepted and the component meets its NFR targets"
5. **Stories**: the list, kept current as Stories are added or split

## Recommended Story Structure

1. **Title**: a behavior, not a task (`Publish order-created event`, not `Kafka work`)
2. **Narrative**: `As a <actor>, I want <capability>, so that <benefit>` for user-facing
   Stories, or a plain behavioral statement for system-to-system Stories with no human actor
3. **Acceptance Criteria**: Given/When/Then or a checklist — specific enough to write a test
   from directly
4. **Traceability**: the Epic it belongs to and the FRD/NFR requirement ID it satisfies
5. **Estimate**: story points, T-shirt size, or hours per team convention
6. **Dependencies**: other Stories or external systems this one is blocked by
7. **Definition of Done**: usually inherited from the team standard (see below), stated only
   if this Story has an exception

## Recommended Task Structure

- One concrete technical step (`Create database migration`, `Implement Kafka producer`, `Add
  unit tests`) with an estimate and an implicit owner (whoever picks it up)
- No acceptance criteria of its own — a Task is done when it compiles/passes review; the
  Story it belongs to is what gets accepted

## Definition of Ready (DoR)

A Story should not enter sprint planning unless it passes all of these:

- [ ] Acceptance criteria are written and specific enough to test against
- [ ] It traces to exactly one Epic and one FRD/NFR requirement
- [ ] It is estimated
- [ ] Its dependencies are identified and either resolved or explicitly sequenced
- [ ] It is small enough to complete within one sprint (INVEST: Small)

## Definition of Done (DoD)

A Story is not done until all of these hold, regardless of what the Story is about:

- [ ] Acceptance criteria are met and demonstrated
- [ ] Code is reviewed and merged (see `../../code-standards` + `/code-review`)
- [ ] Tests exist at the appropriate layer (see `zeno-stack/zeno-python-testing`,
      `zeno-stack/zeno-react-testing`, `zeno-stack/zeno-e2e-testing`, or
      `zeno-stack/zeno-browser-qa` for test code/execution; `../../testing` for test
      specification documents)
- [ ] Documentation affected by the change is updated (API docs, runbook, ADR if a decision
      changed)
- [ ] The change is deployable without manual follow-up steps

## Story Splitting Patterns

When a Story fails INVEST's "Small" test, split along one of these axes rather than
padding out a single oversized Story:

| Pattern | Example |
|---|---|
| Workflow steps | Split "process an order" into "validate order," "reserve inventory," "charge payment" |
| Business rules / variations | Split "apply discounts" into one Story per discount type |
| CRUD operations | Split "manage users" into Create, Read, Update, Delete Stories |
| Happy path vs. edge cases | Ship the happy path Story first; edge cases and error handling become their own Story |
| Cross-cutting concerns | Split "add search" from "add search result caching" — the second is an optimization, not core behavior |

## Writing Rules

- An Epic's title names a component or capability, never an activity or sprint.
- A Story's acceptance criteria must be specific enough that a test could be written from
  them directly — "works correctly" is not an acceptance criterion.
- Every Story traces to exactly one Epic and one requirement. A Story that can't name both is
  scope that snuck in without a design basis (see `../references/lifecycle.md`).
- Don't write a Task as if it were a Story — "Kafka producer" has no acceptance criteria and
  isn't independently valuable; it belongs inside a Story.
- Definition of Done is a standing team agreement, not something to negotiate per Story.
  Only call it out per-Story when this Story is a deliberate exception.

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Epic that never closes | No clear success criteria, becomes a permanent bucket | Define success criteria up front; split into a new Epic when scope genuinely grows |
| Task disguised as a Story | "Update the database" has no acceptance criteria, no user value | Reframe around the behavior it enables, or demote it to a Task inside a real Story |
| Story with no acceptance criteria | Can't verify it's done; scope argued after the fact | Write acceptance criteria before estimating, not after implementation |
| Orphaned Story | No Epic, no FRD/NFR link — can't tell why it exists | Every Story must trace to an Epic and a requirement; if it can't, question whether it belongs |
| Oversized Story | Doesn't fit in a sprint, blocks visibility into progress | Split along one of the patterns above before estimating |
| Definition of Done redefined per Story | Inconsistent quality bar, "done" means different things | Keep one team-wide DoD; only exception explicitly, with reason |

## Review Workflow

1. Confirm the Epic names a real SAD component, not just an activity.
2. Confirm every Story traces to one Epic and one FRD/NFR requirement.
3. Check each Story against Definition of Ready before it's considered sprint-eligible.
4. Check acceptance criteria are specific enough to test against directly.
5. Flag any Task written with Story-shaped language (acceptance criteria, user value) —
   it's either a Story in disguise or unnecessary ceremony.
6. Confirm Definition of Done is the team standard, not reinvented per Story.

## Pre-flight checklist — run before delivering any epic, story, or task breakdown

- [ ] Epic traces to a real SAD component and states success criteria
- [ ] Every Story traces to exactly one Epic and one FRD/NFR requirement
- [ ] Every Story has specific, testable acceptance criteria
- [ ] Stories pass INVEST, including Small — split further if not
- [ ] Tasks are implementation steps, not Stories wearing a Task label
- [ ] Definition of Ready is met before a Story enters a sprint
- [ ] Definition of Done is the team standard, called out per-Story only as an exception
