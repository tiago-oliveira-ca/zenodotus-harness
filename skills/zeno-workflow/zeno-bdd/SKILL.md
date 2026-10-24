---
name: zeno-bdd
description: >
  The BDD stage of zeno's Gate 2 (Route), dispatched via the zeno-workflow dispatcher: translate
  each of zeno-atdd's Business Acceptance Criteria into one concrete Given/When/Then scenario on
  the Story card, written declaratively (behavior, not UI mechanics), before handing off to Gate
  2's own Task-breakdown step (not directly to zeno-tdd — Gate 3's TDD only starts once every
  Story on the Feature's list is fully planned). Runs after zeno-atdd, still in Gate 2. Trigger on:
  "BDD", "Given/When/Then", "write the scenarios", "Gherkin", "translate this story", "user
  scenario", "behavior scenario".
---

# Zeno BDD — acceptance criteria become scenarios

This is Gate 2's BDD stage in the fixed DDD → FDD → ATDD → **BDD** → TDD pipeline, sitting between
`zeno-atdd`'s acceptance criteria and Gate 2's own Task-breakdown step. Its job: turn each
acceptance criterion into a concrete, executable Given/When/Then scenario Gate 3's `zeno-tdd` can
later implement against.

**Iron Law: NO TDD CYCLE WITHOUT A SCENARIO IT PROVES.** `zeno-tdd` only ever implements against a
Given/When/Then written here — never against a vague story title or criterion.

## The gate (do these in order)

1. **Read the Story's acceptance criteria** (written by `zeno-atdd`) on its card. Its `Status`
   should already read `development`.
2. **Translate each criterion into Scenario(s).** A **concrete-condition criterion** becomes
   exactly one Given/When/Then block. A **rule/checklist criterion** (an invariant — "must always
   be true") isn't itself a single example, so it expands into **one scenario per concrete instance**
   that illustrates it — this is not the same anti-pattern as combining unrelated criteria into one
   scenario (below); every scenario still traces back to exactly one criterion, a rule criterion
   just earns more than one. Each scenario:
   - **Given** — the concrete starting state/context.
   - **When** — the single action or event (exactly one per scenario — more than one means it's
     really two behaviors, split it).
   - **Then** — the observable outcome (what would actually be checked) — never an internal
     implementation detail like a raw database row.

   Where `zeno-atdd` named a rule's **counter-example** in the handoff, translate it into its own
   scenario too — a **Given/When** that looks like it should satisfy the rule, paired with a
   **Then** proving the rejection/failure path. A rule proven only by passing scenarios hasn't been
   proven against the case that should fail it.
3. **Write declaratively, not imperatively**, onto the Story card's `## Scenarios (BDD)` section.
   Describe *what* happens in domain language, not *how* a user clicks through a UI. Apply the same
   litmus test as `zeno-atdd`: would this step's wording need to change if the implementation
   changed? If yes, rewrite it.
4. **Hand off to Gate 2's Task-breakdown step** — not directly to `zeno-tdd`. That step (written
   directly by Gate 2, not a `zeno-workflow` dispatch — see `zeno/SKILL.md`'s Gate 2 step 6) turns
   this Story's Scenarios into a concrete Task list, ending with a documentation Task, before Gate
   2 moves to the next unplanned Story (`zeno-atdd/SKILL.md` step 6). Only once every Story on the
   Feature's list has been through this full ATDD → BDD → Task-breakdown pass does Gate 3 open —
   there, each Scenario becomes exactly one `zeno-tdd` red→green→refactor cycle, logged to the
   Story's active Task card's **Proof** section.

For the full Gherkin syntax reference (Feature/Rule/Background/Scenario Outline+Examples/Doc
Strings/Data Tables/Tags) and the Three Amigos/Discovery/Formulation/Automation model, see
`references/bdd-concepts.md` — background theory only. The scenarios this stage actually produces
stay plain markdown on the Story card; nothing here requires adopting Cucumber, `.feature` files,
or literal step-definition tooling unless the project already has that pipeline.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| One scenario covering several *different* criteria at once | One or more Given/When/Then blocks per criterion — never blend two criteria into one scenario |
| Forcing a rule/invariant criterion into exactly one scenario | Let it expand into one scenario per concrete instance the rule covers |
| Imperative, UI-coupled steps ("click," "type in the field") | Declarative, behavior-focused steps in domain language |
| A scenario with no observable **Then** | Rewrite until there's a concrete, checkable outcome |
| More than one **When** in a scenario | Split it — that's two behaviors, not one |
| A scenario invented that no acceptance criterion covers | Every scenario traces back to a written criterion |
| Implementation details leaking into steps (table names, endpoints) | Domain concepts only — see `references/bdd-concepts.md` |
| A rule/checklist criterion with only passing scenarios, no scenario proving its counter-example | Translate ATDD's counter-example into its own Given/When/Then showing the rejection path |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "I'll write the scenario the way the UI works, it's clearer" | Imperative scenarios break on every UI tweak — write behavior, not mechanics |
| "One scenario is basically the whole story" | Split it — each acceptance criterion earns its own scenario |
| "This detail is technical but harmless to include" | If it would change when implementation changes, it doesn't belong in the scenario |

## Red flags — stop and rewrite

- A `zeno-tdd` cycle starting with no Scenario on the Story card.
- A Scenario with no observable **Then**, or more than one **When**.
- Scenario steps that name a button, field, table, or endpoint instead of a domain concept.
- A Story card with Scenarios but no Acceptance Criteria they trace back to.
- A rule-type criterion with a documented counter-example that has no corresponding scenario.

## Pre-flight checklist — run before delivering any BDD scenario set

- [ ] Every acceptance criterion has at least one traceable Given/When/Then scenario — exactly one
      for a concrete-condition criterion, one per instance for a rule/checklist criterion.
- [ ] Every scenario has exactly one **When** and a concrete, checkable **Then**.
- [ ] Steps are declarative and written in domain language, not UI mechanics.
- [ ] Where ATDD named a rule's counter-example, it has its own scenario proving the
      rejection/failure path.
- [ ] The Story card (`docs/stories/STORY-<slug>.md`) is updated in place — no separate file.
