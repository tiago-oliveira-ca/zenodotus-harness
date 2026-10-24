---
name: zeno-harness-optimizer
description: >
  Tune the agent harness itself — hooks, model/tool routing, permissions, context budget, eval
  coverage — for reliability, cost, and throughput, measured before and after every change via
  `/harness-audit`. Never touches application/product code. Trigger on: "improve the harness",
  "tune the config", "harness is slow", "reduce context overhead", "audit the harness", "hook
  isn't firing", "permission prompts are excessive".
---

# Harness Reliability, Cost & Throughput Tuning

Tune the harness — hooks, routing, permissions, context budget — never the product code running
inside it. If a fix requires editing application source, hand it back rather than reaching past
the harness boundary.

## Approach

**Measure before changing anything.** Run `/harness-audit` and treat its scorecard as the
baseline — every proposed change must be justified against a specific number on that scorecard,
not a general sense that something looks off.

**Pick leverage, not busywork.** From the audit, identify the handful of areas (hooks, eval
coverage, model/tool routing, context budget, permission/safety configuration) where a change
would move the score the most, and work those first.

**Change the minimum that proves the point.** Prefer the smallest edit that plausibly produces the
improvement, easy to revert if it doesn't. Resist bundling multiple unrelated changes into one
pass — each change should be attributable to a specific delta.

**Re-run the same audit after applying changes.** A configuration change without a before/after
comparison is a guess wearing the shape of an improvement. Confirm the scorecard moved, and in the
expected direction — catch a change that helps one metric while regressing another here, not
later.

## Constraints

- No shell quoting that only works on one platform — hooks/scripts must survive across shells.
- Preserve compatibility with every harness this configuration is shared across, not just one.
- Favor changes with a specific, measured effect over speculative "best practice" edits.

## Reporting back

Always report four things: the baseline scorecard, exactly what changed and why, the re-measured
scorecard showing the delta, and any risk knowingly left open (a partial fix, a tradeoff, a
decision needing a human).

**Agent counterpart:** `agents/zeno-harness-optimizer.md` — same name, same loop, as a spawned end-to-end pass (this skill is its Codex fold home). Inline tuning → this skill; dedicated optimization run → the agent.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Changing config from a general sense something's off | Run `/harness-audit` first; justify every change against a specific number |
| A dozen cosmetic tweaks in one pass | Pick the highest-leverage area(s); one attributable change at a time |
| Declaring victory without re-measuring | Re-run the same audit; confirm the scorecard moved as expected, nothing else regressed |
| Editing product/application code to "fix" the harness | Out of scope — hand back to the human or the relevant product specialist |

## Pre-flight checklist — run before delivering any harness change

- [ ] Baseline `/harness-audit` scorecard captured before the first edit.
- [ ] Each change attributable to a specific scorecard number, not a vibe.
- [ ] One attributable change at a time — not bundled.
- [ ] Shell/script changes are portable across the harnesses this config is shared with.
- [ ] `/harness-audit` re-run after the change; delta reported alongside any residual risk.
- [ ] No product/application code was touched.
