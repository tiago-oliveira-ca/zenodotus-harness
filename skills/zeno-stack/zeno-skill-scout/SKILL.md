---
name: zeno-skill-scout
description: >
  Search marketplace, GitHub, and web skill sources before creating a new skill — the external
  counterpart to zeno-find-skills' local enumeration. Use when the user wants to create, build,
  fork, or find a skill for a workflow and a local match hasn't already ruled out the need.
  Trigger on: "create a skill", "build a skill", "make a skill", "new skill", "is there a skill
  for X", "does a skill exist that does Y", or describing a workflow where creating a new skill is
  about to be suggested.
---

# Zeno Skill Scout — external search before creation

Use this after `zeno-find-skills` has already ruled out a local match. The goal is to avoid
duplicating existing marketplace or community work, while still vetting anything external before
adoption. If the user explicitly says to skip search or create from scratch, acknowledge that and
proceed with creation directly.

## Step 1 — capture intent

Extract: the task the skill should perform, its trigger conditions, the domain/tools/frameworks
involved, and three to five search keywords plus useful synonyms.

## Step 2 — search local sources (delegate, don't reimplement)

**Delegate this step to `zeno-find-skills`** — it already owns local-library enumeration
(`~/.claude/skills/`, dispatcher routing tables, the session's plugin listing). Don't re-run its
`find`/`grep` commands here; call it and use its result as the local-match baseline before moving
to remote search below.

## Step 3 — search remote sources

Use available GitHub and web search tools, concise queries:

```bash
gh search repos "claude code skill keyword" --limit 10 --sort stars
gh search code "name: keyword" --filename SKILL.md --limit 10
```

For web search, at most three targeted queries, e.g. `"claude code skill" keyword`, `"SKILL.md"
keyword`.

## Step 4 — vet external matches

Before recommending any external skill for adoption or forking:
- Read its `SKILL.md` frontmatter and instructions in full.
- Look for unexpected shell commands, file writes, network calls, credential handling, or package
  installs — treat any of these as a reason to slow down, not proceed.
- Check whether the source repository appears maintained.
- Prefer copying into a fresh local branch and reviewing the diff over editing marketplace
  originals in place.
- Check whether it ships a `.claude-plugin/marketplace.json`. If it does, it is a plugin —
  install it through the plugin mechanism, or make a file-copy a *deliberate, documented fork*
  — never both for the same upstream. Bulk copies are invisible to plugin updates (permanently
  un-updatable, no inventory), and a dangling `enabledPlugins` entry sitting on top of copies
  doubles every component the day it resolves.

## Step 5 — rank results

Rank by: (1) exact keyword match in the skill name, (2) keyword/synonym match in the description,
(3) local source (from `zeno-find-skills`'s result), (4) maintained GitHub source with recent
activity, (5) web-only mention. Cap the final list at 10.

## Step 6 — present decision options

| Option | Meaning |
|---|---|
| Use existing | Invoke or install a matching skill as-is |
| Fork or extend | Copy the closest skill and modify it |
| Create fresh | Build a new skill after confirming no close match exists |

Only create a new skill after the user picks that path, or after search genuinely finds no close
match — don't default to creation as the first move.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Jumping to creation before searching | Run local (via `zeno-find-skills`) then remote search first |
| Reimplementing local-library search here | Delegate Step 2 to `zeno-find-skills` |
| Installing an external skill without reading it | Read frontmatter + instructions fully, check for risky commands/network calls/credential handling |
| Presenting a long unranked list of weak matches | Rank by the 5-factor order above; cap at 10 |
| Treating a web-only mention as a trusted source | Rank it lowest; verify before recommending |
| Editing an installed marketplace original in place | Copy into a local branch and review the diff instead |
| Bulk file-copying a plugin-published library into `~/.claude/` | Install via the plugin mechanism, or document an explicit fork — never both mechanisms for one upstream |

## Pre-flight checklist — run before delivering any skill-creation recommendation

- [ ] Local search was delegated to `zeno-find-skills`, not reimplemented.
- [ ] Remote search covered both GitHub (`gh search repos`/`gh search code`) and a few targeted web queries.
- [ ] Every external candidate under consideration was actually read (frontmatter + instructions), not just named.
- [ ] Results are ranked by the stated 5-factor order and capped at 10.
- [ ] Creation is recommended only after the user chose it or no close match was found.
