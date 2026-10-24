---
name: zeno-atdd
description: >
  The ATDD stage of zeno's Gate 2 (Route), dispatched via the zeno-workflow dispatcher: for every
  Story on a Feature's FDD list, in order — not just the next one — (or an ad hoc Story), write
  Business Acceptance Criteria collaboratively (Three Amigos) in either Given/When/Then or
  rule/checklist form, before handing off to zeno-bdd. Runs after zeno-fdd, before zeno-bdd — both
  still in Gate 2, planning every Story before Gate 3 (Execution) ever opens. Trigger on:
  "acceptance criteria", "ATDD", "conditions of satisfaction", "three amigos", "example mapping",
  "what does done mean for this story", "define acceptance criteria", "is this story ready",
  "acceptance test".
---

# Zeno ATDD — business acceptance criteria before code

This is Gate 2's ATDD stage in the fixed DDD → FDD → **ATDD** → BDD → TDD pipeline, sitting between
`zeno-fdd`'s Story list and `zeno-bdd`'s Given/When/Then scenario translation — both run inside
Gate 2, planning every Story before Gate 3 opens. Its job: turn a Story's one-line goal into the
specific, testable conditions of satisfaction a stakeholder would recognize as "done" —
collaboratively, not by one role in isolation.

**Iron Law: NO STORY MOVES TO BDD WITHOUT TESTABLE ACCEPTANCE CRITERIA WRITTEN COLLABORATIVELY OR
WITH EXPLICIT CROSS-PERSPECTIVE REVIEW.** Acceptance criteria written solo by one perspective, with
no review from the others, reintroduce the communication gap this stage exists to close.

## The gate (do these in order)

1. **Pull the next unplanned Story.** Take the Stories off the parent Feature's FDD Story list in
   order, one at a time — every Story on the list, not just the next one — and open/create each
   one's card at `docs/stories/STORY-<slug>.md` from `zeno/references/story-template.md`. If it
   still reads `Status: backlog`, flip it to `development`. (The list's own `[ ]`/`[~]`/`[x]`
   markers track *implementation* progress in Gate 3, not planning — a Story stays `[ ]` there
   through all of this, even once fully planned; see `zeno-fdd/SKILL.md`.) For an ad hoc Story
   with no parent Feature, there's just the one.
2. **Run a short Example Mapping pass.** Even solo, work through the four card types explicitly:
   the Story itself, the Rules it must satisfy, concrete Examples illustrating each rule, and any
   open Questions. **For every Rule, capture at least one confirming Example and at least one
   counter-example** — a case that looks like it should satisfy the rule but doesn't, or violates
   it outright. A Rule backed only by confirming Examples hasn't been tested against being wrong.
   Timebox it — a well-understood, well-sized story maps in minutes; too many open Questions means
   the story isn't ready, too many Rules means it should be split.
3. **Write the Acceptance Criteria**, onto the Story card's `## Acceptance criteria (ATDD)`
   section. Plain business language, stakeholder-readable, pass/fail — no implementation detail.
   Use whichever format fits: a **rule/checklist** for invariants ("must always be true"), or
   concrete conditions where specific cases matter most. Apply the litmus test: *would this wording
   need to change if the implementation changed?* If yes, rewrite it in domain terms.
4. **Distinguish Acceptance Criteria from Definition of Done.** AC are story-specific — they prove
   *this* feature does what the business needs. DoD is the team-wide quality bar (tests written,
   reviewed, docs updated) that applies to every story regardless of content — don't fold DoD items
   into a Story's AC, and don't skip DoD because AC passed.
5. **Hand off to `zeno-bdd`.** A concrete-condition criterion becomes exactly one Given/When/Then
   scenario. A **rule/checklist criterion may expand into several scenarios** — one per concrete
   instance illustrating the rule — since an invariant isn't itself a single example; say so
   explicitly when handing off a rule-type criterion so `zeno-bdd` doesn't force it into one. Also
   name each rule's **counter-example** explicitly in the handoff — `zeno-bdd` translates it into
   its own scenario proving the rejection/failure path, not just the confirming instances.
6. **Repeat from step 1 for the next unplanned Story**, once `zeno-bdd` and Gate 2's Task breakdown
   have finished this one — until every Story on the Feature's FDD list has been planned. Only then
   does Gate 2 close and Gate 3 open.

For the full walkthrough (Three Amigos origins, the Discuss/Distill/Develop/Demo cycle, Example
Mapping mechanics, INVEST, AC-vs-DoD in depth, and the named anti-patterns), see
`references/atdd-concepts.md`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Acceptance criteria written by one role alone | Three Amigos collaboration — business, dev, test perspectives |
| Criteria written in implementation terms | Plain business language a stakeholder would sign off on |
| Vague, unmeasurable criteria ("fast," "user-friendly") | Specific, measurable conditions with concrete thresholds |
| Folding Definition-of-Done items into a Story's AC | Keep AC story-specific; DoD is the separate, team-wide bar |
| Writing AC after the code exists | AC precede implementation — that's the "driven" in ATDD |
| Moving to BDD with open Example-Mapping questions unresolved | Resolve or explicitly park questions before calling it ready |
| A Rule with only confirming Examples | Capture at least one counter-example per Rule — a case that should fail it |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "I'll just write the criteria myself, it's faster" | Solo AC reintroduce the gap ATDD exists to close — get the perspectives even briefly |
| "The story is small, it doesn't need criteria" | Small stories still need a testable definition of correct |
| "QA will figure out how to test it" | QA-only ownership is a named anti-pattern — the whole team owns AC |
| "This criterion is basically implementation, but it's fine" | Apply the litmus test: would it change if the implementation did? |
| "The rule is obviously right, it doesn't need a counter-example" | Obvious rules hide the edge cases that break them — write the counter-example anyway |

## Red flags — stop and rewrite

- Acceptance criteria written by a single role with no cross-perspective input.
- A criterion that reads as a UI action or code path instead of a business outcome.
- Criteria that duplicate Definition-of-Done items instead of story-specific conditions.
- Moving to `zeno-bdd` with unresolved Example-Mapping questions still open.
- A Rule in the Example Mapping pass with no counter-example — only cases that confirm it.

## Pre-flight checklist — run before delivering any acceptance criteria

- [ ] Acceptance criteria were written collaboratively (or with explicit cross-perspective review).
- [ ] Each criterion is specific, measurable, and phrased in business/domain language.
- [ ] AC are distinct from — and don't substitute for — the team's Definition of Done.
- [ ] Open Example-Mapping questions are resolved or explicitly parked, not silently dropped.
- [ ] Every Rule has at least one counter-example, not only confirming instances, and each was
      named explicitly in the handoff to `zeno-bdd`.
- [ ] The Story card (`docs/stories/STORY-<slug>.md`) is updated in place — no separate file.
