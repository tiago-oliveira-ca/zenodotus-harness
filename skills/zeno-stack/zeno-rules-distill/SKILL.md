---
name: zeno-rules-distill
description: >
  Scans the skill library for cross-cutting principles that appear in multiple skills, and
  distills them into `CLAUDE.md` — appending to an existing section, revising outdated wording, or
  proposing a new section. Applies "deterministic collection, LLM judgment": exhaustive scripted
  scanning first, then contextual cross-reading to produce verdicts. Never edits `CLAUDE.md`
  without explicit per-candidate approval. Trigger on: "distill rules from skills", "what
  principles should be promoted to CLAUDE.md", "rules maintenance", "are there patterns across
  skills that should be a rule", "rules-distill".
---

# Zeno Rules Distill — promote cross-cutting principles into CLAUDE.md

A principle repeated across several skills belongs in `CLAUDE.md` (this repo's single arbitration
document, not a `rules/` directory) so every skill inherits it instead of each one restating it
slightly differently. This skill finds those repeated principles and proposes where they belong.

## When to run it

- Periodic maintenance (e.g. monthly, or after a batch of new skills lands).
- After `zeno-stack/zeno-skill-stocktake` surfaces a pattern that looks cross-cutting.
- When `CLAUDE.md` feels thinner than what the skills actually assume.

## How it works

### Phase 1 — inventory (deterministic)

Scan every `SKILL.md` under `skills/` and index `CLAUDE.md`'s sections/headings. Report the raw
counts before any judgment happens: "N skills scanned, M CLAUDE.md sections indexed."

### Phase 2 — cross-read, match, verdict (judgment)

`CLAUDE.md` is a single file, small enough to hold in full context alongside a batch of skills —
no pre-filtering needed. Group skills into thematic clusters (by shared domain — e.g. all
`zeno-stack` testing-execution leaves in one cluster, all documentation-dispatcher leaves in
another) and cross-read each cluster against the full `CLAUDE.md` text.

**Include a candidate only if all of these hold:**
1. **Appears in 2+ skills** — a principle found in exactly one skill stays in that skill.
2. **Actionable** — phraseable as "do X" / "don't do Y," not "X is important."
3. **Has a stated violation risk** — one sentence on what goes wrong if ignored.
4. **Not already in `CLAUDE.md`** — check the full text, including differently-worded equivalents.

**Assign one verdict per candidate:**

| Verdict | Meaning |
|---|---|
| Append | Add to an existing `CLAUDE.md` section |
| Revise | Existing `CLAUDE.md` content is inaccurate/insufficient — propose a correction |
| New Section | Add a new section to `CLAUDE.md` |
| Already Covered | Sufficiently covered, even if worded differently |
| Too Specific | Should stay at the skill level, not generalize into a rule |

Each candidate needs: the principle (1-2 sentences, "do X"/"don't do Y" form), the evidence (which
skills, which section of each), the violation risk, the verdict, the target section, a confidence
level, and — for Append/New Section/Revise — the actual draft text with `See: <skill-name>` links
back to the skill(s) it came from, so a reader can find the full How behind the distilled What.

**Exclude:** principles already covered, language/framework-specific knowledge (belongs in the
relevant `zeno-stack`/`code-standards` leaf, not `CLAUDE.md`), and code examples/commands (skill
territory, not rule territory).

### Phase 3 — user review and application

Present a summary table (principle / verdict / target section / confidence), then per-candidate
detail (evidence, violation risk, draft). The user responds **Approve** / **Modify** / **Skip** per
candidate.

**Never edit `CLAUDE.md` automatically. Always require explicit per-candidate approval** — this
file is the harness's single arbitration document; an unreviewed edit here changes how every skill
is prioritized.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Promoting a principle found in only one skill | Require 2+ skills as evidence before proposing a rule |
| A candidate with no stated violation risk | Every candidate names what breaks if the principle is ignored |
| Vague verdict text ("Add LLM security principle") | Full draft text with skill evidence and a concrete violation risk |
| Auto-applying candidates without approval | Always Approve / Modify / Skip per candidate, never silent |
| Duplicating code examples into `CLAUDE.md` | Code/commands stay in skills; `CLAUDE.md` gets only the distilled principle + a link back |
| Treating stack-specific knowledge as a cross-cutting rule | Keep it in the relevant `zeno-stack` leaf instead |

## Pre-flight checklist — run before delivering any rules-distillation report

- [ ] Phase 1 inventory counts (skills scanned, `CLAUDE.md` sections indexed) are reported before any judgment.
- [ ] Every candidate has 2+ skill evidence, is actionable, and states a violation risk.
- [ ] Every candidate was checked against the full current `CLAUDE.md` text before being proposed as new.
- [ ] Draft text includes `See: <skill-name>` links back to its evidence.
- [ ] No `CLAUDE.md` edit was applied without an explicit per-candidate Approve from the user.
