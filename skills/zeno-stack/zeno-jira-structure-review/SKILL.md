---
name: zeno-jira-structure-review
description: >
  Reviews an existing Jira backlog's structure — Epics, Stories, Tasks, Bugs, Sub-tasks — finds
  wrong issue types, wrong parents, oversized and undersized tickets, duplicates, missing
  dependencies and weak Story/Task/Bug/Epic quality, and proposes a corrected hierarchy. Applies
  only safe edits on its own; structural changes need approval, and nothing is deleted without
  explicit authorization. Works from a pasted export or the Atlassian MCP once authenticated.
  Trigger on: "review my Jira backlog", "Jira hierarchy", "Jira structure", "epic story task",
  "sub-task", "backlog cleanup", "fix Jira tickets", "is this a story or a task", "split this
  story", "orphaned tickets", "Jira epics".
---

# Jira Structure Review — fix the shape of the backlog, not the people's work

When asked to review or tidy a Jira backlog, inspect the whole relevant hierarchy first, find
systemic problems before individual ones, and propose a corrected structure. The aim is clarity,
ownership, traceability and sprint execution without extra ticket complexity.

**Iron Law: NO STRUCTURAL CHANGE WITHOUT APPROVAL, AND NO DELETION WITHOUT EXPLICIT AUTHORIZATION.**
"Fix everything" and "you have write access" are not approval for restructuring.

## Modes

- **Export mode** (default): the user pasted or attached issues. Review and report; state that
  nothing was changed in Jira.
- **MCP mode**: only when the Atlassian MCP is authenticated (a fresh session may show only its
  `authenticate` tools). Read the hierarchy before proposing anything. Writes follow the SAFE /
  STRUCTURAL rules below.
- **Never invent data.** Missing fields are "requires clarification", not filled in.

## Hierarchy

```
EPIC
 └─ STORY / TASK / BUG        (peers)
     └─ SUB-TASK
```

A Task is not normally a child of a Story. A Story is not nested in a Story. A Sub-task needs a Story,
Task or Bug parent. Epics are outcomes, not folders ("Backend Work", "Sprint 10", "Misc" are folders).

## Final decision rule (per ticket)

1. Major capability or outcome spanning multiple items → **Epic**.
2. Independently delivers user, business or consuming-system value → **Story**.
3. Technical, operational, architectural, research or enablement work → **Task**.
4. Incorrect existing behavior → **Bug**. A feature request dressed as a Bug is not a Bug.
5. One part of completing another Story, Task or Bug → **Sub-task**.

When uncertain, explain the ambiguity instead of guessing.

## Review checks

For each item, in this order:

1. **Outcome** — what is delivered, who gets value, functional or technical, independently testable,
   too large or too small.
2. **Type** — correct per the decision rule? Fake user stories ("As a developer I want a table") are
   Tasks. Architecture work (diagrams, ADRs, standards) is a Task unless it delivers user functionality.
3. **Parent** — Tasks under Stories, Stories nested, Sub-tasks without a valid parent, Epics used as
   folders, orphans that need an Epic.
4. **Oversized** — several unrelated outcomes, several capabilities, likely several sprints, many
   independent acceptance criteria, many owners, words like "complete", "full", "all", "end-to-end".
   Split **vertically by behavior** (create / retrieve / update / deactivate), never by layer
   (DB / API / frontend). Layer sub-tasks under a big Story are a symptom.
5. **Undersized** — DTO, mapper, field, rename. Consolidate into the parent unless separately owned
   or independently valuable; say which when you keep one.
6. **Story quality** — actor, capability, value, testable acceptance criteria (Given/When/Then where it
   helps). Rewrite from existing text only.
7. **Task quality** — objective, scope, deliverable, completion criteria.
8. **Bug quality** — observed vs expected behavior, reproduction, impact, environment. Mark gaps
   `NEEDS CLARIFICATION`; never invent steps.
9. **Epic quality** — one clear outcome, coherent children, no unrelated work, not too broad; consolidate
   Epics that name the same capability.
10. **Duplicates and overlap** — merge, link, convert, re-parent or close-as-duplicate on substance, not on
    similar wording.
11. **Dependencies** — express with link types (blocks / is blocked by / relates to), never with parent-child.

Prefer fewer, clearer tickets. Do not turn Jira into a code-level task list, and do not optimize
reporting at the cost of engineering usability. Do not assume sprint length, capacity, estimates or
owners that were not given.

## SAFE vs STRUCTURAL changes

| Class | Examples | Rule |
|---|---|---|
| **SAFE** | Rename a vague title, fix formatting, improve a description, add acceptance criteria drawn strictly from existing text | May be applied (MCP mode) and reported |
| **STRUCTURAL** | Change issue type, move to another Epic, convert Task↔Story, convert to or from Sub-task, split, merge, close-as-duplicate | Propose with reason; apply only after approval, or if the user explicitly authorized automatic restructuring |
| **DELETE** | Remove an issue | Only with explicit authorization naming deletion. Prefer closing as duplicate or linking |

## Output format (fixed)

1. **Summary** — total structural issues, highest-risk issues, overall backlog quality.
2. **Issues Found** — per item:
   `### <KEY> — <current title>` · Current type · Recommended type · Problem · Recommended action (keep /
   convert / split / merge / re-parent / rename / add acceptance criteria / convert to Sub-task / promote
   from Sub-task / link dependency) · Reason.
3. **Proposed Corrected Hierarchy** — an indented tree (EPIC → STORY/TASK/BUG → SUB-TASK).
4. **Changes requiring approval** — every STRUCTURAL and DELETE item, listed apart from the SAFE ones.

Rewrites keep the original intent, add no unsupported technical detail, use concise outcome-oriented
titles ("Expose store inventory availability API", not "API work"), and mark uncertainty explicitly.

## Boundaries

- `documentation/development-planning-standards` — generic Epic/Story/INVEST/splitting vocabulary; this
  leaf applies it to Jira's issue types and parent rules. **Vocabulary differs:** that skill's *Task*
  (a step inside a Story) is a Jira **Sub-task**; in Jira, Tasks are peers of Stories. On Jira issue
  types and parents, this leaf wins.
- `zeno-stack/zeno-github-ops` — the GitHub equivalent (issues and PRs via `gh`); this leaf is Jira only.
- The zeno `.zeno/` backlog is a separate record. A supplied Jira issue is requirement input to Scope; this
  leaf does not sync or mirror the two.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Applying type changes, re-parenting, splits or merges because the user said "fix everything" | Apply SAFE edits; list STRUCTURAL ones for approval |
| Deleting a duplicate | Close as duplicate or link; delete only on explicit authorization |
| Splitting a big Story into DB / API / frontend sub-tasks | Split vertically into behavior-sized Stories |
| Keeping a Task under a Story | Make it a peer under the Epic and link the dependency |
| Forcing "As a developer…" into a Story | Convert to a Task |
| Filling a vague Bug with plausible repro steps | Mark `NEEDS CLARIFICATION` |
| Merging tickets that merely sound alike | Compare scope and outcome; link if unsure |
| Consolidating a ticket that has a separate owner or independent value | Keep it and say why |
| An Epic named "Backend Work" | Rename to an outcome or split by capability |
| Proposing changes before reading the whole hierarchy | Inspect everything, find systemic problems first |
| Reporting "done" in Export mode as if Jira changed | State that nothing was changed in Jira |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "They told me to fix everything" | That authorizes SAFE edits and proposals. Restructuring needs approval unless explicitly authorized |
| "It is an obvious duplicate, I'll delete it" | Deletion needs explicit authorization. Close-as-duplicate achieves the same result reversibly |
| "I'll add plausible reproduction steps" | Invented detail misleads whoever picks the bug up. Flag the gap |
| "Splitting by layer is simpler" | Layer slices cannot be tested or demonstrated alone. Slice by behavior |
| "These two titles match, so merge them" | Wording is not substance. Compare outcomes and owners |
| "More sub-tasks give better visibility" | Sub-tasks earn their place by ownership or sequencing, not by listing classes |

## Red flags — stop, you're about to break the Iron Law

- You are about to change an issue type, parent, or split/merge with no recorded approval.
- You are about to delete anything.
- You are writing acceptance criteria or repro steps not supported by the existing ticket.
- You are proposing a layer-based split.
- You are reporting results without having read the whole hierarchy.

## Pre-flight checklist — run before delivering any Jira structure review

- [ ] The whole relevant hierarchy was read before any recommendation.
- [ ] Systemic problems are named before individual ones.
- [ ] Every ticket has a type decision by the decision rule; ambiguities are explained, not guessed.
- [ ] Splits are vertical by behavior; consolidations keep separately owned or independently valuable work.
- [ ] Rewrites preserve intent and invent nothing; gaps are marked `NEEDS CLARIFICATION`.
- [ ] Duplicates were judged on substance; dependencies use link types, not parent-child.
- [ ] SAFE changes are separated from STRUCTURAL ones, and every STRUCTURAL and DELETE item is under "Changes requiring approval".
- [ ] Nothing was deleted, and nothing structural was applied without approval or explicit authorization.
- [ ] Export mode states plainly that Jira was not changed.
- [ ] Output follows the fixed format (Summary, Issues Found, Proposed Corrected Hierarchy, Changes requiring approval).
