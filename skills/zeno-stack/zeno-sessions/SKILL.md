---
name: zeno-sessions
description: >
  Save, resume, list, load, and alias session files that carry work context across sessions for
  repos with no tracked `.zeno/project.md` — plain markdown files and file reads, no external
  library or background service. For a repo with a tracked `.zeno/`, prefer that (`zeno`'s own
  State/Next-step) over this. Trigger on: "save this session", "resume my session", "list
  sessions", "alias this session", "load session by date".
---

# Session Save / Resume / List / Alias

Carry work context across sessions for a repo that has no tracked `.zeno/project.md` backlog —
for a zeno-governed repo, prefer `zeno`'s own State/Decisions/Next-step over this instead.

**This skill is the lane's contract owner:** the filename convention, section format, and alias store defined here are what `/save-session`, `/resume-session`, and `/sessions` implement — on a conflict, this file wins, and contract changes land here first, then in the commands.

## Save a session

Write a dated markdown file (`YYYY-MM-DD-<short-id>-session.tmp`) capturing enough for a future
session to resume cold: a header (`**Project:**`, `**Topic:**`, `**Started:**`, `**Last
Updated:**`), what was done, decisions made and why, current state, and the next concrete step.
Confirm the write with the user before ending the session.

## Resume a session

Read the resolved file in full, then brief the user: what was in progress, what decisions are
already made (don't re-litigate them), and the next concrete step — pick up cold, not from
scratch.

## List sessions

List session files newest-first; for each, pull `Project`/`Topic`/`Started` from its header
rather than reading the whole file, apply date/search/limit filters, and print a compact table:
id / date / project / topic. Join in any alias whose target matches the filename.

## Load a session

Resolve an id/alias/date argument: check the alias file first; otherwise treat the argument as a
date (most recently modified match) or a filename/id fragment. Read the resolved file in full and
follow the resume briefing format from there.

## Alias a session

Aliases live in one JSON file (`{"<name>": "<session filename>"}`), created on first use. To set
one: resolve the id to a real filename the way `load` does, then add/update the key and write
back. To remove one: read, delete the key if present (report clearly if it wasn't there), write
back.

## Session info

Report metadata only (filename, resolved path, date, last-modified time, file size, any aliases
pointing at it, header fields) — unlike `load`, this does not read or brief the full content.

## Notes

- Both the legacy no-id filename and the current short-id form are valid and get listed together.
- If no session directory exists yet, say so plainly and point at how to save one — don't error.
- Sessions are plain markdown; this only lists/aliases/locates them, never edits their content.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Using this for a repo with a tracked `.zeno/project.md` | Prefer `zeno`'s own State/Next-step there instead |
| Reading every session file in full just to build a list | Pull header fields only (`Project`/`Topic`/`Started`) for listing |
| Editing session file content from this skill | Read-only over content; only aliasing/metadata are mutated |
| Erroring when no session directory exists yet | Say so plainly, point at how to save one |

## Pre-flight checklist — run before delivering any session save/resume/list/alias action

- [ ] Save: header fields present, decisions and next step captured, write confirmed with the user.
- [ ] Resume: full file read before briefing; briefing states what's already decided and the next step.
- [ ] List/info: header-only reads used for listing, not full-file reads.
- [ ] Alias mutations write back the whole JSON file, not a partial edit.
- [ ] Missing session directory/file handled with a plain message, not an error.
