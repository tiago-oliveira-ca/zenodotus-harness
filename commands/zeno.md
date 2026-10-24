---
description: Run the zeno loop for this repo — start / resume / status / review against ./.zeno/project.md
argument-hint: "[start | resume | status | review]"
---

# /zeno

Entry point and thread tracker for the **zeno** four-gate loop (Scope → Route → Execution →
Review), run against a single repo-root `.zeno/` folder.

**This command dispatches; it does not define.** Every gate definition, write-discipline rule,
sizing decision and card format lives in the `zeno` skill — load it. This file deliberately keeps
no second copy of those rules: a duplicate drifts from the skill and contradicts it.

## Resolving the project folder

Resolve the repo root with `git rev-parse --show-toplevel` (fallback: `pwd`) and read/write
`<root>/.zeno/`. One `.zeno/` folder per repo, at the root, committed with the repo.

## Dispatch — on the first token of `$ARGUMENTS`

| Token | Dispatches to |
|---|---|
| `start` (or no argument, no `./.zeno/project.md`) | The skill's **Gate 1 → Gate 2** path: migrate any legacy layout first (both recipes in `zeno/references/migration.md` — the `THREAD.md` thread *and* the pre-rename `.project/core.md`), then Scope (`zeno-council`, then `zeno-insight`), then Route — which fully plans the backlog (Story list, then every Story's acceptance criteria, scenarios and Task breakdown) **before** Gate 3 opens. Stop there and await go-ahead. |
| `resume` (or no argument, `./.zeno/project.md` exists) | Read `project.md`'s Kanban board, find the single item outside Backlog/Closed, print Goal / State / Next step plus that item's card, and re-enter at the stage the card's own content shows (which section is still empty). Do **not** re-Scope unless the Goal changed. Nothing in flight → reconcile against `git log`, print status, offer the Backlog. |
| `status` | Read-only. Print the Kanban board, counts by column, the active item and its stage, its last Decision and last Proof entry. Make no edits. |
| `review` | The skill's **Gate 4** via `zeno-verify`: exercise the change, record evidence on the closing card's Proof section, and close only if the evidence confirms it — then run that gate's finish tail (CHANGELOG entry, documentation check, verified merge before archiving). |

## What this command owns

Only the dispatch above and the folder resolution. For everything else — the gate contents, the
sizing ladder, `Status` vocabulary, append-vs-overwrite discipline, the card types and the
`docs/archive/` layout, WIP limits, and what `start`/`review` must never skip — the `zeno` skill
is authoritative. If this file and the skill ever disagree, the skill wins and this file is the
bug.
