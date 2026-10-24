---
name: zeno-code-tour
description: >
  Create CodeTour `.tour` JSON files — persona-targeted, step-by-step walkthroughs anchored
  to real files and line ranges, written to `.tours/`. Use for onboarding tours,
  architecture walkthroughs, PR tours, RCA tours, and structured "explain how this works"
  requests that warrant a reusable guided artifact rather than a one-off chat answer.
  Trigger on: "code tour", "onboarding tour", "architecture walkthrough", "PR tour",
  "walk me through this feature", "explain how X works" (when a reusable artifact is
  wanted), or ramp-up material for a new engineer or reviewer.
---

# Code Tour

Author CodeTour `.tour` files — guided walkthroughs that open directly to real files and
line ranges in the editor. Only `.tour` JSON files are produced; this skill never modifies
source code.

## When to use

- The user asks for a code tour, onboarding tour, architecture walkthrough, or PR tour.
- "Explain how X works" and a reusable guided artifact (not a one-off answer) is wanted.
- Ramp-up path for a new engineer or reviewer.
- Examples: onboarding a new maintainer, architecture tour of one service, PR-review
  walkthrough anchored to changed files, RCA tour of a failure path, security review tour
  of trust boundaries.

## When not to use

| Instead of code-tour | Use |
|---|---|
| A one-off chat explanation is enough | Answer directly |
| The user wants prose docs, not a `.tour` artifact | `documenting-code` or repo docs editing |
| The task is implementation or refactoring | Do the implementation work |
| Broad codebase onboarding without a tour artifact | `zeno-codebase-onboarding` |

## Workflow

**1. Discover.** Explore before writing: README, entry points, folder structure, relevant
config, and (for PR tours) the actual changed files. Don't start writing steps before
understanding the shape of the code.

**2. Infer the reader.** Persona and depth follow the request:

| Request shape | Persona | Suggested depth |
|---|---|---|
| "onboarding", "new joiner" | `new-joiner` | 9-13 steps |
| "quick tour", "vibe check" | `vibecoder` | 5-8 steps |
| "architecture" | `architect` | 14-18 steps |
| "tour this PR" | `pr-reviewer` | 7-11 steps |
| "why did this break" | `rca-investigator` | 7-11 steps |
| "security review" | `security-reviewer` | 7-11 steps |
| "explain how this feature works" | `feature-explainer` | 7-11 steps |
| "debug this path" | `bug-fixer` | 7-11 steps |

**3. Verify every anchor.** Confirm the file exists, confirm line numbers are in range,
verify the exact block for selections, and prefer a pattern-based anchor over a line
number for volatile files. Never guess a line number.

**4. Write to `.tours/<persona>-<focus>.tour`** — a deterministic, readable path.

**5. Validate before finishing:** every referenced path exists; every line/selection is
valid; the first step anchors to a real file or directory (never a content-only step);
`ref` points at a revision that actually contains every file the tour references (see
below); the tour reads as a coherent narrative, not a file inventory.

## The `ref` field — the most common failure mode

`ref` ties the tour to a git branch or commit. When it doesn't match what the reader has
checked out, CodeTour opens each step's file from that revision via git, not from disk. If
a file doesn't exist in that revision, the step fails silently with *"The editor could not
be opened because the file was not found"* — even though the file is sitting right there on
disk. The tour and its comments still render, so the real cause is easy to miss.

| Tour type | Set `ref` to |
|---|---|
| PR tour | The PR branch — never the base branch |
| Onboarding / architecture | The branch the reader will be on (often `main`), or omit |
| Not sure | Omit — CodeTour then reads straight from disk |

The PR trap: a PR usually adds new files that don't exist on the base branch yet. Pointing
`ref` at the base (e.g. `develop`) makes every step touching a new file fail to open.
Always confirm each step's file exists at the chosen `ref` before finishing.

## Step types

**Content** — sparingly, usually only for a closing step. Never make the first step
content-only.
```json
{ "title": "Next Steps", "description": "You can now trace the request path end to end." }
```

**Directory** — orient the reader to a module.
```json
{ "directory": "src/services", "title": "Service Layer", "description": "The core orchestration logic lives here." }
```

**File + line** — the default step type.
```json
{ "file": "src/auth/middleware.ts", "line": 42, "title": "Auth Gate", "description": "Every protected request passes here first." }
```

**Selection** — when one block matters more than the whole file.
```json
{
  "file": "src/core/pipeline.ts",
  "selection": { "start": { "line": 15, "character": 0 }, "end": { "line": 34, "character": 0 } },
  "title": "Request Pipeline",
  "description": "This block wires validation, auth, and downstream execution."
}
```

**Pattern** — when exact lines may drift.
```json
{ "file": "src/app.ts", "pattern": "export default class App", "title": "Application Entry" }
```

**URI** — link a PR, issue, or doc when helpful.
```json
{ "uri": "https://github.com/org/repo/pull/456", "title": "The PR" }
```

## Writing rule: SMIG

Each description should hit all four:
- **Situation** — what the reader is looking at
- **Mechanism** — how it works
- **Implication** — why it matters for this persona
- **Gotcha** — what a sharp reader might still miss

Keep descriptions compact, specific, and grounded in the actual code — not generic.

## Narrative shape

Default arc unless the task clearly needs otherwise: orientation → module map → core
execution path → edge case or gotcha → closing/next move. The tour should read as a path
through the code, not an inventory of it.

## Example

```json
{
  "$schema": "https://aka.ms/codetour-schema",
  "title": "API Service Tour",
  "description": "Walkthrough of the request path for the payments service.",
  "ref": "main",
  "steps": [
    { "directory": "src", "title": "Source Root", "description": "All runtime code for the service starts here." },
    { "file": "src/server.ts", "line": 12, "title": "Entry Point", "description": "The server boots here and wires middleware before any route is reached." },
    { "file": "src/routes/payments.ts", "line": 8, "title": "Payment Routes", "description": "Every payments request enters through this router before hitting service logic." },
    { "title": "Next Steps", "description": "You can now follow any payment request end to end with the main anchors in place." }
  ]
}
```

## Best practices

Keep step count proportional to repo size and persona depth; use directory steps for
orientation and file steps for substance; for PR tours cover changed files first; for
monorepos scope to the relevant packages rather than touring everything; close with what
the reader can now do, not a recap of what was shown.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Flat file listing | Tell a story with dependency between steps |
| Generic descriptions ("this file does stuff") | Name the concrete code path or pattern |
| Guessed line numbers or unverified files | Verify every anchor before writing the step |
| Ref points at the base branch for a PR tour | Ref points at the PR branch itself |
| First step is content-only | Anchor the first step to a real file or directory |
| Too many steps for a "quick tour" request | Cut aggressively to match the inferred depth |
| Writing for a generic engineer regardless of request | Infer and write for the actual persona |

## Pre-flight checklist — run before delivering any `.tour` file

- [ ] Every file path referenced by a step exists
- [ ] Every line number / selection is verified in range, not guessed
- [ ] The first step anchors to a real file or directory, never content-only
- [ ] `ref` is set correctly for the tour type (PR branch for PR tours; omitted or `main` otherwise) and every step's file exists at that ref
- [ ] Persona and step count match the inferred request shape
- [ ] Descriptions cover Situation, Mechanism, Implication, and Gotcha where relevant
- [ ] The tour tells a coherent narrative, not a flat file inventory
- [ ] File is written to `.tours/<persona>-<focus>.tour`
