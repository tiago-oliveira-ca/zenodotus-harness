---
name: zeno-skill-stocktake
description: >
  Audits Claude or Codex skills and commands for quality using a deterministic scan script plus
  AI holistic judgment, with two modes — Quick Scan (changed skills only, 5-10 min) and
  Full Stocktake (complete review via sequential subagent batches, 20-30 min). Produces
  per-skill verdicts (Keep/Improve/Update/Retire/Merge) with self-contained, evidence-
  backed reasons. Use when auditing skill/command quality across ~/.claude, $CODEX_HOME/skills,
  or a project's generated skill tree. Trigger on: "audit my skills", "audit Codex skills",
  "skill stocktake", "which skills are
  stale", or "skill quality review".
---

# Skill Stocktake

Audit a selected Claude or Codex skill tree against a quality checklist plus AI holistic
judgment. Invoked directly by name or by any of its trigger phrases above. Two modes:
**Quick Scan** for recently changed skills, **Full Stocktake** for a complete review.

## Scope

Paths are resolved relative to the directory the command is invoked from:

| Path | Description |
|---|---|
| `~/.claude/skills/` | Global Claude skills (default target) |
| `$CODEX_HOME/skills/` | Global Codex-generated skills (`~/.codex` when unset) |
| `{cwd}/.<target>/skills/` | Project-level skills (if the directory exists) |

Select the target explicitly when auditing Codex: `scan.sh --target codex` and
`quick-diff.sh RESULTS_JSON --target codex`. The scripts also accept
`SKILL_STOCKTAKE_TARGET=codex`. Claude remains the default for compatibility. Codex output is
generated: findings about generated content should be fixed in the Zenodotus source tree and
then regenerated with `install-codex.sh`, never hand-edited under `$CODEX_HOME/skills`.
Phase 1 explicitly lists the selected target and which paths were found and scanned.

To include project-level skills, `cd` into that project's root before running. If it has
no `.claude/skills/`, only global skills and commands are evaluated.

## Modes

| Mode | Trigger | Duration |
|---|---|---|
| Quick Scan | `results.json` exists (default) | 5-10 min |
| Full Stocktake | `results.json` absent, or a full stocktake explicitly requested | 20-30 min |

Results cache: `~/.claude/skills/zeno-stack/zeno-skill-stocktake/results.json`.

**The cache carries a `files` map** (`{path: sha256}` for every scanned `*.md`) alongside
`skills`. `quick-diff.sh` compares against it and reports each changed file *with its owning
skill*, so editing a `references/` or `frameworks/` file correctly re-triggers the skill that
ships it. The cache keys on every `*.md` the scan lists, so a reference file re-triggers only its
owning skill. A cache without a `files` map falls
back to the per-skill hashes, which makes the first run after upgrading a full re-evaluation.

**Change detection is content-hash based, not mtime.** `install.sh` copies with
`cp -R` and no `-p`, so every install rewrites every file's timestamp to the same value — an
mtime comparison reports "everything changed" on every run, which silently made Quick Scan
useless. `scan.sh` records a `sha256` per file and `quick-diff.sh` compares those. A cache written
before hashing existed (no `sha256` field) is treated as changed, so the first run after upgrading
is a full re-evaluation by design.

`scan_summary` reports `files` (every `*.md`, including `references/`) and `skills` (`SKILL.md`
only) as separate counts — conflating them inflated the inventory an audit reasons over.

## Quick Scan flow

Re-evaluates only skills changed since the last run.

1. Read the cached `results.json`.
2. Run `bash ~/.claude/skills/zeno-stack/zeno-skill-stocktake/scripts/quick-diff.sh
   ~/.claude/skills/zeno-stack/zeno-skill-stocktake/results.json [--target codex]` — the project
   dir is auto-detected from `$PWD/.<target>/skills`; pass it explicitly only if needed.
3. If the output is `[]`, report "No changes since last run" and stop.
4. Re-evaluate only the changed files using the same Phase 2 criteria as Full Stocktake.
5. Carry forward unchanged skills from the previous results.
6. Output only the diff.
7. Save: `bash ~/.claude/skills/zeno-stack/zeno-skill-stocktake/scripts/save-results.sh
   ~/.claude/skills/zeno-stack/zeno-skill-stocktake/results.json <<< "$EVAL_RESULTS"`.

## Full Stocktake flow

### Phase 1 — Inventory

Run `bash ~/.claude/skills/zeno-stack/zeno-skill-stocktake/scripts/scan.sh [--target codex]` — it
enumerates skill files, extracts frontmatter, and collects UTC mtimes. Project dir is
auto-detected from `$PWD/.claude/skills`; pass it explicitly only if needed. Present the
scan summary and inventory table:

```
Scanning:
  ✓ ~/.claude/skills/         (17 files)
  ✗ {cwd}/.claude/skills/    (not found — global skills only)
```

| Skill | Description |
|---|---|

### Phase 2 — Quality evaluation

Launch a **general-purpose agent** with the full inventory and checklist:

```text
Agent(
  subagent_type="general-purpose",
  prompt="
Evaluate the following skill inventory against the checklist.

[INVENTORY]

[CHECKLIST]

Return JSON for each skill:
{ \"verdict\": \"Keep\"|\"Improve\"|\"Update\"|\"Retire\"|\"Merge into [X]\", \"reason\": \"...\" }
"
)
```

The subagent reads each skill, applies the checklist below, and returns per-skill:
`{ "verdict": ..., "reason": "..." }`.

**Chunk guidance**: ~20 skills per subagent invocation, to keep context manageable. Save
intermediate results to `results.json` (`status: "in_progress"`) after each chunk. After
all skills are evaluated, set `status: "completed"` and proceed to Phase 3. If startup
finds `status: "in_progress"`, resume from the first unevaluated skill.

**Checklist per skill:**
- Content overlap with other skills checked.
- Overlap with MEMORY.md / CLAUDE.md checked.
- Freshness of technical references verified (WebSearch if tool names/CLI flags/APIs are
  present).

**Verdict criteria:**

| Verdict | Meaning |
|---|---|
| Keep | Useful and current |
| Improve | Worth keeping, specific improvements needed |
| Update | Referenced technology is outdated (verify with WebSearch) |
| Retire | Low quality, stale, or cost-asymmetric |
| Merge into [X] | Substantial overlap with another skill; name the merge target |

Evaluation is **holistic AI judgment**, not a numeric rubric. Guiding dimensions:
**Actionability** (code/commands/steps enabling immediate action), **Scope fit** (name,
trigger, and content aligned — not too broad or narrow), **Uniqueness** (value not
replaceable by MEMORY.md/CLAUDE.md/another skill), **Currency** (technical references work
in the current environment).

**Reason quality** — every `reason` must be self-contained and decision-enabling:
- Never write "unchanged" alone — restate the core evidence.
- **Retire**: state the specific defect found and what covers the same need instead.
  Bad: `"Superseded"`. Good: `"disable-model-invocation: true already set; superseded by
  zeno-debug which covers all the same patterns plus root-cause tracing. No unique
  content remains."`
- **Merge**: name the target and describe what content to integrate. Bad: `"Overlaps with
  X"`. Good: `"42-line thin content; Step 4 of chatlog-to-article already covers the same
  workflow. Integrate the 'article angle' tip as a note in that skill."`
- **Improve**: describe the specific change (section, action, target size). Bad: `"Too
  long"`. Good: `"276 lines; Section 'Framework Comparison' (L80-140) duplicates
  ai-era-architecture-principles; delete it to reach ~150 lines."`
- **Keep** (unchanged content, carried forward): restate the original rationale, never
  "unchanged" alone. Good: `"mtime updated but content unchanged. Unique Python reference
  explicitly imported by rules/python/; no overlap found."`

### Phase 3 — Summary table

| Skill | Verdict | Reason |
|---|---|---|

### Phase 4 — Consolidation

1. **Retire/Merge**: present, per file, the specific problem found (overlap, staleness,
   broken references), the alternative that covers the same functionality (for Retire:
   which skill/rule; for Merge: target file + content to integrate), and the impact of
   removal (dependent skills, MEMORY.md references, workflows affected) — before
   confirming with the user.
2. **Improve**: present the specific change and rationale (e.g. "trim 430→200 lines,
   sections X/Y duplicate python-patterns"); the user decides whether to act.
3. **Update**: present updated content with the sources checked.
4. Check MEMORY.md line count; propose compression if >100 lines.

## Results file schema

`~/.claude/skills/zeno-stack/zeno-skill-stocktake/results.json`:

`evaluated_at` must be the actual UTC completion time via `date -u
+%Y-%m-%dT%H:%M:%SZ` — never a date-only approximation like `T00:00:00Z`.

```json
{
  "evaluated_at": "2026-02-21T10:00:00Z",
  "mode": "full",
  "batch_progress": { "total": 80, "evaluated": 80, "status": "completed" },
  "skills": {
    "skill-name": {
      "path": "~/.claude/skills/skill-name/SKILL.md",
      "verdict": "Keep",
      "reason": "Concrete, actionable, unique value for X workflow",
      "mtime": "2026-01-15T08:30:00Z"
    }
  }
}
```

## Notes

Evaluation is blind — the same checklist applies regardless of a skill's origin. Archive/
delete operations always require explicit user confirmation (see `zeno-config-gc` for the
actual soft-delete mechanics). No verdict branches by skill origin.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Full rescan on every invocation | Quick Scan mode re-evaluates only changed files |
| "Unchanged" as the entire reason field | Always restate the core evidence, even for Keep |
| Deleting a Retire-verdict skill immediately | Present evidence + alternative, require explicit user confirmation |
| Numeric-rubric scoring | Holistic judgment across Actionability/Scope fit/Uniqueness/Currency |
| `T00:00:00Z` date-only timestamps | `date -u +%Y-%m-%dT%H:%M:%SZ` for `evaluated_at` |
| Evaluating >20 skills in one subagent call | Chunk at ~20 skills per invocation, checkpoint progress |
| Skipping the currency check on skills with tool/CLI references | WebSearch to verify before verdicting Keep |

## Pre-flight checklist — run before delivering any stocktake report

- [ ] Phase 1 explicitly lists which scan paths were found (global / project)
- [ ] Correct mode (Quick Scan vs Full) was selected based on `results.json` presence
- [ ] Every verdict's reason is self-contained — no bare "unchanged" or "superseded"
- [ ] Retire/Merge verdicts name a concrete alternative and describe removal impact
- [ ] `evaluated_at` was set via `date -u +%Y-%m-%dT%H:%M:%SZ`, not approximated
- [ ] `results.json` was saved/updated at the correct path after evaluation
- [ ] No skill was archived or deleted without explicit user confirmation
