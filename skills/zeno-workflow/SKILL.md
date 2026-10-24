---
name: zeno-workflow
description: >
  The planning-and-implementation pipeline dispatcher for the zeno loop. Routes to the correct
  method skill for the active DDD -> FDD -> ATDD -> BDD -> TDD stage, now split across three
  gates: DDD (Gate 1), FDD/ATDD/BDD (Gate 2, planning the full backlog before any coding starts),
  TDD (Gate 3, looping over the already-planned Task list). Only reachable from inside the zeno
  loop, once Scope has sized and approved the work — not invoked cold. Trigger on: "build
  this feature", "start the pipeline", "which stage are we on", "next stage", "advance the
  pipeline", or any of the five stage names ("DDD", "FDD", "ATDD", "BDD", "TDD") when used to mean
  "which skill handles this stage" rather than a specific technical question already answered by
  one of the nested skills directly.
---

# Zeno Workflow Dispatcher — planning and implementation pipeline

Zeno's fixed DDD → FDD → ATDD → BDD → TDD pipeline spans three gates, not one: Gate 1 runs DDD,
Gate 2 runs FDD/ATDD/BDD (planning every Story fully, before Gate 3 opens), Gate 3 loops TDD over
the already-planned Task list. When it's time to advance to the next stage, load the matching
nested skill below before doing anything else. Every skill in the zeno framework — including every
nested leaf here — starts with `zeno-`, so the flat skill listing always shows its family
membership at a glance.

## Routing Table

| Stage | Gate | Runs when | Skill to load |
|---|---|---|---|
| DDD | **Gate 1** | Framing domain & architecture for a Feature, once, before its Story list exists | `zeno-ddd/SKILL.md` |
| FDD | **Gate 2** | Decomposing a domain-framed Feature into an ordered Story list | `zeno-fdd/SKILL.md` |
| ATDD | **Gate 2** | Writing business acceptance criteria — looped over **every** Story on the Feature's FDD list before Gate 2 closes, not just the next one | `zeno-atdd/SKILL.md` |
| BDD | **Gate 2** | Translating each Story's acceptance criteria into Given/When/Then scenarios — same full-list loop as ATDD, before Gate 2 closes | `zeno-bdd/SKILL.md` |
| TDD | **Gate 3** | Red/green/refactor implementation of one scenario at a time, on one Task (or SubTask, if the Task has a SubTask list) | `zeno-tdd/SKILL.md` |

## Instructions

1. The pipeline runs in this fixed order: **DDD → FDD → ATDD → BDD → TDD.** Never skip a stage
   whose scope applies (see each leaf's own "when to use it" / sizing-ladder guidance for when a
   stage is legitimately skipped — e.g. an ad hoc Story with no parent Feature skips DDD and FDD).
2. **Which stages are even reachable depends on which gate is calling.** From Gate 1, only DDD is
   in scope (plus Epic→Features enumeration, which isn't a `zeno-workflow` stage at all — see
   `zeno/SKILL.md`'s Gate 1). From Gate 2, FDD then ATDD/BDD are in scope, looped over the whole
   Story list — Gate 2 never hands a partially-planned Feature to Gate 3. From Gate 3, only TDD is
   in scope, over an already-fully-planned backlog.
3. Identify the active card (`.zeno/project.md`'s Kanban board shows which item is outside
   Backlog/Closed) and read its `Status`. A `backlog` card hasn't started. A `development` card's
   specific pipeline stage is read off which of its own sections are still empty, not a second
   field: for a **Feature**, an empty Domain & Architecture section means DDD is next, a filled
   one with an empty Story list means FDD is next; for a **Story**, an empty Acceptance criteria
   section means ATDD is next, a filled one with empty Scenarios means BDD is next; once BDD's
   Scenarios are written, Gate 2 writes that Story's Task list directly (not a `zeno-workflow`
   stage — see `zeno/SKILL.md`'s Gate 2 step 6) before moving to the next Story; once every Story's
   Task list exists and Gate 3 has opened, pull the active Story's next `[ ]` Task (or SubTask, if
   that Task has its own SubTask list) and run TDD there — an empty Proof section on that
   Task/SubTask card means TDD is next.
4. Load **only** the matching nested skill; each carries its own full discipline (Iron Law, gate
   steps, anti-pattern table, pre-flight checklist) — this dispatcher holds routing only.
5. This dispatcher is not entered cold — it's reached from `zeno`'s Gate 1 (DDD, via `zeno-insight`),
   Gate 2 (FDD/ATDD/BDD, via Route's planning step), or Gate 3 (TDD), after Gate 1 has sized and
   approved the work.
6. WIP limit is 1: only one item may sit outside Backlog/Closed on the Kanban board at a time, so
   only one of these five skills is ever "active" at once.
7. **Model tier, when a stage's work is delegated to a subagent or Workflow fan-out** (e.g. bulk
   Story-card generation off an already-framed domain, bulk BDD scenario authoring off
   already-agreed acceptance criteria) rather than done inline by the main loop: DDD's domain
   framing is open-ended judgment and never gets downgraded; FDD/ATDD/BDD are template-shaped
   translation once the stage before them has already made the hard call, and are reasonable
   candidates for a cheaper tier when fanned out in bulk — Gate 2's now-mandatory full-Story-list
   loop is exactly this bulk-translation shape; TDD's actual implementation needs a tier that
   matches the codebase's real difficulty, not a blanket default. Use `/model-route` for the
   concrete shape/risk criteria — this dispatcher doesn't restate them.
