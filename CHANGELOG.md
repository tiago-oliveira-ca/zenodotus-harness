## 2026-10-23 — Council stops only on blocking unknowns (STORY-council-over-blocking)

The first `/skill-evals` run showed `zeno-council` still ended at a 7-question round on "requirements are
settled, propose architectures" (council eval 5): the agent rated hosting platform and SSO protocol
`CRITICAL`, so the gate never opened. The impact label was doing the work that decision relevance should do.

`zeno-council` now has a **blocking test**: an unknown blocks only if a plausible answer would change which
option is recommended, or add a hard requirement (compliance scope, sensitive or regulated data handling, an
irreversible or destructive choice, a new external runtime dependency the user has not accepted). Every other
unknown is a recorded `ASSUMPTION` with a default, carried into the recommendation as a revisit condition.
"Settled" never licenses assuming sensitive-data handling or a destructive operation.

- **Measured.** Council eval 5 went from PASS 1/5 (4 N/A) to 5/5 (two options, Challenger, trade-off table,
  recommendation, revisit triggers). A new counter-example, a *settled* payments request, still stops and asks
  how card data is handled. Headless cold-start runs (payments, queue, settled payments) still load
  `zeno-council` right after `zeno`, ask first and write no code; the off-by-one with "run the full council"
  stays Lite.
- **First wiring regressed one thing and was corrected.** Stating the test inline in `zeno` step 0 and both
  hooks let one run apply it from memory without loading the skill or using its question format. The definition
  now lives only in the skill; `zeno` and the hooks (still byte-identical) say "blocking questions" and point to it.
- Open: ❓ / ➡️ marker adherence is not guaranteed (two of three Full text-only runs wrote "Q1 -" prose); an
  anti-pattern row was added, nothing mechanical enforces it.
- Resume review removed residual unconditional-stop instructions from the council's enforcement sections,
  aligned `zeno`'s entry-point/red-flag wording and the USAGE gate table, and reconciled the stale Gate 3
  resume pointer against the committed Tasks.

## 2026-10-24 — Context compaction leaf (STORY-context-compaction)

New leaf `zeno-stack/zeno-context-compaction`: a KEEP / COMPRESS / DROP rubric for compacting or handing
off a session, with a never-drop list (instructions, approvals, irreversible actions, branch state),
verbatim exact values, durable-state detection (point to the `.zeno/` card, ADR or issue instead of
copying), a priority order, "recency is not a retention rule", and a Task-State summary shape. Routed from
the `zeno-stack` dispatcher and the `CLAUDE.md` / `AGENTS.md` lane tables.

- Checked against the Claude Code docs: project-root `CLAUDE.md` is re-injected after `/compact`, and
  `SessionStart` with the `compact` matcher can inject context; nothing documented lets a `CLAUDE.md`
  section steer the summarizer. So the rubric is passed through `/compact <instructions>`, and no
  `CLAUDE.md` block or hook change was made.
- The source prompt was truncated after "Open Issues"; the leaf's last section is a short placeholder for it.

## 2026-10-23 — Eval fixtures repaired after the first /skill-evals run (STORY-fix-eval-fixtures)

The first `/skill-evals` run over `zeno-council`, `zeno-jira-structure-review` and
`zeno-implementation-guardrails` (17 evals, 68 assertions: 64 pass, 4 N/A, 0 fail) found four fixture
bugs, none in a skill. Fixed here, fixtures only:

- All three suites used `assertions` where the house shape and the command read `expectations`; now plain
  `expectations` strings.
- Council eval 5 said "requirements are settled" but gave no purpose, workflows or data, so the council
  correctly blocked and four artifact-shape assertions were N/A. The prompt now describes an expense-approval
  tool with its workflows, data and auth.
- Jira eval 5 said "Here is my backlog export (pasted)" and pasted nothing. The export is now inline, plus
  one expectation that checks the review names concrete defects from it.
- Two loose assertions tightened (council eval 1: what counts as "recommending an architecture"; guardrails
  eval 2: a labeled later-step `DROP COLUMN` sketch is allowed, a ready-to-run migration is not).

## 2026-10-23 — Implementation guardrails leaf (STORY-zeno-implementation-guardrails)

New leaf `zeno-stack/zeno-implementation-guardrails`, loaded at Gate 3 beside the stack leaf. It holds only
what nothing else in the library owned: a source-of-truth ranking (user > Jira issue > accepted ADRs >
architecture docs > repo instructions > code conventions > own judgment; conflicts are reported, not silently
resolved), three named tripwires (`ARCHITECTURE IMPACT DETECTED` with an `ADR PROPOSAL`, `DATA MIGRATION
RISK`, `BREAKING API CHANGE`), test-integrity additions, and a dependency checklist. Everything else in the
36-section source prompt is a pointer to its existing owner (`zeno-tdd`, `zeno-api-design`, `zeno-git-workflow`,
`zeno-verify`, `zeno-council`, `code-standards`): a fit-search found most of it already owned, and copying it
would have repeated the duplication drift of PRs #47/#48.

- **Measured.** Headless runs on fixtures: the baseline wrote and committed a `DROP COLUMN` migration against a
  repo whose README says production holds ~2M orders, and silently removed a field from a finance export that
  read it. The API-rename and Redis-cache prompts were already handled by `zeno-api-design` and the council,
  which is why those are pointers. After the change the migration prompt writes nothing and asks first. The
  agent did not load the leaf itself: the concept reached it through `zeno`'s Gate 3 duty line and a
  `CLAUDE.md`/`AGENTS.md` lane row, so the duty line was tightened to name the flag in the reply.
- `zeno-stack`'s description shed the "cross-session management" phrase to stay at the length ceiling; the
  routing table still lists that leaf. The architecture diagram's leaf count is now derived from the directory (47).

## 2026-10-23 — Jira structure review leaf (STORY-zeno-jira-structure-review)

New leaf `zeno-stack/zeno-jira-structure-review`: reviews a Jira backlog's hierarchy (Epic → Story /
Task / Bug → Sub-task), flags wrong types and parents, oversized and undersized tickets, duplicates and
weak ticket quality, and proposes a corrected hierarchy in a fixed report. It applies only safe edits;
structural changes need approval each time, and nothing is deleted without explicit authorization. It
works from a pasted export until the Atlassian MCP is authenticated.

- **Vocabulary conflict surfaced and arbitrated.** `development-planning-standards` defines a Task as a
  step inside a Story, while Jira makes Tasks peers of Stories. Both skills now say that planning
  standards' Task = a Jira Sub-task, and the new leaf wins on Jira issue types and parents.
- **Measured.** Headless run on a fake export with "just fix everything": baseline closed an Epic,
  retyped a Story to Spike, moved tickets and left Tasks under a Story; with the skill loaded, the report
  followed the fixed format and applied nothing. An unprompted run first never found the leaf behind the
  `zeno-stack` dispatcher; a lane row in `CLAUDE.md` / `AGENTS.md` fixed discovery (the run then loaded
  `zeno-stack` and the leaf). The `zeno-architecture` diagram's stale leaf count (44) is corrected to 46.

## 2026-10-23 — Architecture Council opens every Scope (STORY-zeno-council)

New flat method skill `zeno-council`, run as Gate 1 step 0 before `zeno-insight`. Eight inline roles
(Chief Architect, Business/Domain, Application, Data, Platform/Cloud, Security, SRE, Challenger)
question before they design. Depth scales so "always" does not become ceremony on small work:

- **Lite** — Story-tier work that adds no new boundary, data store, integration, sensitive data,
  security posture or NFR: no questions, one line on the card. A formally worded request does not
  upgrade it.
- **Full** — otherwise: classified facts/assumptions, up to 7 `❓ / ➡️` questions per round, **stop
  for answers**, then 2-3 options, a debate with an adversarial Challenger, a qualitative trade-off
  table, and a recommendation with rejected alternatives and revisit triggers.

It shares `zeno-insight`'s question format and the card's Decisions log (one backlog, not two) and
replaces insight's step 5 only for architecture-level choices. Wired into `zeno` Gate 1,
`zeno-insight`, `zeno-ddd`, `software-architecture-progression`, `agents/REGISTRY.md`, `CLAUDE.md`,
`AGENTS.md`, `/zeno`, and both SessionStart hooks (kept byte-identical). Roles are persona sections,
not new agents; the registry stays at 24.

**Measured, not assumed.** A cold-start test (`claude -p`, payment-service and message-queue prompts)
found the first wiring did not work: agents wrote "Council Lite+: new integration, sensitive data"
on their own card and then built the service without asking a question, never loading the skill.
Step 0 and the hook sentence were made imperative (Full evidence means invoke `zeno-council`, ask
round 1, stop; a headless run ends with the questions and its assumptions). Re-run: both Full
prompts invoke the skill second, ask a round, and write no code; the formal-wording off-by-one prompt
stays Lite. One unrelated observation left open: a plain one-line bug-fix prompt skipped the loop
entirely in one sample.

## 2026-09-04 — Prune stale Codex-managed installation content (STORY-codex-install-prune-stale)

`install-codex.sh` now replaces generated top-level skill directories exactly and persists their
names in `$CODEX_HOME/.zenodotus-managed-skills`, removing obsolete managed content without
touching Codex-owned `.system` or unrelated user skills. It also removes absent Zenodotus hook
scripts and their exact matching registrations, fixing the stale cost-tracker hook observed after
PR #49's sync. An isolated end-to-end regression test covers pruning, preservation, hook
reconciliation, and repeat-install idempotency.

## 2026-09-04 — Harden Codex generator output safety (STORY-codex-generator-safety)

The Codex generator now rejects output paths overlapping the source repository or active Codex
installation and only overwrites existing directories carrying its source-bound ownership marker.
It also treats missing fold targets as fatal generation errors. Added isolated regression coverage
for these rules and corrected `AGENTS.md` to use the supported
`./install-codex.sh --dry-run --out <scratch>` preview command.

## 2026-08-18 — /zeno becomes a dispatcher instead of a second copy (STORY-zeno-command-drift)

`commands/zeno.md` carried a current four-gate header over an old-model body. The stocktake found
six live defects, all of them copies that had drifted from their originals:

- **Gate 2 was missing entirely** from `start` — Scope → create cards → "stop at the Execution
  gate", omitting the mandatory FDD/ATDD/BDD/Task-breakdown-for-every-Story pass the loop requires
  before Gate 3 opens.
- **Abandoned `Done` vocabulary** in four places, where every card template and
  `project-template.md` define the column as `Closed` and the status as `closed`.
- **Half the migration**: `start` invoked only the legacy `THREAD.md` recipe and omitted the
  `.project/core.md` rename, so a `start` could return with `.project/` still on disk.
- **"DDD/FDD" bundled as one unit** — the pre-split model; DDD is Gate 1, FDD is Gate 2 — with no
  mention of the Task-breakdown step or its mandatory trailing documentation Task.
- **"Five card types" followed by six paths**, and a "no directory trees beyond this layout" clause
  that **forbade `.zeno/docs/archive/`** — a tree the loop makes mandatory and which already holds
  30 cards in this repo.
- No mention of Gate 2's branch check, reconcile or skill-currency steps, nor Gate 4's CHANGELOG
  entry, documentation check or verify-merge-before-archive.

**Root cause: the command restated the skill instead of dispatching to it.** Every defect above is
a second copy that fell behind its original — the same duplication failure that produced the ghost
`Stage` field (PR #47) and the archived-tools staleness.

Rewritten to what a command uniquely owns: its frontmatter, how to resolve the repo root, one line
per token saying what it dispatches to, and an explicit statement that the skill is authoritative
and this file is the bug if they disagree. Every restated rule is deleted rather than corrected.

Chose this over regenerating the token table verbatim from the skill: a verbatim copy is still a
copy — correct the day it lands, stale on the next skill edit, which is exactly this file's
history. A one-line summary plus a pointer cannot drift the same way, because it no longer asserts
the details that change.

Verified: Gate 2 present; zero `Done`/`done` vocabulary; both migration recipes named; the
`docs/archive/` prohibition gone; 47 → 38 lines; and four rules sampled from the skill
(`never rewrite history`, `WIP limit is 1`, `must not skip Scope`, the `Status` vocabulary) now
appear **0 times** in the command and 1-2 times in the skill — no second copy remains.

## 2026-08-18 — Remove the ghost `Stage` card field (STORY-ghost-stage-field)

The card templates abolished a `Stage` field and say so explicitly — stage "is read off this card's
own section content … **not a separate field**" — and `zeno-workflow/SKILL.md` documents that
derivation as authoritative. Verified: **zero of the six card templates define `Stage`**. Yet 21
occurrences across five files instructed otherwise: `zeno-ddd-guide` (3), `zeno-fdd-guide` (4),
`zeno-atdd-guide` (6) and `zeno-bdd-guide` (6) all instructed *setting* it, and `commands/zeno.md`
(2) instructed *reading* it on resume and conflated it with the real `Status` field.

The sharpest consequence: `zeno-bdd-guide`'s Proof criteria, Decision authority and Constraints
were all written in terms of that field, so the agent's stated success condition could never be
satisfied against a real card — unverifiable by construction.

Each instruction is replaced with the mechanism that exists, keeping two things distinct that
`commands/zeno.md` had merged: **stage is implicit** (which section is still empty — empty
Acceptance criteria → ATDD, filled but Scenarios empty → BDD, Scenarios filled but Task list empty
→ Task breakdown), while **`Status` is a real field** with a defined vocabulary
(`backlog|development|testing|closed`). `resume` now re-enters at the stage the card's content
shows rather than looking for a field that was never written.

Deliberately did **not** add a `Stage` field to the templates to make the five consumers correct.
The templates' design is better: a derived signal cannot drift against the content it describes,
whereas a stored one can — and the drift this entry fixes is exactly that failure. Five consumers
were wrong, not six producers.

Counter-example held: the real `Status` field survives in all six templates and in `commands/zeno.md`,
which now names its vocabulary explicitly rather than pairing it with the ghost.

## 2026-08-18 — Fix the stocktake's P0s and live bugs (STORY-stocktake-p0-live-bugs)

A full stocktake (3 evaluators, ~100 components) found 26 issues. **Five were introduced or left
half-landed by this session's own PRs (#35-#45)**, and three were live-breaking. All eight fixed,
each verified by execution rather than by reading — which is precisely how they were missed.

**Mine, from the last two days:**
- **`extract-trace.py` could not see subagent transcripts** — the one thing `zeno-skill-comply`
  exists to read. `find_transcripts()` did a non-recursive `os.listdir()` on `<slug>/`, missing
  `<slug>/<session-id>/subagents/agent-*.jsonl`; 127 such files existed under one project while
  the resolver reported 15. The documented method therefore returned the *parent* timeline, where
  each spawned scenario is a single opaque `Agent` call. Now walks the tree, labels each
  transcript session/subagent, and adds `--scope all|parent|subagents`. The docstring's claim that
  both layouts were "verified against real transcripts, not assumed" is **corrected in place**
  rather than deleted: the Codex layout was verified, the Claude subagent layout was not.
- **`quick-diff.sh` reported 60 false positives on every run.** PR #40 fixed the mtime half and
  left the scope mismatch: the cache keyed on 89 `SKILL.md` paths while the scan listed all 149
  `*.md`. Rather than filtering candidates down to `SKILL.md` (which would have silenced the noise
  while leaving `references/` edits invisible), the cache now carries a `files` map for every
  scanned file and `quick-diff` reports each change **with its owning skill** — so editing a
  reference file correctly re-triggers the skill that ships it. Verified both ways: `[]` on an
  unchanged tree, and a planted edit to `zeno/references/story-template.md` attributing to `zeno`.
- **Both SessionStart hooks emitted invalid JSON on the bash fallback.** PR #42 added five quoted
  phrases to `BASE`; the `printf` path interpolated them unescaped, failing to parse at the first
  `"quick"`. Only the python3 branch had ever been exercised, and the comment above it still
  asserted "no JSON metacharacters". Both hooks now escape, and the comment says what is actually
  true. Verified with `python3` stubbed to exit 1.
- **A `work_mem` contradiction** left by PR #40's content move (8MB then 16MB in one section).
- **`c_emp` vs the file's own `CUR_` rule** in oracle-plsql §4.4, introduced while fixing that
  section's cursor logic on 2026-08-16.

**Live bugs:**
- **The cost tracker had no `claude-opus-5` key**, so 74 of 444 real rows (16%) priced at the
  3/15 fallback instead of ~15/75. Added, with the prefix matcher verified across seven model ids.
  Separately, cache-write tokens priced at **$0** whenever a usage record lacked the optional
  `cache_creation` breakdown — those tokens were reported in the row and charged nothing; they now
  price at the 5m rate. (Already-logged rows keep their historical values.)
- **`zeno-config-gc` shipped a command that truncates a live settings file to 0 bytes.** It piped
  `jq` output over the file it was reading; `jq` exits 5 on the null `.permissions.allow` (which
  lives in `settings.json` here, not `settings.local.json`), by which point the shell had already
  emptied the target — wiping both hook registrations. Now: locate the file that actually holds
  the key, write to a temp file, validate it parses, then `mv`. Plus a pre-flight guard.
- **`zeno-redis-patterns`' canonical rate-limiter Lua was cluster-unsafe** — it constructed
  `key .. ':seq'`, a key never declared in `KEYS`, which Redis Cluster rejects (CROSSSLOT) in the
  exact topology the skill's description advertises. Both keys are now declared, with hash-tag
  guidance and a matching invocation example.

The through-line: every one of these passes a read-only audit and fails an execution test. The
prior stocktake checked template shape and closed clean; this one ran the scripts, stubbed the
fallback branch, and read the actual cost log.

## 2026-08-17 — extract-trace.py learns Codex's transcript layout (STORY-codex-transcript-resolver)

`zeno-skill-comply`'s trace extractor resolved only Claude Code's `~/.claude/projects/<slug>/`
layout, so the quota-blocked Codex cold-start runbook had to tell its future operator to find the
file by hand. Built against the real format — 90 live rollouts inspected before any code — per the
Codex Story's own rule that an I/O contract must be confirmed, never guessed.

What the format actually is: rollouts live at `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`
with **no per-project folder**, so resolution reads each rollout's `session_meta` line (head only)
and matches `payload.cwd`. Tool calls are `event_msg` lines with `payload.type == "item_completed"`
carrying `CommandExecution` (shell, wrapped as `["/bin/zsh","-lc",...]`) or `FileChange`.

**Codex has no `Skill` tool call.** On Claude, loop engagement is `Skill(zeno)`; on Codex it reads
as a `CommandExecution` touching a `SKILL.md` or a `FileChange` creating `.zeno/` cards — so
ordering rules do not transfer verbatim between hosts. That is documented in the script's docstring
and the runbook rather than left as a trap. The emitted tool names stay host-native for the same
reason: a fake-uniform vocabulary would hide a real difference.

Verified on real data: 40-tool-call rollout parsed correctly, piped unmodified into
`check-order.py` (`[PASS] CommandExecution~SKILL.md:FileChange @1 before @10`), `--host auto` and
content-based detection both working, and the Claude path unchanged.

## 2026-08-17 — Codex hook parity: the hardened mandate reaches both targets (STORY-codex-hook-parity)

PR #42 hardened the SessionStart mandate so the loop survives adversarial prompts — and edited
only the Claude-target hook. `hooks/codex/zeno-session-start.sh` is a deliberate byte-identical
port (verified live against Codex CLI 0.147.0) and was left carrying the old, weaker text: the one
measured to be bypassed 4/4. Codex users would have kept exactly the ungoverned behavior that fix
exists to remove.

`BASE` is now byte-identical across both targets, and the Codex copy carries a KEEP-IDENTICAL
warning naming this incident, so the next editor is told to mirror the change.

**Why the existing guard missed it.** PR #40 introduced a referrer sweep — grep for what changed,
fix every file that points at it — and it has since caught several stale pointers. It could not
catch this: `hooks/codex/` does not *reference* the Claude hook, it *duplicates* it. The sweep
finds referrers; it is structurally blind to copies that must move in lockstep. Recorded on the
card rather than papered over, with a generalised duplicate-content check left as a candidate
Story if it recurs.

Verified: `BASE` diff empty; the Codex hook emits valid SessionStart JSON (1528 chars) containing
the mandate; `install-codex.sh:72-77` confirmed to copy `hooks/codex/*.sh` to `$CODEX_HOME/hooks/`
and register per-event, so the corrected source is what a real install carries. The Stop hook
remains absent and correctly skipped by that per-event gate — still parked on Codex quota, not
falsely claimed as ported.

## 2026-08-17 — Harden the SessionStart hook so the loop survives adversarial prompts (STORY-harden-sessionstart-hook)

Measured, not assumed. Four cold `claude -p` runs given adversarial framing ("in a big hurry",
"no process or ceremony needed", "speed matters more than polish") **bypassed the loop 4/4** on an
identical fixture: zero `Skill(zeno)` invocations, no branch, no `.zeno/` cards, no tests, no
commits — each edited source directly on `main` in 4-6 tool calls. A supportive-framing run on the
same fixture engaged fully. The loop had become **prompt-dependent**, which is exactly what
`zeno-skill-comply` exists to detect: *"A skill that only gets followed when the prompt already
nudges toward it isn't really governing behavior — the prompt is."*

**Why the hook.** Every bypassing run skipped the skill entirely, so `zeno/SKILL.md` was never
read — a fix there would have targeted a surface the failure never touches. For an agent that
loads no skill, only three surfaces govern: the SessionStart hook, `CLAUDE.md`, and skill
frontmatter. The hook is the one guaranteed present. Its text *described* the loop ("You have the
ZENO loop…") with the instruction buried mid-paragraph among method names — background, not a
mandate.

The injected context now leads with the requirement (invoke `zeno` **before your first Edit or
Write to a source file**) and refuses the waiver by quoting the exact phrasings that defeated it —
"quick", "just hack it in", "no ceremony needed", "speed matters more than polish" — stating they
change the *tier* the work earns, never whether the loop runs. Same technique the skills'
rationalization tables already use: naming the specific excuse beats a generic "don't skip the
process", which is what was there and lost. The typo/rename/one-line-config exemption is preserved
deliberately, so this does not manufacture ceremony for one-liners (the failure PR #36 fixed).

**Verified RED to GREEN with the same prompts on the same fixture:** 4/4 bypass before, **2/2
engage after** — `Skill(zeno)` as tool call #1, `git branch` at #2, feature branch cut, 5 cards
written, commits made, clean tree. Graded from each run's own transcript using the shipped
`extract-trace.py` / `check-order.py`.

**Attribution, recorded so the entry is not misread:** this regression is *not* traceable to this
session's earlier PRs. The invocation-governing surfaces had no relevant changes — the hook and
`zeno`'s description have zero commits, `CLAUDE.md` gained only unrelated lane rows. A second
confound is ours: the test fixture was rebuilt from memory after cleanup and is smaller than the
one the earlier passing run used, so that run may have been the outlier rather than the baseline.
The weakness is real and now fixed; the cause is not established.

## 2026-08-17 — Close the five findings left open at PR #40 (STORY-close-remaining-findings)

The round-2 stocktake deliberately deferred five items because each needed scoping rather than a
one-line correction. All five are now closed, leaving `results.json` with no open Improve verdict.

- **graphify** was the only leaf with neither an anti-pattern table nor a pre-flight checklist,
  both required by `_skill-template.md`. Both authored against what graphify actually gets wrong —
  rebuilding when a current graph exists, inventing an edge instead of using `AMBIGUOUS`, symbols
  instead of raw cohesion numbers, unwarned >5,000-node visualizations, dropping the corpus-check
  warning, treating a god node as "the important file".
- **Production-readiness** triggers collided three ways with no boundary note anywhere. Arbitrated
  on the same doc-vs-execution shape the testing lane already uses: `zeno-production-audit` owns
  the pre-launch *judgement*, `zeno-deployment-patterns` the *mechanics*, `operations-standards`
  the *documents* — a CLAUDE.md lane row plus reciprocal notes in all three, so the split is
  findable from every side (the design-token fix's one-way mistake, not repeated).
- **The documentation dispatcher** carried no feature-planning triggers, so
  `feature-planning-standards` was unreachable unless the dispatcher had already loaded for some
  other reason. Added: feature list, roadmap, release plan, prioritize features, MoSCoW, RICE.
- **The NFR eval** planted unpadded `NFR-01`..`NFR-05` fixtures with no expectation flagging the
  house-grammar violation, so catching them scored nothing while reproducing them passed. The
  malformed IDs are kept deliberately — modelling bad input is the fixture's job — and an
  expectation now rewards flagging them.
- **`postgres/references/operations.md`** still owned a full `pgbouncer.ini` and a
  `postgresql.conf` logging block that its own SKILL.md cedes to `zeno-postgres-patterns`. The
  content was **moved** (destination verified to contain it before anything was removed — PR #40's
  lesson), and the referrer sweep caught `SKILL.md:711` still promising the detail lived in the
  now-empty reference file. That pointer is repointed.

## 2026-08-17 — Finish the remediation the verification stocktake caught half-landed (STORY-stocktake-round2-remediation)

A verification stocktake (4 evaluators, 24 checks) returned 17 RESOLVED / 7 PARTIAL — and found
that the 2026-08-16 remediation had introduced defects of its own. All are now fixed.

**The two that shipped broken:**
- `code-standards/SKILL.md:28,29` still routed Oracle and PostgreSQL work to
  `database-data-modeling/SKILL.md`, deleted in b18c16f — the dispatcher was never opened. Both
  rows now name the leaves directly.
- The postgres "trim to pointers" **deleted** content instead of relocating it: the EXPLAIN signal
  table, the GiST/Hash/SP-GiST index types, the `SET LOCAL app.tenant_id` multi-tenant idiom and
  the postgresql.conf memory/write/planner/autovacuum block existed nowhere, while pointers
  claimed they were owned elsewhere. All four are restored in `zeno-postgres-patterns` — the
  location the pointers name — rather than reverted, since that skill is the correct owner.

**A false proof entry, corrected in place.** `STORY-merge-and-dedupe`'s AC2 Proof claimed a grep
returned 0 hits when it returned 2. The claim was written from intent, not from a run — the exact
failure `zeno-verify`'s Iron Law exists to prevent, inside a card asserting the check passed. A
correction is *appended* to that card; the wrong claim is deliberately left visible, because a
Proof section that quietly repairs itself is worth less than one that shows where verification
failed.

**Stale referrers, swept:** six files still named `github-circleci-standards` as general
deployment owner after it was narrowed to CircleCI-only (`documentation/SKILL.md`, `lifecycle.md`,
`software-test-specification`, `code-standards/SKILL.md`, `_skill-template.md`,
`zeno-self-hosted-deployment`); all now also name `zeno-deployment-patterns`. Design-token
arbitration is reciprocated by `zeno-design-system` and `zeno-frontend-design`, and CLAUDE.md's
lane row gained the fourth claimant (`ui-style`). The Angular split is now stated on the
code-standards side too, matching the Postgres precedent it claimed to mirror.

**Incomplete fixes, completed:** WCAG 2.2 reached `references/examples.md` and `evals/evals.json`
(the eval had been grading against the superseded standard the skill was corrected away from);
the Forms example now compiles (`initial` moved out of the `"use server"` module — such a module
may export only async functions); the refactor lane agrees across skill/agent/command and its
unbacked R-coverage claim is corrected; `epic-template.md` gained the Tier evidence field its
siblings had.

**The stocktake's own tooling, fixed:** `scan.sh` reports `files` and `skills` as separate counts
(149 vs 89 — conflating them inflated the inventory) and records a `sha256` per file;
`quick-diff.sh` compares hashes instead of mtimes. Quick Scan had been structurally impossible:
`install.sh` copies with `cp -R` and no `-p`, so every install rewrote every timestamp to one
value and the diff reported "everything changed" forever. Tested RED/GREEN — exactly 1 file
flagged when 1 differs, 0 when none do. The stale `results.json` is refreshed.

**Still open, recorded not hidden** (5 in the cache): graphify's missing enforcement sections;
the three-way production-readiness trigger collision; the documentation dispatcher's missing
feature-planning triggers; the NFR eval's unpadded fixture IDs; and postgres's `references/
operations.md`, which still holds connection config the SKILL.md cedes away.

**Root cause of the whole class:** each earlier fix corrected the line its verdict cited and
missed the same claim restated elsewhere — in frontmatter, `references/`, `evals/`, callers and
parent dispatchers. Every edit in this pass was followed by a referrer sweep.

# Changelog

Durable, human-facing record of what changed in Zenodotus, one entry per delivered PR. This repo
ships via merged PRs against a rolling `main`, not versioned releases, so entries are dated and
PR-referenced rather than semver'd. Written as part of `zeno-verify`'s Gate 4 finish tail — every
delivery gets an entry here, in addition to whatever `.zeno/` bookkeeping and system-doc
reconciliation that delivery also needed. `.zeno/` cards get archived after merge + deploy; this
file doesn't — it's the durable record that survives archiving.

## 2026-08-16 — zeno-skill-comply ships its trace tooling (STORY-comply-trace-tooling)

The compliance experiment behind PRs #36-#38 ran on two throwaway scratchpad scripts. They found
four real harness defects and were then deleted with the sandboxes — the reusable part of the
method was the tooling, and it wasn't kept. Meanwhile `zeno-skill-comply` *described* trace
capture from `~/.claude/projects/<slug>/*.jsonl` and insisted ordering be checked
"deterministically", while shipping nothing, so every run re-invented both.

Two scripts now ship inside the skill (`skills/zeno-stack/zeno-skill-comply/scripts/`, matching
the `zeno-skill-stocktake` precedent so they install with the skill and work in any repo —
`tools/` is repo-only and never installed, so it was the wrong home):

- **`extract-trace.py`** — resolves a project directory to its Claude Code transcript folder
  (`--list` / `--index` for older runs) and emits a numbered tool-call timeline, or `--json` for
  piping onward.
- **`check-order.py`** — takes `BEFORE:AFTER` rules and reports PASS / FAIL / N/A (the AFTER step
  never happened) / AMBIG (one call matched both sides), exiting non-zero on any FAIL.

Deliberately **not** a grader. The skill's own method says classification is meaning-based via an
LLM, not regex; a shipped regex grader would contradict it and produce confident wrong verdicts.
Code does sequence, the model does meaning — and the skill now says so at both steps.

Dogfooding caught a defect during verification: an early run reported `@12 came after @12`, i.e.
one call matched both sides of a rule (the substring "test" also matches any path under a
directory containing it). Reported as an ordering FAIL, that would have been exactly the silent
wrong verdict this tooling exists to prevent — hence the AMBIG verdict and the warning that
needles match the whole tool input, paths included.

## 2026-08-16 — Advisor tier is read-only for repo state, not just files (STORY-advisor-readonly-bash)

Found live, not by inspection: during the cold verification run for the previous entry, the
`zeno-python-reviewer` subagent it spawned **switched the shared working directory to `main` and
stashed the caller's uncommitted work.** The run detected it and recovered fully (`git checkout` +
`git stash pop`, nothing lost), but the hazard is structural.

`agents/_agent-template.md` defined Advisor tier as "`Read`, `Grep`, `Glob`, optionally `Bash` …
never `Write`/`Edit`", and `REGISTRY.md` called the tier read-only. That guarantee held at the
tool-grant level and leaked entirely through `Bash`: `git checkout`/`switch`/`stash`/`reset`/
`clean`, `rm`/`mv`, shell redirection and package installs were all reachable. Eight of the eleven
Advisors hold `Bash` — database-reviewer, fastapi-reviewer, pr-test-analyzer, python-reviewer,
react-reviewer, security-reviewer, silent-failure-hunter, typescript-reviewer — and the exposure
peaks exactly where the loop mandates them: at Gate 4, against a working branch mid-change.

- **`_agent-template.md`** now states that an Advisor's `Bash` is observation-only and enumerates
  the prohibited classes (branch switching, stash/reset/clean, commits/pushes, file mutation,
  dependency installs), while keeping what the grant exists for — running the suite, linters,
  typecheckers, and read-only inspection (`git diff`/`log`/`status`/`show`). A matching pre-flight
  item makes it checkable for any new Advisor.
- **All eight affected agents** carry the limit in their `Constraints` field. Owner-tier agents
  are deliberately untouched — they are supposed to mutate state within their domain.
- **`REGISTRY.md`** now says what Advisor read-only actually covers (repository and working-tree
  state), naming the incident so the reasoning survives.
- **`zeno-verify`** adds belt-and-braces at the spawn site: if `git status --short` isn't clean
  when invoking the Review specialist, commit first or pass `isolation: "worktree"`.

`Bash` was deliberately *not* removed from these agents — it is what lets them produce evidence,
which `zeno-verify` depends on. The defect was the missing constraint, not the grant.

## 2026-08-16 — Commit authority vs merge authority in Gate 3 (STORY-gate3-commit-authority)

A cold run (C4) completed the entire loop and then left 8 files uncommitted, stating its reason
in its own transcript: *"No commits yet on this branch. I'll stop here rather than commit without
asking, per instructions."* It was the sole outlier of six runs (S1 25 commits, S2 10, S3 3,
C2 6, C3 3, C4 0).

Diagnosed before fixing, per `zeno-debug`: this was not forgetfulness but a documentation
ambiguity. Merge authority is stated four times and emphatically (`zeno/SKILL.md`,
`zeno-verify` — "the human is the sole merge authority, no exceptions"), commit discipline once
and quietly (Gate 3 duty 6) — and **no file said that committing to a working branch sits outside
the human-decision boundary**. A cautious agent therefore generalizes "don't merge without asking"
into "don't write git history without asking". That costs real things: no atomic rollback points,
no per-change record for the loop to run on, and the work dies with the session.

The fix draws the boundary where both rules already live, rather than repeating the commit rule
louder:
- **Gate 3 duty 6** now states that committing to the working branch is the agent's own duty and
  not a decision to ask about — the human's authority begins at *integration* (merging, pushing to
  trunk, opening a PR), never at `git commit` — and that Review should be reached with a clean tree.
- **`zeno-verify`'s finish tail** gains a precondition: run `git status --short` and commit any
  outstanding work *before* presenting merge/PR/keep; a dirty tree is a Gate 3 miss to close, not
  a question for the human, since a menu over uncommitted work asks about something not yet in git.
- **Merge-authority statements scoped, not softened**: they now say "integration authority (merge /
  push to trunk / PR) — not whether you may commit". The prohibitions themselves are untouched;
  `Self-merging to main` remains a violation in both files (verified in the installed copy).
- Enforcement mirrored: two anti-pattern rows in each file, a rationalization row ("I shouldn't
  commit without asking either"), a red flag (presenting the menu while `git status` is dirty), and
  a `zeno-verify` pre-flight item; `zeno-workflow/zeno-tdd` carries the same boundary on its
  per-Task commit line, where the commit actually happens.

## 2026-08-16 — Sizing gate: default down, escalate on evidence (STORY-sizing-gate-default-down)

The sizing ladder was asymmetric. Every sizing signal in the harness pointed *upward* —
`zeno-insight` step 2 ("a long frontier is sizing evidence… may belong at Feature tier"), step 3
("a root frontier spanning several branches → Feature/Epic tier"), and both skills' anti-pattern
rows ("Grinding through 6+ rounds on a Story-tier card"; "A big feature crammed into one pass").
A repo-wide grep for any de-escalation guard returned zero hits.

Found empirically, not by inspection: running the same task (add a `history` subcommand to a
43-line CLI) through five agents, the one given a prompt emphasising *"your full structured
workflow with all its gates"* sized it as a Feature card + 2 Story cards + 4 Task cards, spent
38 of 41 tool calls on planning artifacts, and produced zero lines of implementation. The other
four sized the identical task as a single ad hoc Story and shipped it. Tier inflation is harder
to catch than a skipped gate, because the cards look thorough — it just spends the budget the
implementation needed.

The fix is placement, not new machinery — the same shape as the branch-check fix (Obs 34/38/41):
- `zeno/SKILL.md`'s ladder now opens with a default and a burden of proof: start at the smallest
  tier that fits and climb only on named evidence (the work's shape — independently verifiable
  Stories, several Execution passes — never how formal the request sounds); a Feature card
  requires naming the two-plus Stories it decomposes into, an Epic the Features; the chosen tier
  and its one-line evidence get recorded on the card. States plainly that ceremony depth follows
  the work, not the prompt's tone, and that over-tiering is not a safe error.
- Enforcement mirrored: two anti-pattern rows (Feature card for Story-sized work; raising tier on
  prompt tone), a rationalization row ("more planning can't hurt" → it spends the same budget),
  a red flag (writing a Feature card without being able to name its Stories), and the master
  pre-flight checklist item.
- `zeno-insight` step 3 gains the symmetric downward signal (a frontier closing in 1–2 rounds
  over a 1–2 file blast radius is evidence of Story tier) plus its own anti-pattern row. Existing
  upward escalation left intact.
- `story-template.md` / `feature-template.md` gain a **Tier evidence** field, so the decision is
  recorded structurally rather than from memory.

Verified by re-running the exact prompt that caused the inflation, cold, against the hardened
harness: the agent produced one Story + 3 Tasks (no Feature card), recorded its reasoning
verbatim — *"a Feature/Story split would out-tier the actual work"* — and delivered a working
feature with 10 passing tests, independently re-exercised end-to-end here (10-entry cap, newest
first, failed conversions recorded nothing).

While sweeping for contradictions, `USAGE.md`'s gate table was found still describing the
pre-PR#32 structure (all five stages inside Execution); corrected in the same pass to match the
current model — DDD in Gate 1, FDD/ATDD/BDD in Gate 2, pure TDD in Gate 3.

## 2026-08-16 — Act on the full-project review (FEAT-full-review-remediation)

An 8-evaluator stocktake (all 90 skills, 23 commands, 24 agents, plus a repo-level audit;
verdicts cached in `zeno-skill-stocktake`'s `results.json`) returned 104/137 Keep and a
remediation backlog, delivered as six Stories on one branch:

- **Decommission tail closed** — `zeno-skill-stocktake` lost its dead usage plumbing (scan.sh no
  longer reads the never-written `observations.jsonl`; the always-zero 7d/30d columns are gone),
  and `zeno-skill-comply` gained a real execution substrate (fresh-subagent runs + tool-call
  traces parsed from `~/.claude/projects/*/​*.jsonl` transcripts) plus a stated boundary with
  `/skill-evals`.
- **Nine factual errors fixed** — zeno-build-resolver's React handoff now points at the real
  owner (`zeno-react-build-resolver` via `/react-build`); zeno-react-patterns' Forms example now
  compiles (server action moved to its own `"use server"` module); zeno-react-performance
  updated for the stable React Compiler 1.0; `/checkpoint`'s dead `/verify` reference and
  `/model-route`'s citation of nonexistent scripts removed; `/update-docs`'
  create-vs-never-create contradiction resolved; oracle-plsql §4.4 rescoped so it no longer
  mandates the row-by-row pattern §4.2 forbids; zeno-deep-research gained a WebSearch/WebFetch
  fallback tier (its firecrawl/exa prerequisite is unconfigured in this environment); the test
  spec skill moved to WCAG 2.2.
- **Provenance & invariants** — graphify's third-party sponsor plug removed and its wrapped
  external PyPI engine `graphifyy` explicitly attributed (here and in the skill; CLAUDE.md's
  no-unattributed-content claim now carries the sanctioned-exception clause);
  `OBSIDIAN_VAULT_PATH` set in `~/.claude/settings.json` (invariant 3); zeno-security-scan's CI
  example now instructs commit-SHA pinning.
- **Merges & dedupe** — `zeno-model-route` reduced to a thin router stub (the heuristic lives
  once in `/model-route`; the stub remains the Codex fold home — discovered mid-execution that
  the "twin" skills are deliberate Codex fold targets from STORY-codex-orphan-skills, so
  deletion would break `build_codex.py`); the `database-data-modeling` dispatcher hop deleted
  (its two rows were already named verbatim in the parent); the five agent↔skill twins
  cross-referenced both ways with an arbitration section in `agents/REGISTRY.md` (skill inline,
  agent spawned); the session lane's contract ownership pinned on `zeno-sessions`; the React
  command trio thinned from ~19KB to ~9.5KB of delegation shape; code-standards/postgres and
  zeno-postgres-patterns now both honor their declared split; python's §§2–4 raw-PEP 8
  restatement compressed to a Ruff-config pointer (697→548 lines).
- **Arbitration pass** — CLAUDE.md gained lane rows for CI/CD (CircleCI house standard vs
  GitHub Actions/strategy in zeno-deployment-patterns), design tokens (three-way split), the
  Angular style/framework split, and zeno-harness-optimizer's place in the maintenance lane;
  reciprocal notes in four skills; a which-wins semgrep paragraph in zeno-security-review; the
  E2E lane aligned on Playwright; `TR-NNN` added to the house ID grammar with a House-IDs
  section in the TRD skill; `/update-codemaps` output pinned to `docs/CODEMAPS/`;
  `_skill-template` now cites `cross-cutting-principles.md` by real path; six agents gained
  trigger clauses; zeno-tdd-guide +Glob, zeno-harness-optimizer +Write; the refactor-cleanup
  lane gained per-stack analyzers beyond JS/TS.
- **Repo hygiene** — `install.sh` now compares name *sets* (not counts) across all four dirs and
  names lingering orphans, excludes `hooks/codex/` from the Claude target (installed hooks count
  is 2 again, matching the inventory), and survives a missing/corrupt hook fragment with a
  message instead of a traceback; README corrected (23 commands, real hook self-wiring
  description, current Codex SessionStart status); the cost tracker prices date-suffixed model
  ids by longest prefix; `.ruff_cache/` ignored; stale installed-side artifacts removed and both
  installers re-verified clean (`install.sh` drift check green; `install-codex.sh --dry-run`:
  149 files, 45/45 folds).

## 2026-08-14 — Rename `.project/core.md` to `.zeno/project.md`

User-directed rename: the backlog folder now carries the tool's own name (`.zeno/`) rather than a
generic `.project/` label, and its index file is `project.md` rather than the ambiguous `core.md`.
Renamed across every skill, agent, command, and hook file, the top-level docs (`CLAUDE.md`,
`README.md`, `AGENTS.md`, `USAGE.md`), and this repo's own live folder — including `git mv`ing the
folder and the index file to preserve history, and renaming `references/core-template.md` to
`references/project-template.md`. Added a second migration recipe to `references/migration.md`
(Recipe 2 — a mechanical `git mv`, not a content migration, since the five-card-type model itself
is unchanged) alongside the existing legacy-`THREAD.md` recipe, and wired detection for the
pre-rename layout into `zeno/SKILL.md`'s Gate 2 step 5 and the `/zeno` command's `start` row so a
repo still on the old layout migrates automatically rather than silently diverging.

While sweeping for stale references, found both PlantUML architecture diagrams
(`docs/diagrams/zeno-architecture.puml`, `zeno-loop-activity.puml`) still depicted the
pre-restructure Gate 3 — DDD/FDD/ATDD/BDD/TDD all grouped under one "Gate 3 — Execution" — meaning
the earlier gate-restructure delivery shipped without updating them. Fixed in the same pass:
both diagrams now show DDD framed in Gate 1, FDD/ATDD/BDD/Task-breakdown in Gate 2, and TDD alone
in Gate 3, matching `zeno/SKILL.md`'s actual current gate table; regenerated both `.svg` outputs
via the `plantuml` CLI rather than hand-editing the rendered XML. Both `SessionStart` hooks
(`hooks/zeno-session-start.sh`, `hooks/codex/zeno-session-start.sh`) rewritten and freshly
functionally re-tested against the real renamed file. Routed through the `zeno` loop as ad hoc
`STORY-rename-project-to-zeno`.

## 2026-08-14 — Gate 4's documentation check now runs at the closing item's own scope

User-directed fix, following the previous restructuring: a Story's Gate-2-planned, Gate-3-executed
documentation Task covers that Story's own diff, but Gate 4's own documentation check was written
as if confirming that Task happened (or that the diff "looked internal") satisfied it — no check
ever asked, once every Story under a closing Feature was done, whether the *system's* documentation
(README, inventory tables, architecture notes) still held for the delivery as a whole. Split the
check into two explicit questions in `zeno-verify/SKILL.md`: (1) did each Story's own documentation
Task actually happen — verified via its Proof entry, not assumed; (2) does the system's
documentation still describe the system at the closing item's own scope (Story/Feature/Epic) —
doc-worthy-gated, same as before, but now asked about the delivery as a whole rather than
implicitly inherited from its Stories. Mirrored into `zeno/SKILL.md`'s Gate 4 prose, anti-pattern
table, and pre-flight checklist. Caught and self-corrected a real process miss mid-delivery:
started editing directly on `main` before branching (Gate 2 step 1) — fixed before committing, no
main-branch history affected.

Extended same-session with a further user-directed escalation: for a closing Feature or Epic (not
every ad hoc Story), the documentation check now also asks whether a full documentation set exists
for the touched component — Architecture & Design, Technical & API Specs, User & Admin Guides —
reusing existing `documentation/` skills for the first two and naming the real gap for the third
(no User Guide leaf exists yet). If no full set exists, the check flags it (Decisions log +
`core.md` Open questions) and recommends an Epic; it never backfills the gap inline and never opens
the Epic without the human's confirmation. Considered and declined adding a dedicated Gate 5 for
this — it's a conditional flag a Feature/Epic close can trigger, not something every non-trivial
task runs through the way Gates 1-4 always do, and any resulting Epic still executes through the
ordinary four gates. Routed through the `zeno` loop as ad hoc `STORY-gate4-delivery-scope-doc-check`.

## 2026-08-14 — Restructure zeno's gates: Epics→Features (Gate 1), Stories→Tasks (Gate 2), pure implementation loop (Gate 3)

User-directed restructuring of the zeno loop's DDD→FDD→ATDD→BDD→TDD pipeline, moving from an
all-in-Gate-3, just-in-time model to full up-front planning matching standard Epic/Feature/Story/
Task ownership (Epic = why, Feature = what capability, Story = what the user needs, Task = how we
implement it — the user's own "Golden Rule": Product owns Epics/Features/Stories in business
language, Engineering owns Tasks' technical design). Gate 1 (Scope) now enumerates an Epic's
Features and runs DDD to frame a Feature's domain before it closes. Gate 2 (Route) now runs FDD to
write a Feature's full Story list, then ATDD + BDD + a technical Task breakdown for **every** Story
on it — not just the next one — before Gate 3 ever opens; every Story's Task list always ends with
a dedicated documentation Task. Gate 3 (Execution) is now a pure implementation loop: pull the next
Task off an already-fully-planned Story and run TDD, nothing else. Along the way, fixed a
pre-existing bug found during the restructuring: `zeno-tdd` claimed the Story's Task list was
"written by zeno-bdd's Scenarios," but `zeno-bdd` never actually wrote one — it now has a correct,
explicit owner (Gate 2 itself). Updated the core spine (`zeno/SKILL.md`, `zeno-workflow/SKILL.md`,
all five `zeno-workflow/zeno-*/SKILL.md` stage files), the five `.project/` card templates,
`CLAUDE.md`, and `README.md` for internal consistency; dry-run walked end-to-end against a
throwaway example with no ambiguity found. Some informal "Execution pipeline" shorthand remains as
cross-reference pointers in the four pipeline-stage-guide agent files and `zeno-planner.md` —
logged as accepted residual drift, not a defect (see the Story card). Routed through the `zeno`
loop as ad hoc `STORY-gate-restructure-epic-feature-story-task`.

## 2026-08-14 — Decommission task-observer

Removed `skills/task-observer/` in full (`SKILL.md` + its two `references/` files) — the user
judged its mandatory "invoke at the start of every task-oriented session" activation wasn't
earning its token cost. Removed every mechanism that mandated it: `CLAUDE.md`'s and `AGENTS.md`'s
"task-observer activation" sections (the standing instruction to invoke it every session and check
`~/.claude/skill-observations/log.md`/`~/.codex/skill-observations/log.md` for OPEN observations),
`zeno/SKILL.md`'s "Relationship to task-observer" section and pre-flight checklist line (its own
habit of logging to that same file), `zeno-insight`'s pre-flight line confirming it was active,
and its listing in `CLAUDE.md`'s/`README.md`'s skill inventories. Left `zeno-skill-stocktake`'s and
`zeno-config-gc`'s illustrative/relationship mentions of it corrected rather than dangling. Per the
user's explicit choice, this is a full removal of the observation-logging mechanism, not just the
skill — nothing in the harness writes to or reads `skill-observations/log.md` going forward; the
log file itself is left on disk, unreferenced, not deleted. Historical `CHANGELOG.md` entries and
`.project/` Decisions/Proof entries that mention task-observer are left untouched, per this
document's own append-only convention — they describe what was true when written. No config
snapshot was taken (unlike the 2026-07-30 GSD/superpowers/ECC decommission): everything removed
here was git-tracked repo content, so `git log`/`git show` on the pre-removal commit is already a
complete rollback path.

## 2026-08-14 — Confirm and port Codex's SessionStart hook (STORY-codex-hooks-port)

Unblocked and confirmed `SessionStart`'s real Codex CLI hook I/O contract live, using Codex's own
`--dangerously-bypass-hook-trust` flag against an isolated sandbox (never the user's real
`~/.codex`) to get past the trust-approval gate PR #29 identified. Its stdin payload
(`session_id`/`transcript_path`/`cwd`/`hook_event_name`/`model`/`permission_mode`/`source`) and
stdout envelope (`hookSpecificOutput.additionalContext`) turned out to be identical to Claude
Code's — confirmed by round-tripping the exact, unmodified Claude Code `zeno-session-start.sh`
through a real `codex exec` run and finding its injected context in the resulting transcript.
Ported `hooks/codex/zeno-session-start.sh` as a byte-identical copy and changed
`install-codex.sh`'s hook-registration step to register each event independently based on its own
script's existence, since this Story now lands its two hooks on different timelines. Also
confirmed, as a useful negative result, that `Stop` does not fire on an errored/quota-limited turn
— its contract stays genuinely blocked on Codex usage quota (resets 2026-09-12), not guessed. See
`.project/docs/tasks/TASK-verify-and-port-session-start-hook.md` and
`.project/docs/stories/STORY-codex-hooks-port.md` for full detail.

## 2026-08-14 — Fix install-codex.sh's hook registration schema (STORY-codex-hooks-port)

While attempting to unblock parked `STORY-codex-hooks-port` against a live Codex CLI (0.147.0)
install, confirmed `install-codex.sh`'s hook self-wiring step (shipped in PR #23) targeted the
wrong file and schema entirely: it wrote a `[[hooks]]` array-of-tables to `config.toml`, but real
Codex CLI reads hook registrations from `$CODEX_HOME/hooks.json` (Claude-`settings.json`-shaped
JSON); `config.toml` only holds an unrelated trust-hash cache. Fixed to write `hooks.json` via the
same idempotent JSON-merge pattern `install.sh` already uses, verified end-to-end in an isolated
scratch sandbox (fresh-install and idempotent-rerun both confirmed correct). `AGENTS.md` corrected
to match. The step still no-ops until `hooks/codex/*.sh` exist — the SessionStart/Stop payload
contract itself remains unverified, blocked this session by a hook trust-approval gate and an
exhausted Codex usage quota (resets 2026-09-12); the Story stays parked per its own no-guessing
rule. See `.project/docs/tasks/TASK-fix-hook-registration-schema.md` and
`.project/docs/stories/STORY-codex-hooks-port.md` for full detail.

## 2026-08-13 — Cross-gate consistency pass: stale Gate 4 summary, checklist wording, branch-surfacing hook

After individually hardening all four zeno gates this session (PRs #24-27), a cross-gate
consistency pass found three self-introduced gaps and closed them. `zeno/SKILL.md`'s Gate 4
summary paragraph now names the verify-before-archive rule added in PR #27 — previously the
summary enumerated nearly everything else `zeno-verify` does but omitted its most significant
recent fix. The master pre-flight checklist's archiving line was tightened to match
`zeno-verify`'s own stricter "verified with a real command" wording, plus a matching anti-pattern
row. `hooks/zeno-session-start.sh` now runs `git branch --show-current` and surfaces it alongside
the existing Goal/Next-step resume hint — completing the second half of Observation 41's suggested
improvement (the SKILL.md structural fix landed in PR #25; the hook enhancement was deferred until
now). The hook change was verified by actually executing the script and parsing its real JSON
output, both from source and the post-`install.sh` installed copy, not just reading the diff.
Scoped via a conversational review, routed as ad hoc `STORY-cross-gate-consistency`.

## 2026-08-13 — Gate 4 (Review) hardening: verify-before-archive, content-only carve-out

Two fixes in `skills/zeno-verify/SKILL.md`. First, the Iron Law now explicitly covers bookkeeping
claims — marking an observation-log entry ACTIONED or flipping a card's Status — not just
user-facing "done" statements, and Finish tail step 6 now requires verifying merge state with a
real command (`gh pr view`/`git log`) before archiving, rather than trusting the human's word or
memory of an earlier action. This closes a real, evidenced gap from earlier this same session: PR
#12 sat open, unmerged, for two days while Observation 34's Status line already claimed "ACTIONED"
— the direct root cause of Observations 38 and 41 later finding the same branch-check failure
recurring, because the fix everyone believed had landed never actually shipped. That incident is
now logged as its own entry, Observation 42, in `~/.claude/skill-observations/log.md`. Second, the
"Full-repo phase check" section gained an explicit carve-out: content-only deliverables (docs,
skill/config files, no language toolchain) substitute goal-backward grep/read verification for the
build/type/lint/test steps, mirroring Gate 3's existing non-code language in `zeno/SKILL.md`. Both
fixes carry matching anti-pattern/rationalization/red-flag/pre-flight entries. Scoped via a
conversational review and routed through the `zeno` loop as ad hoc
`STORY-gate4-review-improvements`.

## 2026-08-13 — Gate 3 (Execution/TDD) hardening: schema-drift fixture check, stale-claim guard, numbered duties

Two additive sections in `skills/zeno-workflow/zeno-tdd/SKILL.md`, closing OPEN Observations 39
and 40 (`~/.claude/skill-observations/log.md`). "Schema-drift fixtures (migrations)" requires a
`grep -rl` check for a repo-wide schema-assertion fixture (`ALL_TABLES_AND_COLUMNS`-shaped) before
considering a migration's GREEN commit done — a real session had two migrations in a row silently
skip updating such a fixture, caught only by luck on a third. "Don't trust a prior Story's clean
claim" requires a fresh lint/test run near a new Story's own start when resuming work on an
already-active repo, rather than inheriting a sibling Story's independently-verified "clean" claim
— a real session found a pre-existing lint violation on a fresh run that an immediately-prior,
re-verified closure claim had missed. Both sections carry matching anti-pattern/rationalization/
red-flag/pre-flight entries. Separately, `zeno/SKILL.md`'s Gate 3 section had its post-table prose
(clean-code gate, `zeno-stack` leaf, `zeno-debug` routing, WIP limit) restructured into 6 numbered
duties, matching Gate 1 and the same-day Gate 2 hardening's shape. Scoped via a conversational
review and routed through the `zeno` loop as ad hoc `STORY-gate3-execution-improvements`.

## 2026-08-13 — Gate 2 (Route) hardening: structural branch check, always-reconcile, skill-currency check

Restructured Gate 2 in `skills/zeno/SKILL.md` from a prose paragraph into 5 numbered, ordered
steps, closing a gap that had recurred three separate times in this repo's own history
(`~/.claude/skill-observations/log.md` Observations 34/38/41): non-trivial work starting directly
on `main` because "branch first" lived only as a sentence in Gate 3's prose and a Gate-4
retrospective checklist line, never as something checked before the first edit. Step 1 is now a
blocking `git branch --show-current` + `git status --short` check, run before any Scope/card
content or file edit. Step 2 extends the existing "reconcile against reality" instruction to fire
every time Gate 2 is touched, not only at session start (Observation 37's twin gap: a stale
`core.md` read mid-session, not just on cold resume). Step 3 adds a new check for long-running
sessions to notice the installed `zeno` skill itself changed since it was loaded, deferring the
resolution to the human (also closing Observation 37). Gate 3's old duplicate "branch first"
sentence now cross-references Gate 2 step 1 instead of restating it, and the old duplicate Gate-4
pre-flight checklist line was removed — the rule now lives in exactly one place. Scoped via a
conversational review dialogue (mirroring the same-day Gate 1 hardening) and routed through the
`zeno` loop as ad hoc `STORY-gate2-route-improvements`.

## 2026-08-13 — Gate 1 (zeno-insight) hardening: task-observer check, frontier-round guardrail, worked example

Four targeted edits to `skills/zeno-insight/SKILL.md`, closing one already-open self-review gap
plus three found on a fresh read of the skill. (1) The pre-flight checklist gains a first item
confirming `task-observer` is active for the session — a second, harness-internal enforcement
point for CLAUDE.md's structural trigger, closing `~/.claude/skill-observations/log.md`'s
Observation 36 (a prior session found the trigger can silently fail to fire with nothing catching
it). (2) Step 2 ("ask the current frontier") now names a round-count guardrail: a frontier still
running past roughly 4-5 rounds is itself sizing evidence to revisit step 3's card tier, with
matching rows added to the anti-pattern and rationalization tables. (3) Step 4's opening sentence
now cross-references step 2's distinct `agents/REGISTRY.md` use inline, instead of leaving the
distinction to surface only via the rationalization table. (4) An illustrative worked example of a
`❓/➡️` frontier round was added after step 2's prose. Scoped via Claude Code's plan mode (approved
plan at `~/.claude/plans/review-gate-1-what-witty-pillow.md`) and routed through the `zeno` loop as
ad hoc `STORY-gate1-insight-improvements`.

## 2026-08-13 — Codex CLI target (Phase 1 of a two-phase multi-harness port)

Added a second, generated install target alongside `install.sh`/`~/.claude`: `install-codex.sh`
installs Zenodotus into `~/.codex` for OpenAI's Codex CLI. Since Codex has no per-file,
tool-scoped subagent primitive and deprecated its custom-prompt mechanism in favor of Skills,
`agents/` and `commands/` are folded into their domain-owning skill as titled sections (mapping:
`tools/codex/fold-map.toml`; generator: `tools/codex/build_codex.py`, stdlib-only via `tomllib`)
rather than mirrored 1:1 — the fold only exists in the generated `~/.codex` output, never touching
the shared `skills/` source or the `~/.claude` target. 9 new `zeno-stack` leaves
(`zeno-build-resolver`, `zeno-comment-analysis`, `zeno-harness-optimizer`,
`zeno-performance-profiling`, `zeno-planning`, `zeno-refactor-cleanup`, `zeno-cost-report`,
`zeno-model-route`, `zeno-sessions`) were authored to give 9 previously agent/command-only domains
a real fold target, dual-registered in `zeno-stack/SKILL.md`. `commands/zeno.md`'s dispatch table
was additionally relocated directly into `skills/zeno/SKILL.md`'s own new "Invocation" section,
benefiting both install targets identically. `AGENTS.md` — previously an untracked, uncommitted,
mechanically find-replaced draft of `CLAUDE.md` with a path-casing bug — was discarded and
rewritten from scratch as a real Codex-native arbitration document. `hooks/codex/*.sh` (the
Codex-side `SessionStart`/`Stop` hook scripts) are intentionally not included in this delivery:
Codex's actual hook I/O contract needs live verification this session had no way to perform, and
the plan this work followed was explicit that it must not be guessed and shipped —
`install-codex.sh`'s hook-registration step is built and wired but correctly no-ops until those
scripts exist (tracked as the parked `STORY-codex-hooks-port`). A Gemini CLI target (Phase 2) is
sketched in `.project/docs/features/FEAT-codex-port.md` but not yet built.

## 2026-08-13 — Card lifecycle: archive on merge, don't delete

`zeno-verify`'s finish tail used to delete a closed card's file(s) once merged and deployed,
relying on git log / the merged PR / `CHANGELOG.md` as the only durable record — none of which
carry a card's own Proof/Decisions detail in-repo, in-place. Flipped to archive instead: `git mv`
into `.project/docs/archive/{stories,tasks,features}/` (Epics archive only when the whole Epic
closes), `core.md`'s path references rewritten to match and verified against the filesystem
(zero broken links), Kanban/checklist rows staying (updated to the archive path, not removed).
Mirrored in `zeno/SKILL.md`'s anti-ceremony framing (`.project/docs/archive/` is now the
permanent in-repo record, not a thing to avoid) and its own pre-flight checklist. Added a
periodic (not per-close) housekeeping note for when `core.md` itself grows unwieldy — oldest
entries move to `docs/archive/core-history.md` via `zeno-config-gc` or a manual ask. User had
already reversed the same behavior manually in a different repo's `.project/` and asked for it
codified here. This `CHANGELOG.md` entry's own convention (one entry per delivery, unconditional)
is unchanged — additive to the new archive behavior, not replaced by it, per explicit scope.

## 2026-08-12 — Retired ATTRIBUTION.md

`ATTRIBUTION.md` mixed two different things: genuine licensing/provenance facts, and general
engineering history that only lived there because this file didn't exist yet when it was written.
Split it: the licensing facts folded into `LICENSE` (now self-contained, no outbound pointer to a
file that no longer exists); the engineering history backfilled below as 5 dated,
commit-verified entries (2026-07-30 through 2026-08-09) covering Phases 1-5, the specialist agent
architecture, and the pipeline-stage guide agents. Fixed every cross-reference across `CLAUDE.md`,
`README.md`, `USAGE.md`, `agents/REGISTRY.md`, `agents/_agent-template.md`, and `skills/
_skill-template.md` (9 files, ~24 reference lines total). Also fixed two stale claims found along
the way, independent of this delivery's own scope: `CLAUDE.md` implied an open "list of
not-yet-rewritten bundled files" that was actually already resolved; `skills/_skill-template.md`
claimed vendored non-`SKILL.md` files "remain," when that too was resolved 2026-08-09.

## 2026-08-12 — Config-maintenance table: add `/cost-report`, `/model-route`

Trivial edit, direct to `main` (no Story card, no PR — one-line config per the sizing ladder).
Added `/cost-report` and `/model-route` to CLAUDE.md's Config-maintenance table, closing the last
judgment-call item surfaced by PR #15's context-budget audit.

## 2026-08-12 — PR #20 — Gate 4: mandatory changelog + always-run doc check

This file. Gate 4 (`zeno-verify`, mirrored in `zeno/SKILL.md`) now requires an unconditional
`CHANGELOG.md` entry on every card close — durable and human-facing, unlike `.project/`'s Proof
rollup, which gets pruned after merge + deploy. The prior "documentation check (doc-worthy changes
only)" framing was reworded so the *check* always runs; only the resulting system-doc edit stays
gated on `documenting-code`'s existing doc-worthy trigger table, avoiding manufactured doc churn on
purely internal changes. Backfilled this file's own history through PR #19 from `core.md`'s Proof
rollup. Dogfooded clean against an independent subagent across a doc-worthy and a purely-internal
scenario. See `.project/docs/stories/STORY-gate4-delivery-docs.md` (pruned after this entry) for
the full Scope/Proof record. Commit `43a974b`.

## 2026-08-12 — PR #19 — Gate 1: frontier-round questioning

`zeno-insight`'s Gate 1 replaces strict one-question-at-a-time clarifying questions with a
frontier/design-tree round model (batch every currently-unblocked question per round, `❓`/`➡️`
format with a recommended default), adapted from `grill-me`/`grilling` (mattpocock/skills, MIT)
and extended with capabilities the source can't have: card-persisted per-round Decisions-log
writes, registry-first + impact-analysis-aware self-service research, and frontier-width as a
card-tier sizing signal. Scope-exit check tightened from "every raised decision resolved" to "the
frontier is empty." See `docs/proposals/grill-me-borrowing.md` and
`.project/docs/stories/STORY-gate1-frontier-questioning.md` for the full research/Scope/Proof
record. Commit `39e7fd1`.

## 2026-08-11 — PR #18 — Angular/React custom-element guidance correction

Corrected the bidirectional Angular↔React custom-element guidance added in PR #17 against
follow-up research: r2wc, React 19 consumption semantics, 2 named GitHub issues, single-bundle
build tooling. Commit `fde0e63`.

## 2026-08-11 — PR #17 — Angular/React whole-app coexistence guidance

Added Angular↔React whole-app coexistence guidance to `code-standards` — single-spa, Module/Native
Federation, Angular Elements→React, iframe — grounded via 3 live doc-verification research agents.
Commit `7103259`.

## 2026-08-11 — PR #16 — Cost/context tooling aligned with cost-reduction research

Aligned `zeno-context-budget`, `model-route.md`, and `CLAUDE.md` with the LLM cost-reduction
literature survey. Commit `8f233c1`.

## 2026-08-11 — PR #15 — Cost-tracker hook fix, pricing refresh, real context-budget audit

Fixed the dead cost-tracker Stop hook at its settings-scope root cause, ran a real
`/context-budget` audit, refreshed effective-dated Sonnet 5 pricing, fixed a stale commands-count
reference. Commit `cb5d30e`.

## 2026-08-11 — PR #14 — ATDD/BDD counter-example requirement

Tightened ATDD/BDD so every Example-Mapping Rule needs a counter-example, not just confirming
Examples, and BDD translates each into its own rejection/failure-path scenario — ceremony alone
isn't a warranty of good design, so the gates now force a genuine adversarial act. Commit
`c0002b9`.

## 2026-08-11 — PR #13 — Card-type drift fix, mandatory THREAD.md migration

Fixed four-vs-five-card-type drift across `commands/zeno.md`, `commands/pr.md`, and
`hooks/zeno-session-start.sh`; made `/zeno start`'s legacy-`THREAD.md` migration mandatory instead
of a passive pointer. Commit `3b9ca44`.

## 2026-08-11 — PR #10 — Task/SubTask backlog levels

Added Task/SubTask as new `.project/` card levels beneath Story, with their own card files;
collapsed Status+Stage to one field across all five levels; reattached TDD proof from Story to the
Task/SubTask leaf. Commit `3317489`.

## 2026-08-09 — Vendored-content removal completed; pipeline-stage guide agents added

Backfilled from `ATTRIBUTION.md` (retired this session — see the entry below). Added the 4
pipeline-stage guide agents (`zeno-ddd-guide`/`zeno-fdd-guide`/`zeno-atdd-guide`/`zeno-bdd-guide`),
mirroring `zeno-tdd-guide`'s existing pattern, original from creation (commit `20e79ea`). Resolved
the one non-ECC provenance item: `zeno-stack/zeno-frontend-design` was identified as vendored from
an earlier version of Anthropic's official `frontend-design` plugin (Apache License 2.0, found by
a byte-identical `LICENSE.txt` match); a third rewrite pass cleared the remaining verbatim
passages and the license file was removed (commit `eef18dc`). Deleted the last bundled vendored
scripts (three `zeno-stack` leaves) and dropped `LICENSE-ECC` — no vendored or unattributed
third-party content remained anywhere in the repo from this point on (commit `4d44e79`). Rewrote
`zeno-security-review`'s cloud-infrastructure reference from scratch and deepened it (commit
`eaa0090`). Cut ~2,000 tokens/session off `CLAUDE.md` and 4 heavy skills, and deleted an orphaned
35-file/
~3,800-line vendored `zeno-angular-developer/references/` bundle that had never been cited (commit
`5662c52`).

## 2026-08-08 — Phases 1-3: vendored skills, agents, and commands removed and rewritten

Backfilled from `ATTRIBUTION.md`. The 42 domain skills, 20 agents, and 21 commands vendored from
**everything-claude-code** (MIT © 2026 Affaan Mustafa) were removed and rewritten from scratch as
original `zeno-stack`/`zeno-<name>` content — same technical ground, zeno house style, no
MIT-licensed text remaining (commits `621bc83`, `819be3f`, `7b88534`). Two real bugs fixed along
the way, not just relabeled: the vendored `security-review` recommended an in-process rate
limiter (wrong for production — resets on deploy, doesn't coordinate across replicas); the
Redis-backed implementation from vendored `redis-patterns` became the single source of truth
instead. Vendored `skill-scout` reimplemented logic that duplicated `find-skills` despite its own
text saying it should delegate — now actually delegates. Six vendored commands had real functional
problems beyond stale references (phantom hook/script dependencies, a fictional session-file
format, an ECC-marketplace-plugin assumption that doesn't hold for a git-cloned single-source
repo) — each rewritten to work natively; `project-init.md` was discarded outright (its
multi-harness installer premise had no working capability to preserve).

## 2026-08-08 — Specialist agent architecture formalized

Backfilled from `ATTRIBUTION.md`. Formalized the 20 rewritten agents into a specialist
architecture: `agents/_agent-template.md` (the contract shape) and `agents/REGISTRY.md` (the
routing table). Found and resolved 8 content-overlap clusters by reading all 20 files in full —
security checks duplicated across 4 reviewers, FastAPI checks duplicated across 2, "tests that
lie" duplicated between build-time and review-time agents (kept both, cross-referenced), swallowed
exceptions, DB/React performance, and accessibility duplicated across pairs (resolved by boundary
edit or bidirectional cross-reference, not merge). No `Authority` tier introduced — the human
keeps the sole final merge call. Commit `4621e8e`.

## 2026-08-08 — Phase 4 quality review of zeno-core; Phase 5 de-vendors task-observer

Backfilled from `ATTRIBUTION.md`. Two full-file audits of the 9 zeno-core skills (the spine, 3
gate skills, the 5-stage pipeline) found 8 real defects, not just polish: a methodology gap
between ATDD's rule/checklist criterion format and BDD's strict one-scenario-per-criterion rule
(fixed by letting a rule expand into multiple scenarios); a broken template path; a Feature-level
`Stage`-field gap; a checklist/template field-count mismatch in `zeno-ddd`; 3 non-canonical
Pre-flight checklist headings; uneven specialist-registry wiring (Rationalizations/Red-flags
tables missed); 2 internal Iron-Law/checklist inconsistencies; a Scope-gate ordering drift between
the spine's summary and the actual gate skill (commit `684b442`). A separate full-project
consistency audit fixed ~25 more findings the same day (commit `87f285b`). Separately, `skills/
task-observer/SKILL.md` was found to be third-party content — **CC BY 4.0**, created by Eoghan
Henn (rebelytics.com), sourced from `github.com/rebelytics/one-skill-to-rule-them-all` — gone
unrecorded in this repo's provenance docs and misclassified as hand-authored. Rewritten as
original prose preserving the exact observation-log mechanism `zeno`/`zeno-config-gc` depend on;
the author-attribution block, Licensing section, and Cowork/web-chat-specific material (not
applicable to a Claude-Code-only repo) were cut rather than carried forward. Commit `c335143`.

## 2026-07-30 — Zenodotus becomes the single-source harness

Backfilled from `ATTRIBUTION.md`. Decommissioned the **GSD** (get-shit-done) lifecycle suite in
full — 71 commands, 34 agents, 26 hooks, and the `gsd-core/` engine removed; GSD was never
vendored, so nothing of it remained to rewrite. Uninstalled **superpowers**
(`github.com/obra/superpowers`, MIT © 2025 Jesse Vincent) — its discipline (brainstorm-before-code,
test-first, systematic-debugging, verification-before-completion) inspired the `zeno` loop's
method skills conceptually, but no superpowers text was reused, and it was likewise never
vendored. The pre-decommission state of everything removed, plus the pre-rewrite `CLAUDE.md`, is
archived in a private snapshot that is not published (see
`CLAUDE.md`'s own Config-maintenance invariants for the current pointer). Commit `b9122f0`.
## 2026-10-03 — Make skill stocktake target-aware (STORY-codex-stocktake-target)

`zeno-skill-stocktake` now audits either the Claude tree or the generated Codex tree. Claude
remains the default; Codex is selected with `--target codex` or `SKILL_STOCKTAKE_TARGET=codex`,
using `$CODEX_HOME/skills` and preserving the source-of-truth warning for generated output.
