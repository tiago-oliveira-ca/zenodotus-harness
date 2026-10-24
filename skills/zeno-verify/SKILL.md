---
name: zeno-verify
description: >
  The evidence gate for the zeno loop's Review step. Never claim work is done, passing, or fixed
  without running the proving command in this same message and reading its real output. Verify
  goal-backward — re-read the Scope's Done looks like and prove each deliverable, not just green
  tests. Check for stubs, self-review the diff (severity-gated), then present the finish menu and
  wait for the human. Trigger on: "is it done", "does it work", "verify", "prove it", "confirm",
  "it should pass", "Review gate", "mark complete", "ready to commit", "ready to merge", "did the
  tests pass", "is the bug fixed".
---

# Zeno Verify — evidence before claims

This is Gate 4 of the zeno loop. Claiming something works without checking is not efficiency, it is
guessing out loud. The principle: **evidence before claims, always.**

**Iron Law: NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION EVIDENCE.** If you did not run the
proving command *in this message*, you cannot say it passes. "Should work," "probably fine," and
"looks done" are not evidence. This governs every completion claim, not just user-facing ones —
marking an observation-log entry ACTIONED, flipping a card's Status, or noting a PR as merged
without checking it actually merged are claims this Iron Law covers too.

## The gate function (run before any success statement)

1. **Identify the proof.** What command or observation would actually demonstrate this claim?
2. **Run it fresh.** Now, fully, in this message — not from memory of an earlier run.
3. **Read the whole result.** Full output, exit code, failure count — not just the last green line.
4. **Confirm it matches the claim.** Does the output actually support what you're about to say?
5. **Only then speak.** If any step was skipped, you are not ready to claim.

## Full-repo phase check (steps 1-3 mandatory for any code diff; the rest for larger changes)

**Steps 1-3 are the mechanical clean-code gates and are not optional on a diff that touches
product code** — they are the only clean-code checks that cannot be rationalized past, and their
real output belongs in Proof next to the tests. Run the remaining steps for a change that touched
many files or a full feature/Story; they catch regressions the goal-backward check alone might
not exercise:

**Content-only deliverables (documentation, skill/config files, no language toolchain) substitute
goal-backward grep/read verification for steps 1-4** — there is no build/type/lint/test command to
run against prose, so treating one as required would either stall on a nonexistent command or
produce a rationalized skip of proof altogether. Steps 5-6 (secret/log scan, diff review) still
apply to any diff, code or not. This mirrors Gate 3's own non-code carve-out in `zeno/SKILL.md`
("the pipeline applies to non-code deliverables too... acceptance criteria become concrete
verification checks").

1. **Build** — does the project actually build (`npm run build`, `pnpm build`, or the stack's
   equivalent)? Stop and fix before continuing if it doesn't.
2. **Types** — run the type checker (`tsc --noEmit`, `pyright .`, or equivalent); report and fix
   critical errors.
3. **Lint + format** — run the linter and formatter check (`npm run lint`, `ruff check .`,
   `black --check`/`prettier --check`, or the stack's equivalent). If the repo has no configured
   linter, say so explicitly in Proof rather than silently skipping the gate — and treat that as
   a finding: see `zeno-stack/zeno-git-workflow`'s "Wiring the Mechanical Quality Gate" for the
   pre-commit/CI setup that makes these checks survive a skipped checklist.
4. **Full test suite with coverage** — report total/passed/failed and coverage against whatever
   threshold the repo has set.
5. **Secret/log scan** — grep the diff for hardcoded secrets/API keys and leftover debug logging
   (`console.log`, stray `print`) that shouldn't ship.
6. **Diff review** — `git diff --stat` / `git diff <base> --name-only`, then read every changed
   file for unintended changes, missing error handling, and edge cases.

Beyond the mandatory first three steps this is a speed/coverage helper, not a substitute for
goal-backward verification below — a fully green phase check does not by itself prove the Scope's
"Done looks like" was delivered.

## Goal-backward verification (verify the outcome, not the tasks)

Green tests prove the code does what the tests say — not that you delivered what was asked. So:

- **Re-read "Done looks like"** on whichever card is closing — the Task/SubTask if that's what's
  closing, the Story if every Task under it is done, the Feature if every Story under it is done,
  the Epic if every Feature under it is done. Enumerate the deliverables it implies.
- **Prove each one** by exercising the real flow end-to-end and observing it — a passing unit test is
  necessary, not sufficient. Record each proof (command + observed result) in that card's **Proof**
  section, referencing the deliverable it satisfies, then roll a one-line summary up into
  `.zeno/project.md`'s **Proof** section.
- A deliverable with no fresh evidence is **not done**, even if the suite is green.
- **Trivial edit with no Scope?** A one-liner that skipped Scope has no card and no "Done looks
  like" to read — verify the edit directly (exercise the exact thing you changed) and log a
  one-line proof straight to `.zeno/project.md`'s Proof section.

## Stub / incompleteness check

Before declaring done, scan the change for stubs, `TODO`/`FIXME`, `NotImplemented`, hardcoded
placeholder returns, and swallowed errors. "Tests pass" over a stubbed implementation is a false
done. If it's a knowing placeholder, park it in `.zeno/project.md`'s Open questions / parked
section (referencing the item) rather than claiming it.

## Self-review the diff (not the story)

Review the actual diff, not your memory of what you intended, severity-gated:

- **Critical** (breaks existing behavior, security, data loss) — blocks done; fix now.
- **Important** (missing case, weak error handling) — blocks the next step; fix or log.
- **Minor** (naming, style) — note and defer.

No performative agreement. "You're absolutely right!" or "Perfect!" before you've actually
re-checked the code masks whether evaluation happened. Verify against the real code, then speak.

**Independent review, where a specialist applies.** Self-review catches what the same agent that
wrote the diff can see — which is not nothing, but it is not independent. If the diff falls inside
a domain covered by `agents/REGISTRY.md` (a language, a framework, security-sensitive surface) with
an **Advisor-tier** row, invoke that specialist for a fresh read of the diff *in addition to*
self-review, rather than relying on self-review alone for domain-specific correctness. Where the
registry's only match for the domain is Owner-tier (an execution role — it builds within its
domain, it doesn't review someone else's diff), self-review remains the check; don't invoke an
Owner-tier agent as if it were an independent reviewer. This does not change who approves — the
human is still the sole merge/PR/keep authority below — it means the human's decision is informed
by an independent opinion where one exists, not just the builder's own account of its work.

**Spawning it safely.** An Advisor's `Bash` is observation-only by contract (it may run the suite,
linters, and `git diff`/`log`/`status`; it may not switch branches, stash, commit, or mutate
files — see `agents/_agent-template.md`). Belt and braces, since a reviewer at this gate runs
against a branch that usually carries uncommitted work: if `git status --short` isn't clean when
you spawn it, either commit first (Gate 3's duty, see the finish tail below) or pass
`isolation: "worktree"` so the review runs on its own copy. A reviewer that stashes or switches
branches underneath an in-flight change can silently cost the work being reviewed.

## Finish tail (integration is the human's call)

When the goal is proven and the diff is clean, close out — but don't self-merge:

1. Run the **full** suite one last time; read the result.
2. Add a 2-3 line **Outcome** summary to the closing card and flip its Status → `closed`; when the
   top-level item (the Epic, or the Feature/Story if there's no parent Epic) is what's closing,
   also write the Outcome to `.zeno/project.md` and flip its Status → `closed`, and move the item
   to the Kanban board's Closed column.
3. **Append a `CHANGELOG.md` entry — every delivery, unconditionally.** This is not gated on
   doc-worthiness the way the documentation check below is: even a purely internal delivery gets a
   dated, PR-referenced entry (what changed, one paragraph), because `.zeno/` cards get pruned
   after merge and `CHANGELOG.md` is the durable, human-facing record that survives that pruning.
   A trivial edit that skipped Scope entirely still gets a one-line entry, the same way it already
   logs straight to `project.md`'s Proof section with no card.
4. Run the **documentation check** below (system docs — conditional on doc-worthiness, unlike step 3).
5. **Commit any outstanding work first, then** present the options — **merge locally / push + open
   PR / keep as-is** — and **wait** for the human to choose. Do not integrate to a main branch
   without explicit consent. Run `git status --short`: if the tree isn't clean, that is a Gate 3
   miss to close *before* the menu, not a question for the human. Committing to the working branch
   is the agent's own duty and never needed permission — what's gated here is **integration**
   (merging, pushing to trunk, opening a PR). A finish menu presented over uncommitted work asks
   the human to decide about something that doesn't exist in git yet.
6. **Verify the merge with a real command before archiving — don't rely on the human's word alone
   or on memory of having run the merge earlier in this session.** Confirm via `gh pr view <n>
   --json state,mergedAt` (or `git log --oneline <base>..<branch>` / checking the merge commit is
   reachable from the trunk branch) that the PR actually shows merged, not just opened or claimed.
   This closes a real, observed failure mode: a fix gets written and its observation-log entry
   marked ACTIONED, but the PR carrying it is simply never merged — sitting open and unnoticed
   until something else forces a check, while the very problem the fix was meant to close recurs
   in the meantime because the fix never actually shipped. Once merge is verified — and deploy
   confirmed, for a repo with a separate deploy step — archive the card(s), don't delete them.
   `git mv` the delivered item's file(s) from `.zeno/docs/{stories,tasks,features}/` into `.zeno/docs/archive/
   {stories,tasks,features}/` (create the archive subfolder if it doesn't exist yet). Epics are
   not archived individually — only once the whole Epic itself closes. Rewrite every
   `docs/stories/`, `docs/tasks/`, `docs/features/` path reference to the archived card(s) in
   `project.md` to its new `docs/archive/...` path — do not touch references to cards that are still
   open. After rewriting, grep-verify every `docs/` path `project.md` now references actually
   resolves on disk (zero broken links) before considering this step done. `project.md`'s Kanban
   board and Epics/Features checklist rows **stay** — still updated to `[x]`/Closed as before, but
   now pointing at the archive path instead of being deleted. Still condense the rolled-up `Proof`
   line to a one-liner pointing at the PR/commit; still leave `project.md`'s **Decisions** log
   untouched — it's institutional memory about *why* a choice was made, independent of any one
   card, not a record of the delivered item itself. Don't archive before merge (or deploy) is
   actually verified — a card for work still in flight stays in the active `docs/` folders.

## Documentation check (the check is mandatory; the edit is doc-worthy-gated)

Always run this check before "done" — never skip running it, and never treat a Story's own
Gate-2-planned, Gate-3-executed documentation Task as satisfying it by itself. That Task covers
*that Story's* own diff; this check runs once more, here, at the scope of whichever card is
actually closing (the Story if it has no parent Feature, the Feature once every Story under it is
done, the Epic once every Feature under it is done) — the same closing-scope goal-backward
verification above already uses. Two distinct questions, only the second doc-worthy-gated:

1. **Did each Story's own documentation Task actually happen?** Confirm, don't assume — a Story
   whose last Task has no Proof entry isn't closed, whatever the rest of its Task list shows.
2. **Does the system's documentation still describe the system, now that the closing item is fully
   delivered?** This is the question no single Story's Task can answer alone, because no single
   Story owns the whole picture — a README's feature list, an inventory or routing table, or an
   architecture note can drift from the *sum* of several individually-fine Stories even when each
   one's own diff was narrowly correct. If the closing item touched a **public API, architecture,
   dependencies, or setup** (the `documenting-code` trigger table) **at the item's own scope** —
   not just any one Story's diff — run the `documenting-code` discipline / `/docs-drift` to
   reconcile the anchored system docs (README, architecture notes, API reference), or record an
   explicit `TODO(doc-drift:)`. For a purely internal item, this still runs, it just correctly
   finds nothing to do — do not manufacture doc churn to force an edit here.

**Feature/Epic-tier only — system documentation completeness.** When the closing item is a
Feature or an Epic (it went through Gate 1's DDD, i.e. an architecture decision was actually made,
not just an ad hoc Story's small diff), question 2 above also asks whether a **full documentation
set** exists for the component the item touches, across three kinds — reusing the skills that
already own each, not inventing new ones:
- **Architecture & Design** (component diagrams, data flow, high-level structure) —
  `documentation/solution-architecture-standards` + `documentation/architecture-documentation-and-decision-records`.
- **Technical & API Specs** (algorithms, database layout, integration endpoints) —
  `documenting-code` + `documentation/technical-requirements-standards`.
- **User & Admin Guides** (end-user operation; staff setup/troubleshooting) — the Admin half is
  `documentation/operations-standards`; the User half has **no owning skill yet** in this repo —
  say so explicitly rather than silently reaching for the nearest-sounding leaf.

If reconciling reveals **no full set exists at all** for the touched component, don't try to
backfill all three inline as part of this delivery — that's Epic-sized work in its own right, not
a Review-gate side effect. Instead, **flag it**: record the gap in the closing item's Decisions log
and `project.md`'s Open questions / parked section, and *recommend* — never silently create — a new
Epic scoped to build the missing documentation set. The human decides whether to open one, the same
as every other integration decision this gate already defers to them; this is a flag on the finish
menu, not a fifth gate; the recommended Epic, if opened, runs through the ordinary four gates like
any other work.

(This is independent of the `CHANGELOG.md` entry above, which happens either way.)

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Claiming done from confidence | Run the proving command, then claim |
| Shipping an API/setup change with stale docs | Run `/docs-drift`; reconcile via `documenting-code` |
| Skipping the documentation check because the change "looks internal" | Always run the check; only the resulting edit is doc-worthy-gated |
| Treating a Story's own documentation Task as satisfying Gate 4's documentation check | Gate 4's check runs again at the closing item's own scope (Story/Feature/Epic) — confirm the Task happened, then separately ask whether the *system's* docs still hold |
| Backfilling a missing full documentation set inline because Gate 4 noticed the gap | Flag it — Decisions log + `project.md` Open questions — and recommend an Epic; don't absorb Epic-sized doc work into this delivery |
| Silently opening the recommended documentation Epic without asking | The human decides whether to open it, same as every other integration call this gate defers to them |
| Closing a card with no `CHANGELOG.md` entry | Append one unconditionally — every delivery, not just doc-worthy ones |
| "Tests pass" = "goal delivered" | Verify goal-backward against Done looks like |
| Reading only the final output line | Read full output, exit code, and failure count |
| Reusing a stale earlier run as proof | Re-run fresh in this message |
| Declaring done over a stub/TODO | Scan for stubs; park knowing placeholders in Open Questions |
| Reviewing your intent, not the diff | Self-review the actual diff, severity-gated |
| Calling code clean when no linter/formatter/typechecker ever ran on it | Run the mechanical gates fresh and record their real output in Proof |
| "You're absolutely right!" reflex | No performative agreement; verify against real code first |
| Self-merging to main | Present merge/PR/keep and wait for the human |
| Presenting the finish menu over a dirty tree | `git status --short` first; commit the outstanding work on the working branch (your duty, not the human's), then present |
| Reading "the human decides" as covering `git commit` | It covers integration only — merge, push to trunk, PR. Uncommitted work has no rollback points and dies with the session |
| Relying only on self-review for a domain with an Advisor-tier registry match | Also invoke that specialist from `agents/REGISTRY.md` for an independent pass |
| Leaving a delivered item's card sitting in `.zeno/` after it's merged and deployed | Archive (git mv into `docs/archive/`, rewrite `project.md`'s references) once integration is confirmed |
| Marking an observation ACTIONED (or a card archived) without checking the PR actually merged | Verify with a real command (`gh pr view`, `git log`) before the claim, not just memory of having acted |
| Trying to run (or silently skipping) a nonexistent build/lint command against a content-only diff | Substitute goal-backward grep/read verification for steps 1-4; the carve-out is for the mechanical gates, not for proof itself |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "The tests are green, it's done" | Green tests ≠ the goal delivered; check Done looks like |
| "I'm confident it works" | Confidence is not evidence; run the command |
| "The agent said it succeeded" | Verify independently via the diff, not the report |
| "I'll just commit, it's fine" | Unverified commits are how broken code ships |
| "It's basically done" | "Basically" means a deliverable is unproven — prove it |
| "Self-review is basically the same thing" | Self-review only catches what the builder already believes; that's the whole reason an independent pass exists |
| "This delivery is too small/internal for a changelog entry" | `.zeno/` gets archived, not deleted, but `CHANGELOG.md` is still the durable, easy-to-scan cross-repo record — one line still costs nothing |
| "I already wrote the fix, it counts as done" | Writing the diff isn't the claim being made — verify the PR actually merged before calling it ACTIONED or archiving |
| "This is just a skill/doc file, no need to verify" | No toolchain doesn't mean no proof — grep/read verification against Done looks like still applies |
| "Every Story already got its documentation Task, Gate 4's check is redundant" | A per-Story Task covers that Story's own diff; no single Story owns the README/inventory/routing-table picture the whole Feature adds up to — Gate 4 asks that question separately |

## Red flags — stop before you claim

- Hedging words: "should," "probably," "seems," "I think."
- Premature celebration ("Done!", "Perfect!") before the command has run.
- About to commit / push / PR on unverified work.
- Trusting a delegated agent's success report instead of the diff.
- A partial check standing in for the whole.
- About to say "done" on a diff in a domain with an Advisor-tier registry match, with no independent pass from it.
- About to close a card without a `CHANGELOG.md` entry.
- Skipping the documentation check itself rather than running it and finding nothing doc-worthy.
- Closing a Feature (or Epic) whose documentation check only re-confirmed its Stories' own Tasks, never asking whether the delivered item's system-level docs still hold.
- A Feature/Epic closing against a component with no Architecture & Design, Technical & API Spec, or User & Admin Guide documentation at all, and no flag recorded about it.
- Marking an observation ACTIONED, or a card archived, without checking the PR's merge state with a real command.
- About to skip goal-backward verification because the diff has no language toolchain to run gates against.

## Pre-flight checklist — run before delivering any Review-gate claim

- [ ] The proving command was identified and run fresh in this message.
- [ ] Full output + exit code + failure count were read, not just the last line.
- [ ] Verified goal-backward: each Done looks like deliverable exercised and recorded in the card's Proof section, rolled up into `.zeno/project.md`.
- [ ] Stub/TODO/placeholder scan done; knowing placeholders parked in Open Questions.
- [ ] The actual diff was self-reviewed, severity-gated; no performative agreement.
- [ ] For a code diff: the project's mechanical gates (format, lint, typecheck) ran fresh in this pass and their real output is recorded in Proof alongside the tests — clean code no linter has seen is a claim, not evidence.
- [ ] For a content-only diff (no language toolchain): goal-backward grep/read verification substituted for the build/type/lint steps, not skipped without a substitute.
- [ ] For a code diff: the matching `code-standards` leaf's pre-flight checklist was run against the diff (naming, structure, error handling, function size — whatever that leaf mandates).
- [ ] If the diff falls inside a domain `agents/REGISTRY.md` covers with an Advisor-tier row, that specialist gave an independent pass — not self-review alone.
- [ ] The documentation check ran (always) at the closing item's own scope, not just re-confirmed a Story's own Task: each Story's documentation Task was confirmed actually done (Proof entry present), and separately, if the closing item was doc-worthy at its own scope (API/arch/deps/setup), system docs were reconciled via `documenting-code` / `/docs-drift` (or a `TODO(doc-drift:)` left) — otherwise it correctly found nothing to do.
- [ ] For a Feature/Epic closing: checked whether a full documentation set (Architecture & Design, Technical & API Specs, User & Admin Guides) exists for the touched component — if not, flagged it (Decisions log + `project.md` Open questions) and recommended an Epic rather than backfilling inline or opening one unasked.
- [ ] A `CHANGELOG.md` entry was appended for this delivery — unconditionally, not gated on doc-worthiness.
- [ ] Merge (and deploy, where the repo has one) was verified with a real command (`gh pr view`/`git log`), not assumed from the human's word alone or memory of an earlier action, before the delivered card was archived (`git mv`) into `.zeno/docs/archive/`, not deleted — `project.md`'s Kanban/checklist rows stay, updated to point at the new path, and a broken-link check confirmed every referenced path resolves.
- [ ] Outcome summary written, Status flipped, and the merge/PR/keep choice left to the human.
- [ ] `git status --short` run and clean before the menu was presented — all work committed on the working branch (integration, not committing, is what waits for the human).
