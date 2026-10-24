---
name: zeno-comment-analysis
description: >
  Audit inline code comments for accuracy against the implementation, coverage of non-obvious
  logic, low-value restatement, staleness, and misleading claims — read-only, reports findings
  rather than rewriting comments. Trigger on: "check the comments", "comment rot", "are these
  comments accurate", "stale comments", "TODO/FIXME audit", "comment review".
---

# Comment Accuracy & Rot Audit

A comment is a claim about the code that the compiler never checks. Read each comment against the
code it describes and judge whether it's still true, still useful, and worth the maintenance
burden of keeping it true.

## What to check per comment

**Does it match the code it describes?** Read the comment's claim, then the implementation it's
attached to. Check parameter/return descriptions against what the function actually takes and
returns. Flag anything referencing a function, file, or behavior that no longer exists.

**Does it cover what actually needs explaining?** Complex or non-obvious logic should give a
reader enough context that they don't have to reverse-engineer intent from the code alone. Side
effects and edge cases not visible from the signature deserve a mention.

**Is it worth keeping as-is?** A comment that just restates the line below it in English adds
reading time without information — flag as low-value. A comment tightly coupled to
implementation details that change often will go stale fast. Surface `TODO`/`FIXME`/`HACK`
markers as unresolved debt worth tracking, not noise to skim past.

**Does it actively mislead?** The most damaging category — a comment that contradicts what the
code does is worse than no comment, because a reader trusts it by default.

## Output format

Group findings by severity, most damaging first:

- `Inaccurate` — actively contradicts the code
- `Stale` — describes something that no longer exists
- `Incomplete` — real logic/side-effects/edge-cases with no explanation
- `Low-value` — adds no information beyond what the code already says

For each finding: location, a one-line description of the gap, and — where it's a quick fix —
the corrected wording. This is read-only: propose corrected wording, don't rewrite comments in
place.

**Agent counterpart:** `agents/zeno-comment-analyzer.md` — the spawned standalone audit over this same taxonomy (this skill is its Codex fold home).

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Flagging every comment as equally important | Group by severity — inaccurate/misleading first |
| Rewriting comments directly during the audit | Report only; hand corrections to the human or the owning implementation work |
| Treating a TODO as noise to skip | Surface it as tracked debt |
| Auditing external docs (README, API reference) here | That's `documenting-code`'s domain, not this one |

## Pre-flight checklist — run before delivering any comment-accuracy report

- [ ] Every flagged comment names its category (`Inaccurate`/`Stale`/`Incomplete`/`Low-value`).
- [ ] Each finding has a location and a one-line gap description.
- [ ] Quick fixes include corrected wording, without editing the file directly.
- [ ] External/generated documentation drift was routed to `documenting-code`, not folded in here.
