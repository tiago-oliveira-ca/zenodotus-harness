---
name: zeno-debug
description: >
  The root-cause-first debugging discipline for the zeno loop's Execution gate. When something is
  broken, failing, or behaving unexpectedly, investigate the cause before attempting any fix.
  Four phases: investigate (read the real error, reproduce reliably, trace data flow backward),
  pattern-analysis (diff broken vs a known-good reference), hypothesis-and-test (one variable at
  a time), then fix (reproducing test first, one targeted change). If each fix reveals a new
  failure elsewhere, stop patching — the design is wrong. Trigger on: "debug this", "why is
  this failing", "why doesn't this work", "root cause", "unexpected behavior", "stack trace",
  "reproduce the bug", "it's broken", "diagnose", "this used to work", "trace the error".
---

# Zeno Debug — no fix without a root cause

This is the diagnosis discipline of the Execution gate. Guessing at fixes is how a one-line bug turns
into an afternoon of shotgun edits that each break something new. Find the cause first, then make
one targeted change.

**Iron Law: NO FIX WITHOUT A ROOT-CAUSE INVESTIGATION FIRST.** If you're about to change code and
you cannot state *why* the bug happens in one sentence ("it fails because X"), you are not ready to
fix it — you're guessing.

## Phase 1 — Investigate

- **Read the actual error.** The full message, the full stack trace, the exit code — not a
  paraphrase, not the last line only.
- **Reproduce it reliably.** A bug you can't trigger on demand can't be verified fixed. Find the
  minimal, repeatable trigger before touching anything.
- **Check what changed.** Recent diffs, new dependencies, config/env changes. "This used to work"
  means something moved — find it (`git log`, `git diff`).
- **Trace the data flow backward.** Start at the symptom and walk *upstream* to where the bad
  value/state originates. The fix belongs at the origin, not the symptom. When a graph exists, use
  `graphify path`/`query` to trace callers/dependencies instead of manual grep
  (`zeno/references/impact-analysis.md`).

## Phase 2 — Pattern analysis

Diff the broken case against a known-good reference: a passing test, a working sibling function, an
earlier commit that worked. The delta between broken and working is where the cause lives.

## Phase 3 — Hypothesis and test

State a falsifiable hypothesis: *"I believe X because Y."* Test **one variable at a time** — change
one thing, observe, revert if it wasn't it. Never change three things and declare victory; you won't
know which one mattered (and one of the other two may have introduced a new bug).

## Keeping a long investigation lean

Stack traces, `git log`/`diff` output, and rounds of grep/read pile up fast across Phases 1-3.
Don't let it sit unprocessed: after roughly every 5 tool calls, or at each phase transition,
write a running note to the active card's Decisions log — what's ruled in/out, and why — before
continuing. Treat that note as the record: recall from it, not by re-reading old tool output.
This recency + rolling-summary pattern outperformed both full-history and recency-only context
management on long-horizon tool-use tasks (Lodha et al., *Less Context, Better Agents*,
arXiv:2606.10209: 91.6% task completion vs. 71%/79%, ~3x fewer tokens than full history).

## Phase 4 — Fix (hand back to zeno-workflow/zeno-tdd)

Only once the cause is known: write a **failing test that reproduces the bug** (per `zeno-workflow/zeno-tdd`),
watch it fail, then make **one targeted change** at the origin. Watch the test pass. Record the root
cause in the active card's Decisions log so it isn't re-diagnosed later.

## The architectural-breakdown signal

If every fix reveals a new failure somewhere else — you fix A and B breaks, you fix B and C breaks —
**stop patching.** That cascade means the design is wrong, not that you have many small bugs. Escalate
to Scope (`zeno-insight`): the structure needs rethinking, not another patch.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Changing code before you can state the cause | Investigate until "it fails because X" is one sentence |
| Reading only the last line of the error | Read the full message, stack, and exit code |
| Fixing at the symptom | Trace backward to the origin and fix there |
| Changing several things at once | One variable at a time; revert what wasn't it |
| Declaring it fixed without reproducing first | Reproduce reliably before *and* after the fix |
| Patching an endless cascade of new failures | Recognize the architectural-breakdown signal; return to Scope |
| Fixing a bug with no reproducing test | Write the failing test first (`zeno-workflow/zeno-tdd`) |
| Re-reading old tool output instead of your running note | Roll up findings every ~5 calls; trust the note, not re-derivation |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "It's an obvious one-liner, I'll just change it" | If it's obvious, stating the cause costs one sentence — do that first |
| "I don't have time to reproduce it" | A fix you can't verify is a guess; you'll spend longer re-opening it |
| "The error is probably the same as last time" | Read *this* error; "probably" is how you fix the wrong thing |
| "Let me just try a few things" | Shotgun edits mask the cause and add new bugs; one hypothesis at a time |

## Red flags — stop before you edit

- You're reaching for the editor and can't say why the bug happens.
- You're about to change more than one thing "to be safe."
- You haven't reproduced the failure yet.
- You've fixed the same area three times and it keeps breaking elsewhere.

## Pre-flight checklist — run before delivering any debug fix

- [ ] The root cause is stated in one sentence and recorded in the active card's Decisions log.
- [ ] The bug was reproduced reliably before the fix.
- [ ] A failing test reproducing the bug was written first (`zeno-workflow/zeno-tdd`) and now passes.
- [ ] Exactly one targeted change was made at the origin, not the symptom.
- [ ] No cascade of new failures — or, if there was one, it was escalated to Scope as a design issue.
