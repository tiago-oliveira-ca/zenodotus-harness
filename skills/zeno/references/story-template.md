# Story: <slug>

**Parent feature:** FEAT-<slug> | none (ad hoc)
**Tier evidence:** <one line — why Story tier fits: the single coherent behavior, one Execution
pass, blast radius. Per zeno's sizing ladder the smallest fitting tier is the default; this line
records that it was chosen deliberately, not by habit.>
**Implements:** FR-<NNN>[, NFR-<NNN>]   <!-- optional — only when a requirements doc chain exists -->
**Goal:** <one sentence — the story's success condition>
**Status:** backlog | development | testing | closed
<!-- development spans ATDD, BDD, and Task breakdown — all three run in Gate 2, planning this
     Story fully before Gate 3 opens. Which one is active is read off this card's own section
     content (empty Acceptance criteria → ATDD; that filled but Scenarios empty → BDD; Scenarios
     filled but Task list empty → Task breakdown), not a separate field. TDD happens in Gate 3,
     below this card, on each Task/SubTask, once every Story reachable from this planning pass has
     a full Task list. -->
**Points:** <optional Scrum estimate>
**Updated:** <YYYY-MM-DD>

<!-- Definition of Ready / INVEST / story-splitting — see
     skills/documentation/development-planning-standards/SKILL.md rather than redefining here. -->

## Acceptance criteria (ATDD)
- <plain-language business pass/fail condition>
- <plain-language business pass/fail condition>

## Scenarios (BDD)
### Scenario: <name> [FR-<NNN>]
- **Given** <initial context>
- **When** <action>
- **Then** <observable outcome>
<!-- One scenario per acceptance criterion. The [FR-NNN] suffix applies only when a
     requirements chain exists — it makes Proof double as test-level traceability. -->

## Task list (breakdown)
<!-- Written by Gate 2's Task-breakdown step (not Gate 3, not a zeno-workflow dispatch — see
     zeno/SKILL.md's Gate 2 step 6), with real technical content per Task — which files, what
     approach, Engineering-owned detail — not a placeholder one-liner. Ordered, each step a
     concrete technical step owned by one contributor. A Task earns its own SubTask list only when
     it's still too big for one sitting — see `task-template.md`. TDD's red/green/refactor proof
     lives on the leaf card (the Task, or its SubTasks if decomposed), not here. The **last** Task
     is always documentation (create/update), implemented via `documenting-code`/`/docs-drift`
     rather than a TDD cycle. -->
- [ ] TASK-<slug> — <one-line goal> → `../tasks/TASK-<slug>.md`
- [ ] TASK-<slug> — <one-line goal> → `../tasks/TASK-<slug>.md`
- [ ] TASK-update-docs — create/update documentation for this Story's changes → `../tasks/TASK-update-docs.md`
<!-- [ ] not started · [~] in progress · [x] done — WIP limit: 1 [~] at a time -->
<!-- These markers track Gate 3 implementation progress, not Gate 2 planning progress — every
     Task above already has full technical content by the time Gate 3 starts touching any of
     them. -->

## Decisions
- <YYYY-MM-DD> <decision + one-line why>   (append-only; newest last)

## Outcome
<!-- Optional — written when Status flips to closed. -->
<what shipped, and any follow-ups left open>
