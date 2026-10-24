# Project: <repo or feature name>

<!--
  Five principles this file is organized around — every other section is support material for
  one of these:
    State      — the current reality / starting point / where the problem begins.
    Goal       — the final outcome / success condition / target state (header field below).
    Decisions  — choices made to weigh alternatives, select paths, steer actions.
    Next step  — the immediate, tactical action executed from the present context.
    Proof      — the test, audit trail, or verification artifact confirming the path worked.
-->

**Goal:** <one sentence — the final outcome / success condition for this line of work>
**Status:** backlog | development | testing | closed
**Framework:** SAFe/Lean (Scrum + Kanban at team level)
**Program Increment:** PI-<n> — <objective — optional, omit if not meaningful at this scale>
**Sprint:** <n> — <goal — optional>
**Updated:** <YYYY-MM-DD>

## State
<2-4 lines: the current reality — where things stand right now. Overwrite each session.>

### Kanban board  (WIP limit: 1 item outside Backlog/Closed at a time)
| Backlog | Development | Testing | Closed |
|---|---|---|---|
| STORY-x | STORY-z | | STORY-w |

### Epics / Features
<!-- Epics are optional — only for genuinely epic-sized work. Small work may list a Story here
     directly with no parent Feature ("(ad hoc)"). Task/SubTask are optional at their own tier —
     most Stories need a Task list; only a Task still too big for one sitting needs SubTasks. -->
- [ ] EPIC-<slug> — <one-line goal> → `docs/epics/EPIC-<slug>.md`
  - [ ] FEAT-<slug> → `docs/features/FEAT-<slug>.md`
    - [ ] STORY-<slug> → `docs/stories/STORY-<slug>.md`
      - [ ] TASK-<slug> → `docs/tasks/TASK-<slug>.md`
        - [ ] SUBTASK-<slug> → `docs/subtasks/SUBTASK-<slug>.md`

## Decisions
- <YYYY-MM-DD> <decision + one-line why>   (append-only; newest last)

## Next step
<the single next concrete action — which item, which pipeline stage — the first thing to do on resume>

## Proof
- <YYYY-MM-DD> <item id> <what was exercised> → <observed result>   (rollup; append-only; full
  per-scenario evidence lives on the item's own Story card under `docs/stories/`)

## Open questions / parked
- <anything deferred, so it isn't lost across sessions>

## Outcome
<!-- Optional — the 2-3 line close-out written at Review when Status flips to closed. -->
<what shipped, and any follow-ups left open>
