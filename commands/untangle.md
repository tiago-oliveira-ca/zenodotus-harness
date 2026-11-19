---
description: Untangle a codebase's coupling and special cases — inventory first, then one Story per cluster.
argument-hint: "[optional area or concern to focus on]"
disable-model-invocation: true
---

# /untangle

Runs only when you call it: an untangle touches a whole area of the codebase and spends real
budget, so it never starts on its own. The doctrine lives in `zeno-stack/zeno-untangle`; load it and
follow its four phases inside the zeno loop.

## Steps

0. **Open the zeno loop** — load `zeno` and `zeno-stack/zeno-untangle`. The leaf's *How it runs in
   the zeno loop* section says what each gate does: WIP 1, Feature or Epic sizing, council depth.
1. **Offer the optional passes** before anything else: a comment pass (`zeno-comment-analysis`) and a
   test pass (`zeno-test-prune`). Do only the ones the user picks.
2. **Inventory, read-only** — the area in `$ARGUMENTS`, or the whole repo. Record every finding
   (hidden link, needless link, surplus, special case) with its location and evidence on a Feature
   card's `## Findings` table. No product file changes in this phase.
3. **Redesign** — group findings into clusters where one change removes several; each cluster
   becomes a Story on the Feature's list. Show the inventory and the clusters to the user before
   Gate 3.
4. **Fix, one Story per cluster** — Gates 2-4 for each: pin current behavior with tests first, make
   the change, keep the suite green. Hand dead-code surplus to `zeno-refactor-cleanup`.
5. **Re-inventory** — an independent pass over the same area; stop only when the skill's stop
   rubric holds. New clusters reopen Gate 2 for themselves, or go to a follow-up Feature.
