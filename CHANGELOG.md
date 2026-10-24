# Changelog

Recent changes, newest delivery first within each day. Older history (August to early September 2026,
including the de-vendoring passes) is in [docs/changelog-archive.md](docs/changelog-archive.md). Commit
hashes quoted in either file refer to the author's earlier private history, which is not part of this
repository.

## 2026-10-24 — GitHub repository setup for going public

- Added the community files: `CODE_OF_CONDUCT.md`, issue forms (bug report, idea) with a security contact link,
  a pull request template, `CODEOWNERS`, Dependabot for the pinned GitHub Actions, and a CodeQL workflow
  (Python and Actions; skipped while the repository is private).
- New `tools/github-settings.sh` applies the repository settings with `gh` and is safe to re-run: merge options,
  read-only workflow token, only GitHub-owned actions pinned to SHAs, approval for outside contributors' workflows,
  Dependabot alerts and updates, secret scanning and push protection, private vulnerability reporting, and rulesets
  that protect `main` (pull request, passing CI on Ubuntu, macOS and Windows, no force push or deletion) and `v*` tags.
- The CodeQL workflow can also be started by hand (`workflow_dispatch`), so a baseline scan does not have to wait for
  the weekly schedule.

## 2026-10-24 — Cross-platform installer for Claude Code and Codex (macOS, Linux, Windows)

- `install.sh` is now the single entry point: `--target claude|codex|all` (default `claude`, so existing
  behaviour is unchanged), `--help`, and everything after `--` is passed to `install-codex.sh`.
- New `install.ps1` for PowerShell: finds Git Bash (skipping the WSL launcher in `System32`) and delegates to
  `install.sh`, so Windows and Unix cannot drift apart.
- New `tools/install-common.sh`: OS detection (macOS, Linux, WSL, Git Bash) and a Python finder that executes each
  candidate (`python3`, `python`, the `py` launcher) instead of trusting `PATH`, which skips the Windows Store
  stub. Codex requires 3.11+, Claude 3.8+. Missing Python now fails early with per-OS install advice.
- The hooks resolve Python the same way at run time instead of hard-coding `python3`.
- `install-codex.sh` writes the hook path in native form on Git Bash (`cygpath -m`).
- `.gitattributes` forces LF on shell scripts so a Windows checkout cannot break `bash install.sh`.
- New `tools/test_install.sh` (argument validation, default-target isolation, both targets, idempotence, hooks
  registered exactly once, hook emits valid JSON). CI runs it on Ubuntu, macOS and Windows, plus the PowerShell
  launcher on Windows.
- - Documentation updated throughout: `README.md` rewritten (requirements per OS, install, Windows notes, layout,
  checks), `USAGE.md`, `AGENTS.md`, `CLAUDE.md` pointer, `CONTRIBUTING.md`, `SECURITY.md`.
- Security hardening from the review of this change: `install-codex.sh` refuses a `CODEX_HOME` containing
  `"`, `$`, a backtick, a backslash or a newline (checked in the forward-slash form on Git Bash) before writing
  anything, since the path is embedded in a hook command run later through a shell; `settings.json` and
  `hooks.json` are now written atomically (temp file plus rename, file mode preserved); the CI actions are pinned
  to commit SHAs.
- Windows CI caught a real bug on its first run: `build_codex.py` read skill files with Python's default encoding
  (cp1252 on Windows) and crashed on UTF-8 content. Every read and write in the generator and the installers'
  embedded Python now names `encoding="utf-8"` and writes LF.
- Windows behaviour is covered by CI only; I could not run Windows locally.

## 2026-10-24 — Security review hardening

A manual security review of the published copy found one injection path and four unpinned or unsafe
install steps. Fixed:

- Both SessionStart hooks no longer copy `.zeno/project.md` text (Goal, Next step) into the session; a
  cloned repo could plant instructions there. They now state that a thread exists and point to
  `/zeno resume`. The branch name is sanitized to `[A-Za-z0-9._/-]` and capped at 100 characters.
- `graphify` installs a pinned `graphifyy==0.9.95` and no longer falls back to `--break-system-packages`.
- The CircleCI template no longer pipes a remote script into `sudo bash`; it downloads a pinned release and
  verifies its checksum.
- The build-resolver skill and agent use `npm ci` and no longer delete `package-lock.json`.
- `agent-browser` is pinned to `0.39.2`.

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
