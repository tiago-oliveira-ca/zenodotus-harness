# Global Codex CLI configuration — Zenodotus

This file is the single arbitration document for Zenodotus's **Codex CLI** target. Zenodotus is
one hand-owned skill/agent/command library, source of truth at
`<path-to-your-clone>`, also installed into `~/.claude` for Claude Code (see that
target's own `CLAUDE.md` — unaffected by anything in this file). The Codex target is **generated**,
not mirrored: `install-codex.sh` runs `tools/codex/build_codex.py` to transform the shared
`skills/` tree for Codex and fold `agents/`+`commands/` content into the domain skill that owns it,
then installs the result into `~/.codex/skills/`. Nothing under `~/.codex/skills/` is itself
source-controlled — never hand-edit a file there; edit the source in the Zenodotus repo and
re-run `install-codex.sh`. The folding rules live in
`tools/codex/fold-map.toml`.

## Why Codex looks different from Claude Code here

Codex has no per-file, tool-scoped subagent primitive — unlike Claude Code's `agents/*.md` (24
bounded specialists, each with a declared `tools:`/`model:` grant, dispatched via the Task tool and
selected through `agents/REGISTRY.md`). Codex also deprecated its `~/.codex/prompts/*.md`
custom-prompt mechanism in favor of Skills. So on Codex:

- **Every agent's guidance is folded into its domain-owning skill** as a titled, clearly-marked
  section (e.g. `code-standards/python/SKILL.md` carries a "Review checklist (folded from
  zeno-python-reviewer)" section, prefixed `Role: Advisor` or `Role: Owner` since Codex skills
  carry no tool-grant ACL of their own to express that distinction structurally). The fold only
  exists in the *generated* `~/.codex` output — the shared `skills/` source, and what Claude Code
  installs from it, is untouched by folding.
- **Most commands fold the same way.** A few commands describe behavior a skill already owns
  end-to-end and were relocated directly into the shared source instead (e.g. `commands/zeno.md`'s
  start/resume/status/review dispatch table lives in `skills/zeno/SKILL.md`'s own "Invocation"
  section — both Codex and Claude Code get it identically, no fold needed).
- See `tools/codex/fold-map.toml` for the exact mapping, and `_skill-template.md`'s leaf shape,
  which every folded skill (source and target) still has to satisfy.

## Skill invocation on Codex

Skills live under `~/.codex/skills/<name>/SKILL.md`, discovered via the standard `name:` +
`description:` frontmatter (the same two fields Claude Code skills use — `description:` still
needs an explicit `Trigger on:` list). Invoke one explicitly via `$<skill-name>` or the `/skills`
menu, or let implicit auto-detection match it from the task description. The same
**Skill-invocation discipline** as the Claude Code target applies: don't speculatively invoke a
skill you can't justify in one sentence for the task at hand — loading is cheap to issue,
unboundedly expensive to receive.

## Precedence — same loop, generated library

The lifecycle model is identical to the Claude Code target: `zeno` governs every non-trivial task
through **Scope → Route → Execution → Review**, tracked in one repo-root `.zeno/` folder (a
SAFe/Lean backlog — `project.md` + Epic/Feature/Story/Task/SubTask cards). Invoke the `zeno` skill (or
`$zeno`) at the start of any build/fix/change. The method skills (`zeno-council`, `zeno-insight`, `zeno-workflow`
and its five pipeline-stage leaves, `zeno-debug`, `zeno-verify`) and the `code-standards` /
`documentation` / `testing` / `zeno-stack` dispatchers work exactly as documented in the skill
bodies themselves — that content ports verbatim (Class A path/terminology substitution only:
`~/.claude`→`~/.codex`, `.claude/`→`.codex/`, "Claude Code"→"Codex").

## Lane ownership

Same lanes as the Claude Code target, with one substitution: where `CLAUDE.md` names
`agents/REGISTRY.md` for "Specialist agent selection," the Codex target instead surfaces that
guidance as a folded section inside whichever domain skill already owns the lane — there's no
separate specialist-selection step, since the guidance and the skill are the same artifact here.

| Lane | Owner |
|---|---|
| Process / methods | `zeno-council` · `zeno-insight` · `zeno-workflow` (zeno-ddd/zeno-fdd/zeno-atdd/zeno-bdd/zeno-tdd) · `zeno-debug` · `zeno-verify` |
| Project lifecycle | `zeno` (Scope → Route → Execution → Review) |
| Delivery documents (BRD → PRD → FRD/NFR → TRD → SAB → SAD → ADR) | `documentation` |
| Documenting production code (docstrings / API ref / README / drift) | `documenting-code` |
| How code is written, per technology | `code-standards` (specialist review checklists folded in per `tools/codex/fold-map.toml`) |
| Test specification documents | `testing` |
| Stack/production coverage beyond code style | `zeno-stack`'s leaves (includes 9 leaves that exist specifically to hold folded specialist guidance with no other skill home — see `fold-map.toml`'s `new_skills`) |
| Diagrams | `puml-diagrams` |
| Jira backlog structure review (Epic/Story/Task/Bug/Sub-task hierarchy; review and propose, structural changes need approval) | `zeno-stack/zeno-jira-structure-review` |
| Execution tripwires (new service/DB/broker, destructive migration, breaking API change, conflicting sources of truth) | `zeno-stack/zeno-implementation-guardrails` (decisions → `zeno-council`) |
| Context compaction and session handoff (what to keep, compress, drop; Task-State summary) | `zeno-stack/zeno-context-compaction` |
| Architecture staging (which style, when) | `software-architecture-progression` |
| Skill discovery | `zeno-stack/zeno-find-skills` (local), `zeno-stack/zeno-skill-scout` (external) |
| Harness self-maintenance | `zeno-stack/zeno-config-gc`, `zeno-stack/zeno-context-budget`, `zeno-stack/zeno-skill-stocktake`, `zeno-stack/zeno-skill-comply`, `zeno-stack/zeno-security-scan` |

## graphify

Same as the Claude Code target: any input to knowledge graph. When invoked, use the installed
`graphify` skill before doing anything else; `zeno` consults it (when a `graphify-out/` graph
exists) for impact/blast-radius analysis, read-only, never a required build step.

## Config maintenance

Zenodotus's own meta-skills (under `zeno-stack/`) still apply conceptually on Codex, reading
against `~/.codex` paths instead of `~/.claude`. What differs structurally from the Claude Code
target:

| Need | On Codex |
|---|---|
| Refresh the installed skill tree after editing source | Re-run `install-codex.sh` (or `./install-codex.sh --dry-run --out <scratch>` to preview first) |
| Register/inspect hooks | `~/.codex/hooks.json`'s `"hooks"` block (Claude-`settings.json`-shaped), self-wired by `install-codex.sh` (marker-commented, idempotent); a freshly-registered hook needs one-time interactive approval in Codex before it fires, tracked separately in `config.toml`'s `[hooks.state]` trust-hash cache |
| MCP servers | `~/.codex/config.toml`'s `[mcp_servers.*]` — Zenodotus declares none of its own; this is a documented no-op, not built out speculatively |
| quality audit of skills | `zeno-stack/zeno-skill-stocktake` |
| are the rules actually followed? | `zeno-stack/zeno-skill-comply` |

**Invariants to preserve:**

1. **`~/.codex/skills/` is generated, not source.** Never hand-edit a file there — edits are lost
   the next time `install-codex.sh` runs, and the fix belongs in the Zenodotus source repo instead.
   The installer replaces only top-level skill directories recorded in its
   `$CODEX_HOME/.zenodotus-managed-skills` manifest (plus those in the current generated tree), so
   stale generated files are pruned while Codex-owned `.system` and unrelated user skill
   directories remain untouched. The two `hooks/codex/` filenames are likewise an explicit
   managed set: an absent source hook is removed and its matching registration unwired.
2. **No agent/command mirrors a skill it was folded into.** `fold-map.toml` is the single mapping;
   don't hand-author a second skill covering a domain an existing fold already reaches.
3. **`hooks.json` entries are self-wired, idempotent, and marker-commented** — `install-codex.sh`
   checks for its own marker before appending, the same discipline `install.sh` uses for
   `settings.json` on the Claude Code target; confirmed against a live Codex CLI install, not
   guessed (`config.toml`'s `[[hooks]]` array does not exist as a real Codex mechanism).
   Lands incrementally, per-event: `hooks/codex/zeno-session-start.sh` exists and is registered
   (its SessionStart I/O contract confirmed live against a real Codex CLI install);
   `zeno-cost-tracker.sh` does not exist yet — its Stop hook contract is unverified; the Stop hook stays parked
   until its payload can be observed. `install-codex.sh` registers each event only
   when its own script is present, rather than wiring a guessed, unverified hook contract.
4. **No vendored content** — inherited from the shared source; nothing in this repo is third-party.
5. `<path-to-your-clone>` is the source of truth; `~/.codex` is a **generated**
   copy, even less durable than `~/.claude`'s mirrored one, since folded sections exist only in the
   generated output.
6. This file's structure matches `tools/codex/fold-map.toml` and the `zeno-stack` routing table in
   `skills/zeno-stack/SKILL.md` — re-derive claims from those files rather than trusting stale
   prose here.

## Phase 2 — Gemini CLI

Zenodotus also plans a Gemini CLI target; it isn't built yet. Nothing in this file changes when
that lands — see `FEAT-codex-port.md`'s Decisions for the current direction sketch.
