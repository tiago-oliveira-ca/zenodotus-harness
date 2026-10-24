---
description: Create, verify, list, or clear workflow checkpoints after running verification checks.
---

# /checkpoint

`/checkpoint [create|verify|list|clear] [name]`

Marks a known-good point in a workflow so later work can be compared back against it — before a
risky change, between implementation and refactor, or ahead of opening a PR.

## Create

1. Run the project's own test/lint command first (per the `zeno-verify` skill's
   run-the-proving-command discipline), so the checkpoint is only recorded from a clean state.
2. Record the checkpoint as a git stash or commit named after it.
3. Append a line to `.claude/checkpoints.log`:

```bash
echo "$(date +%Y-%m-%d-%H:%M) | $CHECKPOINT_NAME | $(git rev-parse --short HEAD)" >> .claude/checkpoints.log
```

4. Confirm to the user that the checkpoint was created.

## Verify

1. Look up the named checkpoint in the log.
2. Diff current state against it:
   - files added since
   - files modified since
   - test pass rate then vs. now
   - coverage then vs. now
3. Report the comparison:

```
CHECKPOINT COMPARISON: $NAME
============================
Files changed: X
Tests: +Y passed / -Z failed
Coverage: +X% / -Y%
Build: [PASS/FAIL]
```

## List

Show every recorded checkpoint with its name, timestamp, git SHA, and status relative to the
current HEAD (current / behind / ahead).

## Clear

Trim `.claude/checkpoints.log` to the 5 most recent entries — old checkpoints from finished work
accumulate and make `list` noisy, but the log itself (and any git stashes/commits it points at)
isn't something to prune aggressively, so this only trims the log's tail, and never touches the
underlying git history:

```bash
tail -n 5 .claude/checkpoints.log > .claude/checkpoints.log.tmp && mv .claude/checkpoints.log.tmp .claude/checkpoints.log
```

Report how many entries were dropped and which 5 remain.

## Typical flow

Checkpoints usually bracket the stages of a change:

```
[Start] --> /checkpoint create "feature-start"
   |
[Implement] --> /checkpoint create "core-done"
   |
[Test] --> /checkpoint verify "core-done"
   |
[Refactor] --> /checkpoint create "refactor-done"
   |
[PR] --> /checkpoint verify "feature-start"
```

## Arguments

$ARGUMENTS:
- `create <name>` — create a named checkpoint
- `verify <name>` — verify current state against a named checkpoint
- `list` — show all checkpoints
- `clear` — remove old checkpoints (keeps the last 5)
