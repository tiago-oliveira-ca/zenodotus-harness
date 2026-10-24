---
description: List, load, and alias saved session files in ~/.claude/session-data/ — the companion to /save-session and /resume-session.
---

# Sessions Command

> **Contract owner:** the `zeno-stack/zeno-sessions` skill defines this lane's shared contract — filename convention, section format, alias store, and the prefer-`.zeno/`-when-tracked rule. The three session commands implement that contract; on a conflict, the skill wins.

Manage the session files that `/save-session` writes and `/resume-session` reads — list what's
there, load one by id/alias/date, and give frequently-used ones a memorable name. Everything here
runs with plain shell commands and file reads — no external library, no background service.

## Usage

```text
/sessions [list|load|alias|unalias|info|aliases] [options]
```

## List sessions

```bash
/sessions                          # same as: /sessions list
/sessions list --limit 10
/sessions list --date 2026-02-01
/sessions list --search abc
```

List `~/.claude/session-data/*-session.tmp` (and, for older files, `~/.claude/sessions/*-session.tmp`),
newest first:

```bash
ls -t ~/.claude/session-data/*-session.tmp ~/.claude/sessions/*-session.tmp 2>/dev/null
```

For each file, pull `**Project:**`, `**Topic:**`, and `**Started:**` from its header (`grep -m1`
each field) rather than reading the whole file, apply `--date`/`--search`/`--limit` as plain
filters over that file list, and print a table: id (filename minus the `-session.tmp` suffix,
truncated to what fits) / date / project / topic. If `~/.claude/session-aliases.json` exists, join
in any alias whose target matches the filename.

## Load a session

```bash
/sessions load <id|alias>
/sessions load 2026-02-01          # most recent session for that date
```

Resolve `<id|alias>`: check `~/.claude/session-aliases.json` for a matching alias first: if found,
use its target filename. Otherwise treat the argument as a date (find the most recently modified
matching file for that date) or a filename/id fragment (match against the listing above). Read the
resolved file in full and follow `/resume-session`'s briefing format from there — this command
finds and hands off; `/resume-session` is what absorbs and briefs.

## Alias a session

```bash
/sessions alias <id> <name>          # create
/sessions alias --remove <name>      # remove
/sessions unalias <name>             # same as --remove
/sessions aliases                    # list all
```

Aliases live in one JSON file, `~/.claude/session-aliases.json` — `{"<name>": "<session filename>"}` —
created on first use if absent. To set one: resolve `<id>` to a real filename the way `load` does,
then read the JSON, add/update the `<name>` key, and write it back. To remove one: read, delete the
key if present (report clearly if it wasn't there), write back. `/sessions aliases` just prints the
file's contents as a name → filename table.

## Session info

```bash
/sessions info <id|alias>
```

Resolve the same way `load` does, then report: filename, resolved path, date (from the filename),
last-modified time (`stat`), file size, any aliases pointing at it (reverse-lookup the alias JSON),
and the header fields (`Project`/`Topic`/`Started`/`Last Updated`) pulled the same way `list` does.
Unlike `load`, this reports metadata only — it does not read or brief the full content.

## Notes

- Sessions are markdown files written by `/save-session`; this command only lists/aliases/locates
  them, it never edits session content.
- The legacy no-id filename (`YYYY-MM-DD-session.tmp`) and the current short-id form
  (`YYYY-MM-DD-<short-id>-session.tmp`) are both valid and both get listed.
- If neither `~/.claude/session-data/` nor `~/.claude/sessions/` exists yet, say so plainly and
  point at `/save-session` rather than erroring.

## Related

- `/save-session` — writes the files this command lists.
- `/resume-session` — the full briefing flow once a session file is found; `/sessions load`
  resolves *which* file, then hands off to the same briefing format.
- `/zeno status` / `/zeno resume` — the `.zeno/`-backed equivalent for zeno-governed repos;
  prefer these over `/sessions` when the repo has a tracked `.zeno/project.md`.

## Arguments

$ARGUMENTS:
- `list [options]` — `--limit <n>` (default 50), `--date <YYYY-MM-DD>`, `--search <pattern>`
- `load <id|alias>`
- `alias <id> <name>` / `alias --remove <name>` / `unalias <name>`
- `info <id|alias>`
- `aliases`
