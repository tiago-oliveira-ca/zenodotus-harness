---
name: zeno-find-skills
description: >
  Discovers and recommends skills already available in this Claude Code install, and gates the
  decision between reusing, updating, installing, or creating a skill. Use proactively whenever
  the user asks about capabilities, looks for functionality that might exist as a skill, or wants
  to extend agent behavior. Trigger on: "find a skill for X", "is there a skill that can...", "how
  do I do X" (when a skill might cover it), "install a skill", "create a new skill", "what skills
  are available", "add a skill", "does a skill overlap with". Always enumerate the live skill
  library first — never answer from memory.
---

# Zeno Find Skills — local discovery before creation

Discover what's already available in this install and decide whether a request needs an existing
skill, an update to one, or a new one — before creating anything.

## Skill locations in this install

| Scope | Location | Purpose |
|---|---|---|
| Session-provided | The skill listing already in the current conversation | Skills and plugin skills loaded/loadable right now |
| User-global | `~/.claude/skills/` | The user's library, available across all projects |
| Project-local | `<repo>/.claude/skills/` | Skills shared with a team via a specific repo |
| Plugins | Plugin skills in the session listing | Installed plugin capabilities |

The user-global library follows a dispatcher pattern (per `~/.claude/CLAUDE.md`): dispatcher
skills (`code-standards/`, `documentation/`, `testing/`, `zeno-stack/`) route to nested leaves via
a routing table in their own `SKILL.md`; everything else is standalone.

## Step 1 — enumerate the live library, never trust a cached inventory

Skill inventories drift; always enumerate at time of use:

```bash
ls ~/.claude/skills/                              # top-level dispatchers + standalones
find ~/.claude/skills -name SKILL.md | sort        # full library, including nested leaves
grep -A3 "^description:" ~/.claude/skills/*/SKILL.md   # what each top-level skill covers
```

For nested coverage, read the dispatcher's own routing table (`code-standards/SKILL.md`,
`documentation/SKILL.md`, `testing/SKILL.md`, `zeno-stack/SKILL.md`) — that table is the
authoritative index of what's nested underneath, not the directory listing alone. Also check the
session's plugin-skill listing for anything that already covers the request.

## Step 2 — decide: reuse, update, install, or create

In strict order of preference:

1. **Reuse** an existing skill, including a nested leaf reachable via a dispatcher's routing table.
2. **Update** an existing skill when the request is a small delta on something already covered —
   never install or create an overlapping skill when a small update would do.
3. **Install** an external skill only when the user explicitly wants one, into the correct scope.
4. **Create** a new skill only after 1-3 are ruled out — nest technology/artifact skills under the
   matching dispatcher (`code-standards`, `zeno-stack`, etc.); go top-level only for a domain no
   dispatcher covers; give it `name` + `description` frontmatter with concrete trigger phrases;
   register it in the dispatcher's routing table AND its own frontmatter description.

This skill owns **discovery and the overlap check** — creation mechanics follow whatever the
repo's own skill-authoring convention is (see `~/.claude/CLAUDE.md`'s "Creating new skills"
section, and `_skill-template.md` for the canonical shape).

## Step 3 — present options to the user

1. Name the skill (with its dispatcher path if nested) and what it covers.
2. State whether it's already available, needs an update, or doesn't exist yet.
3. For a genuine gap: recommend where a new skill would live (which dispatcher, or top-level)
   before any creation starts.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Answering "what skills are available" from memory | Enumerate `~/.claude/skills/` + dispatcher routing tables live, this turn |
| Hand-maintained skill inventory baked into this skill | Live enumeration commands — inventories rot, commands don't |
| Creating a new skill that overlaps an existing one | Update the existing skill; check dispatcher routing tables for nested overlap first |
| New top-level skill for a technology/artifact type | Nest under the matching dispatcher instead |
| Registering a nested leaf only in the routing table | Also give it its own trigger-rich frontmatter description |
| Referencing other harnesses' paths (`.agents/skills/`, `~/.codex/skills/`) | This install only: `~/.claude/skills/` and project `.claude/skills/` |

## Pre-flight checklist — run before delivering any skill-discovery answer

- [ ] Live enumeration was performed this turn (`ls`/`find` on `~/.claude/skills/`), not answered from memory.
- [ ] Dispatcher routing tables were checked for nested leaves, not just top-level directory names.
- [ ] The session's plugin-skill listing was considered.
- [ ] If recommending creation: overlap was ruled out first, and the target location follows the dispatcher pattern.
- [ ] If recommending an update instead of a new skill, the target skill and section are named specifically.
