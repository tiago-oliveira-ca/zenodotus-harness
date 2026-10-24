# Migrating into `.zeno/`

Two distinct migrations land here, both triggered by `zeno`'s Gate 2 step 5 — a legacy free-form
thread predating the backlog format entirely, and the pre-rename `.project/core.md` layout that
already had the backlog format, just under the old folder/file names. `zeno`'s Gate 2 (Route)
defines the target layout but not how to get either starting point there — these are that recipe,
so the next legacy repo migrates the same way instead of re-deriving the mapping from scratch.

## Recipe 1 — a legacy `THREAD.md` (or similar free-form log)

Some repos predate the `.zeno/` backlog format and carry a single `THREAD.md` (or a similarly
named free-form log) instead.

### The mapping

| Legacy content | Target |
|---|---|
| Each `## Frame` section | One Story card's Scope (Problem / Approach / Done looks like), moved verbatim |
| Plan checklists (M-steps / H-steps) | The parent Feature card's Story list, as checklist lines — **not** retroactive per-step Story, Task, or SubTask cards |
| Each dated Decisions/Proof-log entry | Moved verbatim to the one card that owns it; `project.md` keeps only a one-line rollup pointer |
| Unresolved Open-questions items | A Backlog Story card (if it's never-started work) or a `project.md` parked line (if it's a note, not a task) |
| Struck-through / resolved items | Dropped — their resolution already lives on the owning card and in git history |

### Rules

- **No retroactive per-step Story, Task, or SubTask cards.** Task and SubTask are legitimate card
  levels for *new* work still being decomposed — they are not a license to retroactively convert a
  finished checklist item-by-item into individual cards. Converting old checklist steps into
  Story/Task/SubTask cards fabricates dozens of cards for work that's already done; keep the
  checklist as Feature-list lines instead.
- **No fabricated ATDD/BDD.** Don't retroactively write Acceptance Criteria or Given/When/Then
  scenarios for stories that are already complete — leave a comment on the card noting that the
  real tests already captured in Proof serve as the scenario record.
- **Move history verbatim, don't re-summarize it.** The owning card should read as if it had
  produced that Decisions/Proof entry in the first place, not a paraphrase of the old thread.
- **Delete the legacy file at the end, but record the migration.** Once everything has a home,
  delete `THREAD.md` (or equivalent) and add one `project.md` Decisions entry recording the migration
  and the git ref/commit where the pre-migration text can still be found if needed.

## Recipe 2 — the pre-rename `.project/core.md` layout

A repo already on the backlog format, just under the old names (`.project/` instead of `.zeno/`,
`core.md` instead of `project.md`). The five-card-type model, the templates, and every card's own
content are unchanged by this rename — it's a mechanical move, not a content migration, so this
recipe is much shorter than Recipe 1's.

1. **Move the folder and the index file**, preserving git history:
   ```
   git mv .project .zeno
   git mv .zeno/core.md .zeno/project.md
   ```
   Every card under `docs/` moves with the folder automatically — their own relative path
   references (`../stories/STORY-<slug>.md` and similar) stay valid unchanged, since only the
   parent folder's name changed, not the structure beneath it.
2. **Rewrite `.zeno/project.md`'s own top heading** (`# Core: <name>` → `# Project: <name>`) to
   match — the content of every other section is untouched.
3. **Zero-broken-links check.** Grep the repo for any remaining `.project/` or bare `core.md`
   mention outside historical record (old `CHANGELOG.md` entries, already-archived cards' own
   prose) and fix it — a lingering reference to the old path is exactly the kind of drift Gate 4's
   own documentation check exists to catch.
4. **Record the migration** as one `project.md` Decisions entry — the commit that did the `git mv`
   is enough provenance; no separate migration log is needed the way Recipe 1's free-form thread
   needs one (there's no content transformation to explain, just a rename).

## Why

A format upgrade needs an explicit migration recipe, or every migrator invents a different one.
Recipe 1's core rule generalizes beyond its specific format: move history verbatim to the card
that would have produced it, and never fabricate ceremony the work never actually ran. Recipe 2
exists for the same reason at a smaller scale — even a mechanical rename deserves one written-down
recipe, not a different ad hoc `git mv` sequence invented per repo.
