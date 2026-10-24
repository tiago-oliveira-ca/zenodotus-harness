---
name: zeno-context-budget
description: >
  Audits Claude Code context-window consumption across agents, skills, MCP servers,
  rules, and CLAUDE.md — inventories token overhead per component, classifies each as
  always/sometimes/rarely needed, flags bloat and redundancy, and produces a prioritized
  token-savings report. Use when a session feels sluggish, after adding several
  agents/skills/MCP servers, or before adding more and needing to know if there's room.
  Trigger on: "context budget", "how much context am I using", "session feels slow",
  "context window audit", or "do I have room for more MCP servers".
---

# Context Budget

Estimate token overhead across every loaded component in a Claude Code session and
surface prioritized, actionable ways to reclaim context space.

## When to use

- Session performance feels sluggish, or output quality is degrading.
- Several skills, agents, or MCP servers were recently added.
- Before adding more components and needing to know if there's headroom.
- Invoked directly by name or by any of its trigger phrases above.

**Scope boundary:** this skill audits *context-window* token overhead only — how much of the
window a component's content consumes, regardless of model. It does not estimate dollar cost or
audit whether an agent's `model:` tier is well-chosen for its work; that's
`commands/harness-audit.md` category 7's job (checked against `agents/_agent-template.md` §4's
policy), with `/model-route` supplying the shape/risk criteria for a specific routing decision.
Complementary, not overlapping: a component can be well-sized for the context window and still be
on the wrong model tier, or vice versa. Runtime tool-call/conversation-history accumulation during
a long loop is a different axis again — see `zeno-debug`'s and `zeno-workflow/zeno-tdd`'s
per-cycle rolling-summary guidance for that; this skill stays static-inventory only.
KV-cache/attention-level serving optimization (eviction, quantization, streaming windows) is out
of scope entirely for a different reason than the exclusions above: those techniques cut GPU
memory and inference throughput for a self-hosted model server, and Claude Code is an API client
with no inference server of its own to tune.

## Method

### Phase 1 — Inventory

Scan each component directory and estimate token consumption:

**Agents** (`agents/*.md`) — tokens per file (`words × 1.3`); extract `description`
frontmatter length. Flag files >200 lines (heavy) and descriptions >30 words (bloated
frontmatter — this loads into every Task tool invocation, not just when the agent runs).

**Skills** (`skills/*/SKILL.md`) — tokens per file. Flag files >400 lines. Check for
duplicate copies elsewhere (e.g. `.agents/skills/`) and skip identical copies to avoid
double-counting.

**Rules** (`rules/**/*.md`) — tokens per file. Flag files >100 lines. Detect content
overlap between rule files in the same language/domain module.

**MCP servers** (`.mcp.json` or active MCP config) — count servers and total tool count;
estimate schema overhead at ~500 tokens/tool. Flag servers with >20 tools, and servers
that merely wrap a simple CLI already available for free (`gh`, `git`, `npm`, etc.).

**CLAUDE.md** (project + user-level) — tokens per file in the chain. Flag combined total
>300 lines.

**Frontmatter extraction — first block only, anchored at start of file.** Use
`re.match(r'^---\n(.*?)\n---\n', text, re.S)` (via `python3 -c`) or an equivalent
first-block-only loop. Never a `sed` range address (`sed -n '/^---$/,/^---$/p'`): range
addresses restart after every match, so on Markdown they also capture body sections delimited
by `---` horizontal rules — inflating totals (~1.8× observed) while leaving percentages
plausible enough to pass a smell test. Before reporting, sanity-check the per-item extremes:
the largest single "frontmatter" must be physically plausible (a YAML block is rarely over
~1 KB); one implausible outlier invalidates the whole measurement and any recommendation
derived from it.

### Phase 2 — Classify

| Bucket | Criteria | Action |
|---|---|---|
| Always needed | Referenced in CLAUDE.md, backs an active command, matches current project type | Keep |
| Sometimes needed | Domain-specific, not referenced in CLAUDE.md | Consider on-demand activation |
| Rarely needed | No command reference, overlapping content, no obvious project match | Remove or lazy-load |

### Phase 3 — Detect issues

- Bloated agent descriptions (>30 words) — loaded into every Task tool context regardless
  of whether the agent is ever invoked.
- Heavy agents (>200 lines) — inflate Task tool context on every spawn.
- Redundant components — skills duplicating agent logic, rules duplicating CLAUDE.md.
- MCP over-subscription — >10 servers, or servers wrapping free CLI tools.
- CLAUDE.md bloat — verbose explanations, stale sections, instructions that belong in
  rules instead.
- Prose-dense sections — large from rationale/examples rather than distinct directive content.
  This is a different signal from the length flags above: apply an extractive-compression read
  (would cutting the restatement/example past some threshold lose an instruction, or only a
  repeated explanation?) rather than line count alone — a short file can still be low-density,
  and a long one can be justified by genuinely distinct content.

### Phase 4 — Report

```
Context Budget Report
═══════════════════════════════════════

Total estimated overhead: ~XX,XXX tokens
Context model: Claude Sonnet (200K window)
Effective available context: ~XXX,XXX tokens (XX%)

Component Breakdown:
┌─────────────────┬────────┬───────────┐
│ Component       │ Count  │ Tokens    │
├─────────────────┼────────┼───────────┤
│ Agents          │ N      │ ~X,XXX    │
│ Skills          │ N      │ ~X,XXX    │
│ Rules           │ N      │ ~X,XXX    │
│ MCP tools       │ N      │ ~XX,XXX   │
│ CLAUDE.md       │ N      │ ~X,XXX    │
└─────────────────┴────────┴───────────┘

Issues found (N): [ranked by token savings]

Top 3 optimizations:
1. [action] → save ~X,XXX tokens
2. [action] → save ~X,XXX tokens
3. [action] → save ~X,XXX tokens

Potential savings: ~XX,XXX tokens (XX% of current overhead)
```

Verbose mode adds: per-file token counts, line-by-line breakdown of the heaviest files,
specific redundant lines between overlapping components, and a full MCP tool list with
per-tool schema-size estimates.

## Estimation calibration

- Prose: `words × 1.3`.
- Code-heavy / mixed content: `chars / 4`.
- MCP is the biggest lever — each tool schema costs ~500 tokens, so a 30-tool server can
  cost more than the entire skill library combined.
- Agent descriptions are *always* loaded, whether or not the agent is invoked — treat
  bloated descriptions as a standing tax, not a one-time cost.

## Examples

**Basic audit** — invoke `zeno-context-budget` → scans setup → 16 agents (12,400 tokens), 28 skills
(6,200), 87 MCP tools (43,500), 2 CLAUDE.md (1,200). Flags: 3 heavy agents, 14 MCP servers
(3 CLI-replaceable). Top saving: remove 3 MCP servers → -27,500 tokens (47% overhead
reduction).

**Pre-expansion check** — "I want to add 5 more MCP servers, do I have room?" → current
overhead 33% → adding 5 servers (~50 tools) adds ~25,000 tokens → pushes to 45% overhead.
Recommendation: remove 2 CLI-replaceable servers first to stay under 40%.

## Best practices

Use verbose mode only when pinpointing exact offending files, not for routine audits.
Audit after any addition of an agent, skill, or MCP server to catch creep early rather
than discovering it during a slow session weeks later.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Reporting overhead with no per-component breakdown | Always show the component table |
| Treating "green CI" or "small skill count" as proof of low overhead | Actually estimate tokens per component |
| Ignoring MCP tool schema cost | ~500 tokens/tool — usually the single biggest lever |
| Recommending removal without naming token savings | Every recommendation states its estimated savings |
| One-time audit, never repeated | Re-run after every meaningful addition |
| Flagging bloat without checking if the component backs an active command/CLAUDE.md reference | Classify into always/sometimes/rarely before recommending removal |
| `sed -n '/^---$/,/^---$/p'` to extract frontmatter | First-block-only parse anchored at start of file; sed ranges restart at every `---` rule and inflate totals |

## Pre-flight checklist — run before delivering any context-budget report

- [ ] All five component categories (agents, skills, rules, MCP, CLAUDE.md) were scanned
- [ ] Every component was classified always/sometimes/rarely needed before flagging
- [ ] Token estimates used the correct heuristic (prose vs. code-heavy)
- [ ] Duplicate skill/rule copies were deduplicated, not double-counted
- [ ] Top optimizations each state an estimated token savings
- [ ] Report includes the component breakdown table and total estimated overhead
- [ ] Verbose-mode detail was included only when requested or needed to pinpoint offenders
- [ ] Frontmatter was extracted first-block-only, and the largest per-file value was sanity-checked for physical plausibility
