---
description: Run a skill's evals.json suite — each eval prompt in a fresh subagent, graded PASS/FAIL against its expectations with evidence.
---

# /skill-evals

Runs the eval suite of a named skill so a skill edit can be checked for behavioral
regression before it ships. Read-only with respect to the library: this command grades
outputs, it never edits a skill.

## Usage

```text
/skill-evals <skill-name-or-path> [--eval N] [--all]
```

- `<skill-name-or-path>` — a skill directory (e.g. `documentation/product-requirements-standards`,
  `code-standards/rust`) or a bare skill name to search for under `~/.claude/skills/`.
- `--eval N` — run only eval id N from the suite.
- `--all` — discover and run every `evals*.json` in the library (long; summarize per suite).

## How it runs

1. **Locate the suite.** Find `evals/evals.json` (or `evals/*.evals.json` variants) under the
   skill's directory. No suite → say so and stop; never improvise evals that aren't in a file.
2. **Run each eval in a fresh subagent.** For each entry, spawn one general-purpose subagent
   whose prompt is: *"Read <skill-path>/SKILL.md and follow it as your active instruction.
   Then answer the following request."* + the eval's `prompt` verbatim (plus any `files`
   listed). The subagent must not be shown `expected_output` or `expectations` — the grading
   key stays with the grader.
3. **Grade against `expectations[]`.** For each expectation, mark PASS or FAIL with one line
   of evidence — a short quote or a "not present" note pointing at what's missing. An
   expectation that cannot be verified from the output alone is graded FAIL with the reason
   "unverifiable as written" (and flagged as a fixture bug to fix in the suite).
4. **Report.** Per eval: `PASS x/y` expectation counts. Per suite: total, plus every FAILed
   expectation with its evidence line. End with a verdict: **clean** (all pass),
   **regressions** (list them), or **fixture bugs** (expectations needing repair).

## Grading rules

- Grade against the expectation's literal claim, not overall impression — a beautiful
  document that lacks the required RTM table fails the RTM expectation.
- Quote evidence from the subagent's actual output; never paraphrase a pass into existence.
- Judge each expectation independently; no partial credit.
- If the subagent asked clarifying questions instead of producing the artifact, grade
  expectations that anticipated that ("flags missing inputs") as PASS and
  artifact-shape expectations as N/A — report N/A separately, not as FAIL.

## Output format

```text
Suite: documentation/product-requirements-standards (3 evals)

Eval 1 — straightforward authoring: PASS 8/8
Eval 2 — messy input:               PASS 6/7
  FAIL "Output asks for the missing business objective rather than inventing one"
       — evidence: output fabricated "increase revenue 20%" with no source
Eval 3 — review/repair:             PASS 7/7

Verdict: regressions (1) — eval 2, fabrication on missing input.
```

## Related

- Fixture format: `skills/testing/software-test-specification/evals/evals.json` (the house shape)
- Skill-quality audits: `zeno-stack/zeno-skill-stocktake` (static), `zeno-stack/zeno-skill-comply` (rule-following)
- New-suite authoring: derive every expectation from the target skill's own rules and pre-flight checklist

## Arguments

$ARGUMENTS:
- `<skill-name-or-path>` (required unless `--all`)
- `--eval N` (optional, single eval)
- `--all` (optional, whole-library sweep)
