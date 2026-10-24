---
description: Recommend the best model tier for the current task based on complexity, risk, and budget.
---

# /model-route

`/model-route [task-description] [--budget low|med|high]`

Picks the model tier that best fits the task at hand, weighing how complex and how risky it is
against the stated budget.

## Routing heuristic

Cross two axes — task **shape** and **risk** — rather than picking a tier off a flat list. Same
policy `agents/_agent-template.md` §4 already enforces for agent frontmatter; this command applies
it to ad hoc work that isn't going through a named agent.

| Shape | Read-only / advisory | Mutates code | Adversarial / unfamiliar repo |
|---|---|---|---|
| Mechanical, templated (generation from a fixed skeleton, classification against a known spec, comment-rot detection, doc/codemap regeneration) | `haiku` | `haiku` (with a `sonnet` spot-check on the diff if the change is non-trivial) | `sonnet` |
| Implementation / refactoring with a clear target shape | `sonnet` | `sonnet` | `opus` |
| Open-ended judgment (architecture decisions, ambiguous requirements, deep/adversarial review) | `opus` | `opus` | `opus` |

One concrete in-repo precedent this table generalizes, worth citing when the reasoning needs a
worked example rather than an abstract rule:
- `zeno-security-scan` risk-gates escalation instead of defaulting to the expensive tier: the
  static scan runs at the normal tier, and the `--opus` adversarial pass is reserved specifically
  "for higher-stakes onboarding" / "a new/unfamiliar repo" — escalate on risk signal, not by habit.

## Calibration — close the loop against actual spend

This table is a static heuristic; it can drift from reality if usage patterns shift. Periodically
cross-check it against `/cost-report`'s per-model breakdown: if the expensive-tier (`opus`) share
of spend is rising without a matching rise in adversarial/unfamiliar-repo or open-ended-judgment
work, the escalation criteria above — not the budget cap — need tightening, since that drift means
routine work is landing in the expensive cell by habit rather than by risk signal. This is the same
lever FrugalGPT/RouteLLM/Hybrid-LLM cascade research reports 40-98% cost reductions from: sending
only genuinely hard or risky work to the expensive tier, and re-checking that boundary against
measured outcomes rather than setting it once and trusting it forever.

## `--budget` is a ceiling, not a suggestion

`--budget low|med|high` caps the recommendation — it does not just get echoed back unused:

- `--budget low` — hard cap at `sonnet`, regardless of what the table says. Say so explicitly in
  the output ("table says `opus`; capped to `sonnet` by `--budget low` — expect a quality/cost
  tradeoff") rather than silently downgrading.
- `--budget med` (the default) — no cap; the shape/risk table's answer stands as-is.
- `--budget high` — no cap, and when a task sits on the boundary between two table cells, round up
  to the more capable tier rather than down.
- No `--budget` given — treat as `med`.

If the cap changes the answer from what the table alone would say, state both: the table's answer
and the capped answer, so the tradeoff is visible instead of silently absorbed.

## Output

Always return:

- the recommended model (post-cap)
- what the shape/risk table alone would have said, if `--budget` changed it
- a confidence level for that recommendation
- the reasoning behind the fit (name the shape and risk cell used)
- a fallback model to try if the first attempt doesn't land

## Arguments

$ARGUMENTS:
- `[task-description]` — optional free-text description of the task
- `--budget low|med|high` — optional, defaults to `med` (see above — this is an enforced ceiling,
  not a hint)
