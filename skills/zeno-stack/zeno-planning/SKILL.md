---
name: zeno-planning
description: >
  Turn a feature request or refactor into a file-level implementation plan a different engineer
  could execute and get the same result back — exact file paths, phased steps with
  action/why/dependencies/risk, a testing strategy, and success criteria. Advisory only: produces
  the plan, doesn't implement it. Trigger on: "plan this feature", "implementation plan", "how
  should I build this", "plan the refactor", "break this down into steps".
---

# File-Level Implementation Planning

Turn a feature request or refactor into a plan someone could hand to a different engineer and get
the same implementation back. A plan that only makes sense to the person who wrote it isn't
finished.

## Where the plan lands

When the zeno loop is active (a tracked `.zeno/` exists), plan content belongs **on the `.zeno/`
Story/Task cards** — Gate 2's Task-breakdown pass is exactly this skill's step contract, and a
parallel standalone plan file would violate the loop's no-ad-hoc-files rule. Produce a standalone
"Implementation Plan" document only for advisory-only requests outside the loop (or when the
user explicitly asks for a plan file).

## Before writing a single step

Restate the requirement, surface any assumption explicitly rather than silently baking it in, and
note what "done" means concretely enough to check later. Then read the codebase before proposing
anything — find the components this touches, look for an existing implementation of something
similar (a plan that reinvents a pattern the codebase already has is a worse plan).

## What makes a step usable

"Add subscription logic" is not a step, it's a restatement of the goal. Every step needs: an
**exact file path**, the **specific action**, **why** the step exists, its **dependencies** (or
"none"), and a **risk level** (low/medium/high, with a one-line reason above low). Group steps
into phases so related changes land together; order phases by dependency, not presumed
importance.

## Shape of the finished plan

```markdown
# Implementation Plan: [Feature Name]
## Overview
## Requirements
## Architecture Changes
## Implementation Steps
### Phase 1: [Name]
1. **[Step]** (File: path/to/file.ts) — Action / Why / Dependencies / Risk
## Testing Strategy
## Risks & Mitigations
## Success Criteria
```

## Sizing large work

Break anything too big for one pass into phases that each ship something real on their own —
never a plan where nothing works until every phase lands: **Minimum viable** → **Core
experience** → **Edge cases** → **Optimization**.

## Planning a refactor differently than a feature

Start from the code smells and debt actually present, not a generic checklist. The plan must
preserve existing behavior — "nothing observable changed" is the primary success criterion — and
prefer backward-compatible, incremental steps over a big-bang rewrite, since a refactor that can't
be merged in pieces can't be reviewed in pieces either.

## What makes a plan worth rejecting

Watch for these before handing a draft off: steps without a real file path, phases that can't be
merged independently, no testing strategy at all, hardcoded values where the codebase already has
a config pattern, and hand-waved error handling ("handle errors appropriately" is not a step).

**Agent counterpart:** `agents/zeno-planner.md` — the spawned independent planning pass over this same step contract (this skill is its Codex fold home).

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| A step that restates the goal ("add the feature") | Name the exact file, the specific action, and why |
| Reinventing a pattern the codebase already has | Read the codebase first; reuse what exists |
| A refactor plan framed as a big-bang rewrite | Incremental, independently-mergeable steps; "nothing observable changed" is success |
| No testing strategy, or hand-waved error handling | Both are required sections, not optional prose |
| Implementing the plan inside this skill | Advisory only — hand off to Execution once approved |

## Pre-flight checklist — run before delivering any implementation plan

- [ ] Every step names an exact file path, the specific action, why, dependencies, and a risk level.
- [ ] Phases are ordered by dependency and each is independently mergeable.
- [ ] A refactor plan treats "nothing observable changed" as the primary success criterion.
- [ ] Testing Strategy and Risks & Mitigations sections are both present, not hand-waved.
- [ ] The draft was checked against the "what makes a plan worth rejecting" list with no gaps found.
