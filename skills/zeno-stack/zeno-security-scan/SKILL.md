---
name: zeno-security-scan
description: >
  Scans the Claude Code harness configuration itself (CLAUDE.md, settings.json, mcp.json,
  hooks/, agents/*.md) for prompt-injection surface, overly permissive tool grants, and
  supply-chain/secret risk, using the AgentShield CLI. Use before committing changes to
  `.claude/`, when onboarding a repo with an existing config, or for periodic harness hygiene.
  Distinct from `zeno-security-review`, which audits application code, not the agent config.
  Trigger on: "scan my .claude config", "audit CLAUDE.md", "is my settings.json safe",
  "AgentShield", "check hooks for injection", "harness security check", "config security scan".
---

# Zeno Security Scan

Audits the Claude Code configuration itself — not the application it builds — using
[AgentShield](https://github.com/affaan-m/agentshield). The threat model here is the harness:
a poisoned `CLAUDE.md`, an over-broad `Bash(*)` grant, a hook that shells out to interpolated
input, or an MCP server pulling unpinned code at session start. For application-code security
(SQLi, XSS, auth, secrets in product code), use `zeno-security-review` instead — different
surface, different skill.

## When to run this

- Setting up Claude Code in a new repo
- After editing `.claude/settings.json`, `CLAUDE.md`, `mcp.json`, hooks, or agent definitions
- Before committing any configuration change
- Onboarding into a repo that already has a `.claude/` directory you didn't write
- Periodic hygiene, independent of any specific change

## What gets scanned

| File | Checks |
|---|---|
| `CLAUDE.md` | Hardcoded secrets, auto-run instructions, prompt-injection patterns |
| `settings.json` | Overly permissive allow lists, missing deny lists, dangerous bypass flags |
| `mcp.json` | Risky MCP servers, hardcoded env secrets, `npx` supply-chain exposure |
| `hooks/` | Command injection via interpolation, data exfiltration, silent error suppression |
| `agents/*.md` | Unrestricted tool access, prompt-injection surface, missing model specs |

## Running a scan

```bash
# Confirm it's available, or run ad hoc via npx (no install required)
npx ecc-agentshield --version
npx ecc-agentshield scan .

# Scope to a specific path or severity floor
npx ecc-agentshield scan --path /path/to/.claude
npx ecc-agentshield scan --min-severity medium
```

Output formats: terminal (default, colored, with a letter grade), `--format json` for CI,
`--format markdown` for docs, `--format html > security-report.html` for a shareable
self-contained report.

### Auto-fix

```bash
npx ecc-agentshield scan --fix
```

Applies only findings marked auto-fixable — replacing a hardcoded secret with an env-var
reference, tightening a wildcard permission to a scoped one. It never touches
manual-review-only findings; those still require a human decision.

### Deep adversarial pass

For a higher-stakes review (new repo, unfamiliar `.claude/`, pre-release), run the three-agent
adversarial pipeline instead of the static scan alone:

```bash
export ANTHROPIC_API_KEY=your-key
npx ecc-agentshield scan --opus --stream
```

This runs an Attacker pass (finds attack vectors), a Defender pass (recommends hardening), and
an Auditor pass that synthesizes both into a final verdict — meaningfully more thorough than
the rule-based scan, at the cost of an API key and run time.

### Scaffolding a new, secure config

```bash
npx ecc-agentshield init
```

Produces a `settings.json` with scoped permissions and a deny list, a `CLAUDE.md` seeded with
security guidance, and an `mcp.json` placeholder — a safer starting point than an empty
`.claude/` grown ad hoc.

### CI wiring

```yaml
# Pin third-party actions to a full commit SHA, never a mutable tag — the same
# supply-chain rule zeno-security-review enforces. Resolve the current SHA with
# `gh api repos/affaan-m/agentshield/commits/v1 --jq .sha` before committing.
- uses: affaan-m/agentshield@<full-commit-sha>  # e.g. resolved from the v1 tag
  with:
    path: '.'
    min-severity: 'medium'
    fail-on-findings: true
```

Gate merges to `.claude/` the same way you'd gate merges to application code — a config change
that widens tool access or loosens a hook is a security-relevant diff, not a formatting one.

## Grading

| Grade | Score | Meaning |
|---|---|---|
| A | 90-100 | Secure configuration |
| B | 75-89 | Minor issues |
| C | 60-74 | Needs attention |
| D | 40-59 | Significant risks |
| F | 0-39 | Critical vulnerabilities |

## Interpreting findings

**Critical — fix immediately:**
- Hardcoded API keys or tokens in any config file
- `Bash(*)` (or equivalent unrestricted shell grant) in the allow list
- Command injection in a hook via unsanitized `${file}`-style interpolation
- An MCP server configured to run arbitrary shell commands

**High — fix before the config change ships:**
- Auto-run instructions embedded in `CLAUDE.md` (a prompt-injection vector — text in the
  config that gets treated as an instruction rather than context)
- Missing deny lists in `settings.json` permissions
- Agent definitions with `Bash` access they don't need for their stated job

**Medium — recommended:**
- Silent error suppression in a hook (`2>/dev/null`, `|| true`) that could hide a real failure
- No `PreToolUse` security hook where one would catch a dangerous call before it runs
- `npx -y` auto-install in an MCP server config (accepts whatever version is published at
  invocation time)

**Info — awareness only:**
- MCP servers missing descriptions
- Prohibitive instructions correctly flagged as good practice (not a finding to act on)

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Treating this as an application security scan | Use `zeno-security-review` for app code; this skill is config-only |
| `Bash(*)` or similarly unscoped tool grants | Scope allow lists to the specific commands actually needed |
| Hardcoded secret in `mcp.json` or `CLAUDE.md` | Environment variable reference, verified present at runtime |
| Hook interpolating `${file}`/user input directly into a shell command | Sanitize/quote input, or avoid shell interpolation entirely |
| Silent `2>/dev/null` / `|| true` in a hook | Surface the failure; suppress only with a documented reason |
| Skipping the scan after an "obviously safe" config edit | Run it on every `.claude/` change — the whole point is catching what looks safe |
| Treating a clean scan as a substitute for the `--opus` pass on a new/unfamiliar repo | Run the adversarial pipeline for higher-stakes onboarding |

## Pre-flight checklist — run before delivering any harness security scan

- [ ] Scan run against the current `.claude/` state, not a stale prior report
- [ ] Every Critical and High finding addressed or explicitly deferred with a reason
- [ ] `--fix` applied only for auto-fixable findings; manual-only findings reviewed by hand
- [ ] Grade and finding counts reported, not just "looks fine"
- [ ] For a new/unfamiliar repo, the `--opus` adversarial pass considered, not just the static scan
- [ ] CI gate (`fail-on-findings`) confirmed still wired if this repo relies on it
