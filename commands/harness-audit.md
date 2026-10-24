---
description: Run a repository harness audit and return a prioritized scorecard, checked directly (no external scoring script).
---

# Harness Audit Command

Audit this repo's Claude Code harness configuration and return a prioritized scorecard.

## Usage

`/harness-audit [scope] [--format text|json] [--root path]`

- `scope` (optional): `repo` (default), `hooks`, `skills`, `commands`, `agents`
- `--format`: output style (`text` default, `json` for automation)
- `--root`: audit a specific path instead of the current working directory

## How this runs

There is no bundled scoring script — the checks below are run directly (grep/`ls`/file reads),
the same way `zeno-stack/zeno-config-gc` (a skill) and `agents/zeno-harness-optimizer` (an agent)
already audit this repo without a separate binary. Every score must trace to a concrete file/rule
check named in the finding — don't invent a point value with no check behind it.

Score each applicable category `0-10`. The first seven are always applicable; GitHub Integration
and the two Config Health categories (13-14) are always applicable; deploy-target categories
(9-12) only when their marker file is present.

| # | Category | What to check |
|---|---|---|
| 1 | Tool Coverage | Every `agents/zeno-*.md` grants only the tools its stated domain needs (`agents/REGISTRY.md` tier: Advisor = read-only, Owner = bounded Write/Edit); no tool grant broader than the agent's Contract's `Tools` field states. |
| 2 | Context Efficiency | Skill/agent frontmatter descriptions stay under `_skill-template.md`'s ~1000-char ceiling; no oversized `SKILL.md` that should be split into `references/*.md`. |
| 3 | Quality Gates | `zeno-verify`'s Review gate and its "Full-repo phase check" are intact and reachable; any project using this harness has a real build/test/lint command the gate can invoke. |
| 4 | Memory Persistence | `.zeno/project.md` exists for repos with active work and its Kanban board reflects reality (no stale `[~]` items past the WIP limit of 1); the SessionStart hook (`hooks/zeno-session-start.sh`) is registered per `session-hook.fragment.json`. |
| 5 | Eval Coverage | Test-execution skills (`zeno-stack/zeno-python-testing`, `zeno-stack/zeno-react-testing`, `zeno-stack/zeno-e2e-testing`) are reachable from `zeno-stack/SKILL.md`'s routing table; `zeno-workflow/zeno-tdd` is wired into Build. |
| 6 | Security Guardrails | `zeno-stack/zeno-security-scan` and `zeno-security-reviewer` are both reachable (`agents/REGISTRY.md`); no agent grants `Bash` without a stated reason in its Contract; no secret-looking string committed under `skills/`/`agents/`/`commands/`. |
| 7 | Cost Efficiency | Model assignments in agent frontmatter match `agents/_agent-template.md` §4 (haiku for narrow/mechanical, opus only for `zeno-planner`-style open-ended judgment); no oversized always-loaded skill description inflating every session's context. |
| 8 | GitHub Integration | `.github/workflows/` exists with at least one workflow, if this repo ships CI. |
| 9 | Vercel Integration | Only when `vercel.json` or `.vercel/` is present. |
| 10 | Netlify Integration | Only when `netlify.toml` or `.netlify/` is present. |
| 11 | Cloudflare Integration | Only when `wrangler.toml`/`wrangler.jsonc` is present. |
| 12 | Fly Integration | Only when `fly.toml` is present. |
| 13 | Plugin Config Health | Every `enabledPlugins` key resolves to an entry in `installed_plugins.json`; for each enabled plugin, any declared MCP server needing `env` vars has them set, and any bundled `setup.sh`/`install.sh` a marketplace install wouldn't have run is flagged. "Installed" and "configured" are different states — an enabled-but-unconfigured plugin costs context every session and fails only on first tool call. |
| 14 | Governance Accuracy | Every testable claim in always-loaded governance docs (CLAUDE.md inventory counts, named directories/plugins/agents/hooks) is diffed against the filesystem; no installation-guide or other read-on-demand content rides along in an always-loaded file. Stale claims mis-route work silently — they're worse than silence. |

## Output Contract

Return:

1. `overall_score` out of `max_score` — `max_score` depends on which categories applied; never
   assume a fixed total (deploy-target categories that don't apply are excluded, not scored 0).
2. `applicable_categories[]` and `category_count`.
3. Per-category score with the concrete finding(s) that produced it.
4. Failed checks with exact file paths — no vague "could be better."
5. Top 3 actions, each naming the file/rule it fixes.
6. Relevant `zeno-stack` skills to apply next, where a failed check maps to one.

## Checklist

- Every score traces to a named check in the table above — no invented dimensions.
- If `--format json` is requested, return the same data as structured JSON, not prose.
- Include exact file paths for every failed check and every top action.

## Example Result

```text
Harness Audit (repo): 71/80
- Tool Coverage: 10/10 — every agent's tools match its Contract's Decision authority tier
- Context Efficiency: 9/10 — one skill description over 900 chars, none over the 1000 ceiling
- Quality Gates: 10/10 — zeno-verify's phase check intact, project's test command wired
- GitHub Integration: 2/10 — no .github/workflows/ present

Top 3 Actions:
1) [GitHub Integration] Add at least one workflow under .github/workflows/.
2) [Security Guardrails] Confirm zeno-security-reviewer is invoked before merging auth changes.
3) [Cost Efficiency] zeno-comment-analyzer's description is 940 chars — trim toward the ~1000 ceiling's front-loaded triggers.
```

## Arguments

$ARGUMENTS:
- `repo|hooks|skills|commands|agents` (optional scope)
- `--format text|json` (optional output format)
- `--root path` (optional, audit a specific path instead of the current working directory)
