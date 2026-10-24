---
description: Security scan — harness config (AgentShield) or application code (zeno-security-reviewer), depending on target.
---

# Security Scan Command

Two different surfaces share the word "security," and this command routes to whichever one
applies rather than treating them as one scan:

| Target | Owner |
|---|---|
| The Claude Code harness config itself (`CLAUDE.md`, `settings.json`, `mcp.json`, `hooks/`, `agents/*.md`) | `zeno-stack/zeno-security-scan` skill, via the AgentShield CLI |
| Application code (endpoints, auth, DB queries, dependencies) | `zeno-security-reviewer` agent |

## Usage

```text
/security-scan [path] [--target harness|app]
```

- `path` (optional) — defaults to the current project.
- `--target` — `harness` scans `.claude`-style config; `app` reviews application code. If omitted,
  infer from `path`: a path under `.claude/`, `~/.claude/`, or a repo whose primary content is
  skills/agents/commands is `harness`; anything else is `app`.

## Harness-config target

Delegates entirely to `zeno-stack/zeno-security-scan` — load that skill and follow it. In short:
run the AgentShield CLI (`npx ecc-agentshield scan --path <path> --format text`, or `npm run scan`
from a local AgentShield checkout for development), then turn findings into a prioritized
remediation plan, separating active runtime findings (hardcoded secrets, broad tool grants,
executable hooks, MCP servers with shell/filesystem/unpinned-`npx` access, agent prompts with no
untrusted-input defenses) from lower-confidence inventory (docs examples, template files, optional
project-local settings). Do not invent findings — the scanner's output is the source of truth;
scanner facts and follow-up judgment stay clearly separated in the report.

## Application-code target

Delegates to the `zeno-security-reviewer` agent (see `agents/REGISTRY.md`) — a manual, read-only
OWASP-focused review (injection, secrets, SSRF, weak crypto, auth) rather than a packaged scanner,
since application code doesn't have an equivalent off-the-shelf tool wired into this repo. Invoke
it directly for a full pass, or as the independent-review specialist at the zeno Review gate for a
diff that touches user input, auth, or sensitive data.

## Output Contract

Whichever target ran, report:

1. Target (harness config or application code) and why it was selected.
2. Findings grouped by severity, with file path and concrete remediation for each.
3. For the harness target: a security grade/score and counts by severity + runtime confidence,
   per `zeno-security-scan`'s own report format.
4. For the app target: the `zeno-security-reviewer` agent's standard findings report.
5. A remediation order across both if both were run.

## Related

- Skill: `zeno-stack/zeno-security-scan` (harness config, AgentShield).
- Agent: `zeno-security-reviewer` (application code).
- These are distinct because the surfaces are distinct — see `zeno-stack/zeno-security-scan`'s own
  frontmatter for why it doesn't try to cover application code too.

## Arguments

$ARGUMENTS:
- optional target path
- `--target harness|app`
