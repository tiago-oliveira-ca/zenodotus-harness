# Project: <repo or feature name>

<!--
  Five principles this file is organized around — every other section is support material for
  one of these:
    State      — the current reality / starting point / where the problem begins.
    Goal       — the final outcome / success condition / target state (header field below).
    Decisions  — choices made to weigh alternatives, select paths, steer actions.
    Next step  — the immediate, tactical action executed from the present context.
    Proof      — the test, audit trail, or verification artifact confirming the path worked.

  READ-PATH BUDGET. Every resume reads this file, so it holds what is open and what is next,
  never history. `check_lifecycle.py .zeno/project.md` fails when any of these is exceeded:
    file ≤ 24 KB · State prose ≤ 5 lines · Next step ≤ 3 lines · Decisions ≤ 10 entries ·
    Proof ≤ 10 entries · no closed rows in Epics / Features · no card ids in the Closed column.
  Overflow moves (verbatim, oldest first) to `docs/archive/core-history.md` at card close.
  Detail lives on the card where it happened; this file carries one line and a pointer.
-->

**Goal:** <one sentence — the final outcome / success condition for this line of work>
**Status:** backlog | development | testing | closed
**Framework:** SAFe/Lean (Scrum + Kanban at team level)
**Program Increment:** PI-<n> — <objective — optional, omit if not meaningful at this scale>
**Sprint:** <n> — <goal — optional>
**Updated:** <YYYY-MM-DD>

## State
<≤5 lines, overwritten each session — never stacked: branch/PR, active item, what is true now.
 What happened before belongs on the closed card and in core-history.md, not here.>

### Kanban board  (WIP limit: 1 item outside Backlog/Closed at a time)
| Backlog | Development | Testing | Closed |
|---|---|---|---|
| STORY-x | STORY-z | | <count> → `docs/archive/core-history.md` |

### Epics / Features
<!-- Open items only. Epics are optional — only for genuinely epic-sized work. Small work may
     list a Story here directly with no parent Feature ("(ad hoc)"). Task/SubTask are optional at
     their own tier — most Stories need a Task list; only a Task still too big for one sitting
     needs SubTasks. When an item closes, move its line to core-history.md. -->
- [ ] EPIC-<slug> — <one-line goal> → `docs/epics/EPIC-<slug>.md`
  - [ ] FEAT-<slug> → `docs/features/FEAT-<slug>.md`
    - [ ] STORY-<slug> → `docs/stories/STORY-<slug>.md`
      - [ ] TASK-<slug> → `docs/tasks/TASK-<slug>.md`
        - [ ] SUBTASK-<slug> → `docs/subtasks/SUBTASK-<slug>.md`

## Decisions
- <YYYY-MM-DD> <portfolio-level decision + one-line why>   (newest 10; card-local decisions
  stay on their card; older entries move to core-history.md)

## Next step
<≤3 lines: the single next concrete action — which item, which pipeline stage>

## Proof
- <YYYY-MM-DD> <item id> closed → <PR/commit> · <card path>#Proof   (one line per closed
  top-level item, newest 10; evidence itself stays on the card per
  `zeno/references/evidence-contract.md`; older lines move to core-history.md)

## Open questions / parked
- <deferred question or finding> — Owner: <who decides>; Next action: <concrete follow-up>; Revisit: <date or trigger>

## Outcome
<!-- Optional — the 2-3 line close-out written at Review when Status flips to closed. -->
<what shipped, and any follow-ups left open>
