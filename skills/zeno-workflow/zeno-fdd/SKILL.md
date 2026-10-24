---
name: zeno-fdd
description: >
  The FDD stage of zeno's Gate 2 (Route), dispatched via the zeno-workflow dispatcher: at Feature
  scope, once the domain is framed by Gate 1's zeno-ddd, break the feature into an ordered Story
  list written into its Feature card. Gate 2 then walks that whole list — not just the next Story —
  via zeno-atdd + zeno-bdd + a Task breakdown, fully planning every Story before Gate 3 (Execution)
  ever opens. Keeps everything inside the .zeno/ folder's fixed layout — no extra plan
  files, no phase directories. Runs after zeno-ddd (Gate 1), before zeno-atdd (Gate 2). Trigger on:
  "plan this out", "break this down", "decompose this", "too big for one pass", "make a plan",
  "step by step plan", "sequence the work", "this is a big feature", "outline the steps",
  "how do we stage this", "feature list".
---

# Zeno FDD — feature list & development plan

Some tasks are too large for a single Scope → Route → Execution → Review pass. This is Gate 2's
opening stage in the fixed DDD → **FDD** → ATDD → BDD → TDD pipeline: it turns a Gate-1-framed
Feature into an ordered Story list — written into that Feature's own card, not a directory of plan
files. It runs after Gate 1's `zeno-ddd`, and before Gate 2's own `zeno-atdd`/`zeno-bdd`/Task-breakdown
loop takes every Story on that list through the rest of the pipeline, all before Gate 3 opens.

**Iron Law: EVERY STORY IS INDEPENDENTLY VERIFIABLE.** A Story with no way to prove it's done is
not a Story — it's a wish. If you can't name how a Story will be verified, it isn't ready.

## When to use it

Reach for `zeno-fdd` when the Framed work spans multiple files, multiple Stories, or a sequence where
later Stories depend on earlier ones. For a single-behavior change, skip it — file the one Story
directly (ad hoc, no parent Feature, no `zeno-ddd` stage either) and let Gate 2's
`zeno-atdd` → `zeno-bdd` → Task breakdown fully plan it, then Gate 3's `zeno-tdd` implement it.

## How to plan

1. **Confirm the domain is framed.** `zeno-ddd` must have already filled in all five fields of the
   Feature card's `## Domain & Architecture (DDD)` section. Don't start listing Stories against an
   unframed Feature.
2. **Write the Story list (FDD).** An ordered `## Story list (FDD)` section on the Feature card
   (`docs/features/FEAT-<slug>.md`, the template provides it). The card's `Status` stays
   `development` throughout — once the list is written, Gate 2 moves on to plan **every** Story on
   it (ATDD, BDD, Task breakdown), tracked on each Story's own card, not this one, all before Gate 3
   opens. Each Story is one line:
   - **Sized to one Story** — one ATDD → BDD pass (then its own Task list for TDD), and per the
     feature-naming discipline (`<action> the <result> for a(n) <object>`) roughly 1-3 days, no
     more than ~2 weeks — split anything bigger.
   - **Names the file(s) it touches** — so the next session (or you, later) knows where it lands.
   - **States a rough feasibility hint, not a final spec** — enough to know verification is
     possible in principle (e.g. "an integration test against the new endpoint"). This is not the
     Story's real Acceptance Criteria — `zeno-atdd` writes those collaboratively, and its criteria
     supersede whatever's sketched here if the two ever disagree.
   - **Ordered by dependency** — earlier Stories unblock later ones; note any that can be done in
     any order.
   Use a flat status marker per Story: `[ ]` not started · `[~]` in progress · `[x]` done. That is
   the whole ceremony — no numbering scheme, no per-story plan files, no separate plan document.

For the full Feature List table format (priority, effort, dependencies, success metric),
prioritization frameworks (MoSCoW/RICE/Kano/Value-vs-Effort), the Roadmap-vs-Release-Plan
distinction, and traceability guidance, see
`documentation/feature-planning-standards/SKILL.md` — this stage applies a trimmed version of that
skill's discipline directly onto the Feature card; it doesn't redefine it.

## How Gate 2 plans it, how Gate 3 implements it

Planning and implementation are two separate passes over the same list now, not one interleaved
walk:

- **Gate 2 (planning):** works through the Story list top-down, fully detailing **every** Story —
  `zeno-atdd` writes its acceptance criteria, `zeno-bdd` its scenarios, then Gate 2 writes its Task
  list directly — before Gate 2 closes. This pass doesn't flip the list's own `[ ]`/`[~]`/`[x]`
  markers; those track *implementation* progress, not planning progress. A Story with a fully
  populated card (Acceptance criteria, Scenarios, Task list all filled) but still `[ ]` on the
  Feature's list means "planned, not yet implemented" — the expected state for every Story once
  Gate 2 closes and before Gate 3 has touched any of them.
- **Gate 3 (implementation):** works through the same list top-down, marking each Story `[~]` then
  `[x]` as `zeno-tdd` loops its already-written Task list to completion. This is where the WIP-1
  rule bites — only one Story is ever `[~]` at a time.

`.zeno/project.md`'s **Next step** always points at the first `[ ]` Story, so resume is instant —
during Gate 2 that means "next Story to plan," during Gate 3 it means "next Story to implement."
When a Story's reality diverges from the plan, update its line and log why in the Feature card's
Decisions log — the Story list is a living checklist, not a contract.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Decomposing a single-behavior change | Skip the Feature/Story list; file one ad hoc Story |
| Stories with no verification | Every Story names how it's proven done |
| A Story too big for one ATDD→BDD→TDD pass | Split it until each is independently verifiable |
| Vague Stories ("add validation") | Name the file(s) and the concrete change |
| Listing Stories before `zeno-ddd` has framed the domain | FDD never opens before DDD closes |
| Spawning plan files / phase directories | The Story list lives on the one Feature card |
| Treating the Story list as fixed | Update lines + log deviations as reality diverges |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "I'll hold the Stories in my head" | The point is cross-session resume; an unwritten list is lost on compaction |
| "A plan doc would be cleaner than the Feature card" | A second file is the sprawl this system exists to avoid |
| "This Story is obviously done when it's done" | If you can't name the check, you can't prove it — split or clarify |
| "I'll skip straight to FDD, DDD felt like overhead" | An unframed Story list drifts into a grab-bag — `zeno-ddd` closes first, always |

## Red flags — stop and re-plan

- A Story you can't verify.
- A Story you can't finish in one ATDD→BDD→TDD pass.
- More than one `[~]` Story at a time (you're not sequencing, you're sprawling — this is the
  Kanban board's WIP limit, not just a plan-list rule).
- A Story list with no Domain & Architecture section above it on the Feature card.
- The Story list lives anywhere other than its Feature's own card.

## Pre-flight checklist — run before delivering any plan

- [ ] `zeno-ddd` has framed the Feature card's Domain & Architecture section before any Story is listed.
- [ ] The Story list lives in the one Feature card — no plan files, no directories.
- [ ] Every Story is sized to one ATDD→BDD→TDD pass (roughly 1-3 days, never more than ~2 weeks).
- [ ] Every Story names the file(s) it touches and its own verification.
- [ ] Stories are ordered by dependency; `Next step` on `project.md` points at the first `[ ]`.
- [ ] Decomposition was actually warranted (multi-file / multi-story), not a one-liner.
