---
name: zeno-untangle
description: >
  Untangle an area of a codebase: inventory its coupling (hidden links, needless links, surplus)
  and its special cases without changing anything, redesign them into clusters where one change
  removes several, then fix one Story per cluster through the zeno gates and re-inventory until a
  stop rubric holds. User-started only, via /untangle. Trigger on: "/untangle", "untangle this
  codebase", "untangle the billing module", "remove the special cases", "this module is a mess",
  "reduce coupling across", or an explicit user request for a whole-area structural cleanup.
---

# Untangle — remove coupling and special cases, one cluster at a time

When the user runs `/untangle` (or explicitly asks for a whole-area structural cleanup), make the
area cheaper to change: a typical change should land in one place, and nothing should break
silently somewhere else. Do it as an inventory first, then a redesign, then one zeno Story per
cluster of findings, then a fresh inventory. Never as one big pass.

**Iron Law: NO CHANGE BEFORE THE INVENTORY IS ON A CARD.** (Invariant. The inventory is what turns
"clean this up" into checkable work, and what lets the loop know when it's finished.)

## Boundary — what this skill owns

- **Owns:** finding structural coupling and special cases across an area, grouping them, and running
  their removal through the zeno loop.
- **Dead code** found along the way (unused exports, files, dependencies) goes to the sibling leaf
  `zeno-stack/zeno-refactor-cleanup`, which has the detection tools and the one-at-a-time deletion discipline.
- **Weak tests** found along the way go to `zeno-stack/zeno-test-prune`; offered up front as the optional test pass.
- **Comments that restate code** go to `zeno-stack/zeno-comment-analysis`; offered up front as the optional comment pass.
- **Architecture-level choices** a cluster raises (a new boundary, a data store, an integration) go
  to `zeno-council` before the cluster's Story is planned.
- **Code style per language** comes from the matching `code-standards` leaf in Gate 3, as always.

## Finding taxonomy

Every finding has a kind, a location and evidence. Ask of any two pieces of code: should these
change together? Coupling is where the code's answer and the honest answer differ.

| Kind | What it is | Examples |
|---|---|---|
| **Hidden link** | Pieces that must change together but nothing says so | Two copies of the same rule with drifting details; shared mutable globals; one feature spread across layers; code that only works if called in a certain order |
| **Needless link** | Pieces tied together that shouldn't be | Callers reaching into a module's internals; dependencies pointing from core toward detail; parameters named in one caller's vocabulary; shallow modules whose interface is as big as their body |
| **Surplus** | Structure that carries nothing | Pass-through wrappers; configuration for options nobody uses; abstractions with one implementation and no second in sight; dead code (→ `zeno-refactor-cleanup`) |
| **Special case** | A one-off patch over a missing concept | An `if` for one id, plan or region; a parameter only one caller passes; a swallowed error; a retry, sleep or timeout that hides a race; a skipped or disabled test |

Treat each special case as evidence of a requirement the design never named. The fix is usually
to name that requirement, not to tidy the patch.

## Evidence — where findings come from

Read the area fully; do not inventory only the smells someone mentioned. Then corroborate with:
- **Dependency structure** — `graphify` when a graph exists, else `/update-codemaps`, else a scripted
  import graph; rerun it after each Story to see links disappear (`zeno/references/impact-analysis.md`).
- **Change history** — files that change together in `git log` but sit apart in the tree are a hidden
  link; `git blame` on a special case often names the requirement it was patching.
- **Search** — grep for the special-case signs above (literal ids, `sleep(`, broad `catch`, skip markers).
- **Skeletons and summaries** — for a large area, script a signatures-only view or have a registry
  specialist summarize parts, so the inventory covers everything without reading every line twice.

## How it runs in the zeno loop

`/untangle` opens the zeno loop; this skill supplies what each gate does with it.
- **Before starting** — WIP limit 1. If another item is outside Backlog/Closed, ask the user
  whether to finish it first or park it in Backlog; don't open the untangle Feature beside it.
- **Gate 1, Scope** — size first. One area is a **Feature**. A whole repo with several separable
  areas is an **Epic** with one Feature per area, each untangled in turn. Council depth: Lite while
  the work stays inside existing modules; **Full council** as soon as a cluster would add, merge or
  move a module boundary, or change a data store or integration. The Feature's `zeno-ddd` framing
  is where the missing concepts behind special cases get their names.
- **Gate 2, Route** — the inventory goes in the Feature card's optional `## Findings` table
  (`zeno/references/feature-template.md`), not in another file. Clusters become the Story list;
  every Story is planned before Gate 3, as usual.
- **Gate 3, Execution** — each cluster's Tasks are **Behavior-preserving Tasks** in
  `zeno-workflow/zeno-tdd`: the pin test's RED is a deliberate break, not missing code. When fixing
  a needless link changes a public signature or a client-visible contract, write
  `BREAKING API CHANGE` per `zeno-stack/zeno-implementation-guardrails` and wait for authorization.
- **Gate 4, Review** — each Story closes with its own Proof and PR. The re-inventory Story's
  Proof records the stop rubric.

## The four phases

1. **Offer the optional passes, then inventory (read-only).** Ask whether to include the comment
   pass and the test pass; do only what the user picks. Then open a Feature card (zeno Gate 2
   bootstrap) and record every finding in its `## Findings` table: kind, location, evidence, and for
   each special case the requirement it seems to patch. Product files do not change in this phase. A special case whose
   purpose you can't establish from code or history is a question for the user, logged on the card
   — not an assumption either way.
2. **Redesign into clusters.** Group findings that one change would remove together: three special
   cases caused by one missing concept are one cluster, not three fixes. For each cluster write the
   intended design in a sentence, the findings it removes, and the behavior that must not change.
   Order clusters by how many findings each removes for its risk. Each cluster becomes a Story on
   the Feature's list (`zeno-workflow/zeno-fdd` ordering), and the list always ends with a
   **re-inventory Story** (phase 4), so the final check is planned work, not an afterthought. Gate 2
   planning for a cluster Story can be short but not empty: its acceptance criteria are "these
   findings are gone" and "this behavior is unchanged", each with a scenario. Show the inventory and
   clusters to the user and **wait for their go-ahead** (they may drop, merge or reorder clusters)
   before Gate 3 opens. Clusters touching money, auth or data
   correctness need the user's explicit choice where current behavior is ambiguous (for example two
   rounding rules — which one is right?).
3. **Fix one Story per cluster.** WIP limit 1. In Gate 3, first pin current behavior with tests that
   would fail if it changed (characterization tests where none exist), then make the change, keeping
   the suite green. A pinning test must itself be able to fail: break the behavior it pins, watch it
   go red, revert (the mutation check from `zeno-stack/zeno-test-prune`). Existing tests that can't
   fail don't count as pins, whether or not the user chose the test pass. Remove the special case by implementing the named requirement, not by moving the
   `if` somewhere tidier. A sleep or retry is removed only with a reproduced race and a real fix
   (idempotency, an awaited event, a lock); if that isn't possible within the Story, keep it and log
   it on the card as an open finding with its evidence. Each Story closes through Gate 4 with its
   own PR.
4. **Re-inventory and decide.** After the planned Stories close, run the inventory again over the
   same area — independently: a fresh pass (or a registry reviewer) that did not write the fixes.
   New or remaining findings become new clusters. A new cluster reopens Gate 2 for that cluster
   only (plan its Story fully, then Gate 3), or, if the user prefers, it goes to a follow-up Feature
   and the current one closes with it logged as open. Stop only when the stop rubric holds.

**Stop rubric** — the loop ends when all of these are true and recorded on the Feature card:
- No cluster remains whose findings outweigh its cost — judged by findings removed versus files and
  callers it would touch; when that is close, the user decides, and the decision is recorded.
- A typical change to the area lands in one place (check two or three recent real changes from `git log`).
- Every remaining special case is either a named requirement in code or an open finding with a reason and an owner.
- Behavior is unchanged except where the user chose otherwise; the full suite is green.
A deadline does not satisfy the rubric. If time runs out, stop at a Story boundary and report the
remaining clusters as open — never as done.

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "The user said no paperwork, so one quick card is enough" | The inventory *is* the work's definition. Keep cards short, but every finding goes on one, and each cluster is its own Story |
| "I know the problems already, the user listed them" | Listed smells are a sample. Read the whole area; the hidden links are the ones nobody mentioned |
| "These special cases are probably intentional, I'll keep them" | Maybe. Find the requirement in history or ask; then either name it in code or log it. Silently keeping and silently removing are both guesses |
| "I'll move each special case into a named rule and call it done" | Relocating an `if` keeps the coupling. Name the missing concept so the special case stops being special |
| "The sleep is risky, I'll leave it alone" | Leaving it can be right, but only as a logged open finding with evidence, not as silence |
| "Friday forces a stop" | A deadline ends work at a Story boundary; it doesn't make the area untangled. Report the remaining clusters as open |
| "It's faster to fix everything in one pass" | One pass is one huge diff nobody can review or revert. One Story per cluster keeps each change provable |

## Red flags — stop, you're bypassing the discipline

- You're editing a product file and the inventory isn't on a card.
- Your inventory only contains the smells the user mentioned.
- A cluster's Story has no test pinning current behavior and you're already changing code.
- You're keeping or removing a special case without having found or asked for its reason.
- You're about to say "done" because time ran out rather than because the stop rubric holds.
- The re-inventory is being done by the same pass that wrote the fixes, from memory.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Fixing as you read | Read-only inventory first, recorded on a Feature card |
| One fix per special case | Group findings into clusters one change removes; one Story per cluster |
| Moving an `if` into a helper | Name the missing requirement and implement it |
| Removing a sleep or retry blind | Reproduce the race and fix it properly, or log it as an open finding |
| Changing money/auth/data behavior silently | Pin it, show the ambiguity, let the user choose |
| One giant refactor PR | One PR per cluster Story, WIP 1 |
| Stopping on a deadline and calling it done | Stop at a Story boundary and report remaining clusters as open |
| Deleting dead code inline with structural changes | Hand surplus to `zeno-refactor-cleanup` |

## Pre-flight checklist — run before delivering any untangle phase

- [ ] The user started this via `/untangle` or an explicit request, and chose which optional passes to run.
- [ ] WIP limit 1 held; the tier (Feature, or Epic for several areas) and council depth (Full for any boundary change) are on the card.
- [ ] The inventory (kind, location, evidence, suspected requirement) was in the Feature card's `## Findings` table before any product file changed.
- [ ] The whole area was read, and dependency structure and change history were checked, not just the reported smells.
- [ ] Findings were grouped into clusters, each with a one-sentence design, its findings and its protected behavior; each cluster is a Story.
- [ ] The Feature's Story list ends with a re-inventory Story, and the user gave a go-ahead on the inventory and clusters before Gate 3.
- [ ] Ambiguous money/auth/data behavior was decided by the user, not by the agent.
- [ ] Each cluster Story pinned current behavior with tests that were shown to fail under a deliberate break, before changing code, and closed through Gate 4 with its own PR; public-contract changes were flagged `BREAKING API CHANGE` and authorized.
- [ ] Clusters found by the re-inventory reopened Gate 2 for themselves only, or moved to a follow-up Feature.
- [ ] Every special case kept is named in code or logged as an open finding with reason and owner.
- [ ] An independent re-inventory ran, and the stop rubric's four conditions are recorded on the card — or remaining clusters are reported as open.
