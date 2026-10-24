---
name: zeno-config-gc
description: >
  Garbage collection for the Claude Code configuration under ~/.claude — scans skills,
  memory, hooks, permissions, MCP servers, and caches for redundant, stale, or orphaned
  items, then walks through a confirm-each-item cleanup with soft-delete and an undo log.
  Never deletes autonomously. Use for periodic config review or when the setup feels
  bloated. Trigger on: "clean up my config", "config GC", "too many skills", "audit my
  setup", "my .claude is bloated", or a periodic config review.
---

# Config GC — Garbage Collection for Claude Code Setups

Borrows the runtime-GC idea — periodically scan for objects no longer referenced,
redundant, expired, or low-value, and reclaim the space — with one deliberate difference:
**collection always requires a human in the loop. Never delete autonomously.**

## When to activate

- The user asks to clean up, audit, or slim down their Claude Code configuration.
- Complaints about too many skills, noisy hooks, or slow session startup.
- A periodic (roughly monthly) config review is due.
- After installing a large skill pack, to reconcile overlaps with the existing setup.

Not for: cleaning project source code (that's refactoring), clearing chat history, or
uninstalling Claude Code itself.

## Design philosophy

1. **Append-only configs leak.** Skills, memory files, hooks, and permission entries only
   ever accumulate. Without periodic review they rot silently.
2. **Regular audits beat one-time purges.** Scan roughly every 30 days, propose a small
   batch of candidates each time — GC is periodic, not exhaustive.
3. **Per-channel strategies.** Each accumulation type has its own staleness signal; one
   rule doesn't fit all of them.
4. **Soft-delete first.** `.disabled` rename → `~/.claude/_gc_trash/` move → hard delete,
   in that order. Always keep an undo path.
5. **Forced human-in-the-loop.** Every candidate gets its own `[y/n/skip]` confirmation —
   no "yes to all."
6. **Keep a log.** Every run appends to `~/.claude/gc_log.md`: what was touched, why, and
   how to undo it.

## Scan channels

| # | Channel | Path | Staleness / redundancy signals |
|---|---|---|---|
| 1 | Skills | `~/.claude/skills/*/` | Overlapping names; never triggered in recent transcripts; domain mismatch with actual work; broken/empty SKILL.md |
| 2 | Memory | `~/.claude/**/memory/*.md` + index | Multiple index entries for one topic; content contradicting newer entries; dates already passed; orphan files missing from the index; sub-100-word fragments that should merge |
| 3 | Hooks | `~/.claude/hooks/` + settings | Scripts on disk referenced by no hook config; old versions superseded by rewrites |
| 4 | Permissions | `permissions.allow` in `settings.json`/`settings.local.json` | Duplicate entries; specific entries already covered by a wildcard; one-off grants from past experiments |
| 5 | MCP servers | `~/.claude.json` or project `.mcp.json` | Servers that fail to connect; functional duplicates; long-unused |
| 6 | Scheduled jobs | wherever the user keeps them | Fired one-shots older than 30 days; jobs whose target scripts no longer exist |
| 7 | Project history | `~/.claude/projects/*/` | Stale handoff snapshots; session records superseded by newer state |
| 8 | Runtime caches | `cache/`, `file-history/`, `logs/`, `shell-snapshots/` | Sort by size/mtime; propose items >30 days old and large |

## Workflow

1. **Scan** all channels (or the subset named) — collect path, channel, triggering
   signal, size, last-modified for each candidate.
2. **Rank** by confidence — broken/orphaned is high confidence, merely-old is low. Present
   as a numbered table, capped at ~20 candidates per run.
3. **Confirm one by one.** Show evidence per candidate, ask `[y/n/skip]`. The user can
   stop at any point.
4. **Close the reference graph before removing anything.** Components form workflow
   clusters (skill → command → agent chains expressed only in prose), so per-item relevance
   scoring can't see the dependency: it keeps the endpoints and deletes the middles. Grep the
   *surviving* set for inbound references to each removal candidate; a non-zero count means
   either keep it or remove its referrers in the same pass. Removals create new orphans, so
   re-run the sweep after every removal round until no dangling references remain — a single
   pass cannot converge. Also verify any safety net's *directionality* first: a `--delete`
   mirror propagates deletions on the next sync and protects nothing; only a dated snapshot
   protects destructive work.
5. **Soft-delete confirmed items** — `.disabled` rename for skills/hooks;
   `_gc_trash/<date>/` move for files. Permission entries (no comments possible in JSON):
   back up the settings file, log the removed entry verbatim, then remove it with `jq`.
   Hard-delete only when the user explicitly asks.
6. **Log** the run to `~/.claude/gc_log.md`: timestamp, items actioned, undo instructions.
7. **Report** reclaimed size, channels still healthy, suggested next review date.

## Example scan/action commands

Orphaned hook scripts (channel 3):

```bash
for f in ~/.claude/hooks/*; do
  name=$(basename "$f")
  grep -rq "$name" ~/.claude/settings.json ~/.claude/settings.local.json 2>/dev/null \
    || echo "ORPHAN: $f"
done
```

Redundant permission entries (channel 4) — duplicates, and specific grants shadowed by a
wildcard:

**Find the file that actually holds the entries first — do not assume.** Permissions may live in
`settings.json`, `settings.local.json`, or a project's `.claude/settings.json`, and on this
install they are in `settings.json` while `settings.local.json` holds only hook registrations.
Running these against the wrong file yields `jq: error: Cannot iterate over null` (exit 5).

```bash
# 1. locate it
for f in ~/.claude/settings.json ~/.claude/settings.local.json ./.claude/settings.json; do
  [ -f "$f" ] && printf '%s: %s entries\n' "$f" "$(jq '(.permissions.allow // []) | length' "$f")"
done

# 2. audit whichever file reported a non-zero count (substitute it for $SETTINGS)
SETTINGS=~/.claude/settings.json
jq -r '(.permissions.allow // [])[]' "$SETTINGS" | sort | uniq -d
if jq -e '(.permissions.allow // []) | index("Bash(*)")' "$SETTINGS" >/dev/null; then
  jq -r '(.permissions.allow // [])[]' "$SETTINGS" | grep '^Bash(' | grep -vF 'Bash(*)'
fi
```

Largest stale caches (channel 8) — `du -k` instead of GNU-only `find -printf`, so it works
on macOS/BSD too:

```bash
find ~/.claude/file-history ~/.claude/shell-snapshots -type f -mtime +30 \
  -exec du -k {} + 2>/dev/null | sort -rn | head -20
```

Soft-delete with undo path (capture the date once so the log can't disagree with the
directory):

```bash
gc_date=$(date +%Y-%m-%d)
mkdir -p ~/.claude/_gc_trash/$gc_date
mv ~/.claude/skills/dead-skill ~/.claude/_gc_trash/$gc_date/
echo "$(date -Iseconds) moved skills/dead-skill -> _gc_trash/$gc_date/ (undo: mv back)" >> ~/.claude/gc_log.md
```

Removing a confirmed-redundant permission entry (back up, log, then edit):

**Never redirect `jq` output into the file it is reading, even via a `.bak`.** The shell truncates
the target to 0 bytes *before* `jq` runs, so a filter error (or a missing key) leaves the live file
empty — on a settings file that silently unregisters every hook. Write to a temp file, verify it
parses, then move it into place:

```bash
SETTINGS=~/.claude/settings.json        # the file located above, not assumed
ENTRY='Bash(git push)'

cp "$SETTINGS" "$SETTINGS.bak"
tmp=$(mktemp)
if jq --arg e "$ENTRY" '.permissions.allow -= [$e]' "$SETTINGS" > "$tmp" && jq -e . "$tmp" >/dev/null; then
  mv "$tmp" "$SETTINGS"
  echo "$(date -Iseconds) removed permission entry: $ENTRY (undo: restore $SETTINGS.bak or re-add)" >> ~/.claude/gc_log.md
else
  rm -f "$tmp"
  echo "jq filter failed — $SETTINGS left untouched" >&2
fi
```

## Best practices

Run after big additions, not just on a calendar — installing a large skill pack is exactly
when overlap with existing skills appears. When two skills overlap, disable the one with
the weaker trigger description; it's the one that was probably never firing anyway.
Permission cleanup is the highest-value channel per minute spent — redundant allow-entries
make security review harder. Keep `gc_log.md` forever; it's tiny, and "when did I disable
that hook and why" comes up more than expected.

## Related skills

`zeno-skill-stocktake` audits skill *quality* — run it on whatever survives GC.
`zeno-context-budget` measures per-component token overhead and feeds targets to GC.
`zeno-skill-scout` is the subtractive lifecycle's counterpart on the acquisition side —
check before adopting anything external. `zeno-security-scan` pairs well with the
permissions channel.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| "Delete all 15? [y/n]" bulk approval | One candidate, one decision, every time |
| Hard-deleting on the first pass | Soft-delete (`.disabled` / `_gc_trash/`) first, always |
| Treating "old" as "dead" | Age is a signal, not a verdict — a human confirms |
| Truncating one side to resolve conflicting memory files | Read both, keep the newer truth, merge deliberately |
| Wandering into project source trees | Config GC stays inside `~/.claude` (or project `.claude/`) only |
| Skipping the log entry for a deletion | Every action gets a `gc_log.md` line with an undo path |
| Pruning by per-item relevance alone | Check inbound references from the surviving set; iterate until the reference graph closes |
| Trusting a mechanism named "backup" before destructive work | Verify directionality: a `--delete` mirror propagates deletions; only a dated snapshot protects |

**Before any settings edit:** confirm the target file actually contains the key you are filtering
(`jq -e '.permissions.allow' "$SETTINGS"`), and never write `jq` output directly over its own input.

## Pre-flight checklist — run before delivering any config-gc report

- [ ] Every deletion candidate was confirmed individually — no bulk "yes to all"
- [ ] Every action taken was soft-delete (rename/move) unless the user explicitly asked for hard delete
- [ ] `gc_log.md` has a timestamped entry with an undo path for every action taken
- [ ] No action touched anything outside `~/.claude` or the project's `.claude/`
- [ ] The report states reclaimed size, healthy channels, and a suggested next review date
- [ ] Permission-entry removals were backed up before editing the settings file
- [ ] Every removed item was grepped for inbound references from the surviving set, and the sweep re-ran after each removal round until the graph closed
- [ ] Any backup relied on before destructive work was verified to be a dated snapshot, not a converging mirror
