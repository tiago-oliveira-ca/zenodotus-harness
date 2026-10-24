---
name: zeno
description: >
  The single always-on workflow for any non-trivial coding task. Runs four gates in order —
  Scope (architecture council via zeno-council, then design via zeno-insight; Epic->Features enumeration and Feature-domain DDD framing),
  Route (repo-root .zeno/: project.md State/Goal/Decisions/Next step/Proof plus a SAFe/Lean
  Epic->Feature->Story->Task->SubTask backlog; also fully plans a Feature's Story list (FDD) and
  every Story's Acceptance Criteria/Scenarios/Task breakdown (ATDD/BDD) before any coding starts),
  Execution (a pure TDD implementation loop via the zeno-workflow dispatcher over the
  already-planned Task list; zeno-debug for bugs), Review (goal-backward evidence via
  zeno-verify). Fixed, templated ceremony — no ad hoc files. Invoke
  at the START of any build/fix/change before writing code, and to resume a repo's thread.
  Trigger on: "project.md", "run zeno", "let's build", "implement", "add a feature", "fix this
  bug", "start a task", "resume where we left off", "pick this back up".
---

# Zeno — one loop for every non-trivial task

Before writing code for any non-trivial change, run all four gates **in order**:
**Scope → Route → Execution → Review.** The gates are always on; the machinery is a fixed,
templated folder — not a free-for-all, but not a single cramped file either.
One skill, one command (`/zeno`), one `.zeno/` folder per repo.

The name is Zenodotus — the first librarian of Alexandria. The job is the same: keep the thread,
so nothing is lost between sessions — now scaled to a real backlog instead of one task at a time.

**Iron Law: EVERY NON-TRIVIAL TASK RUNS ALL FOUR GATES.** The discipline is uniform; only genuinely
trivial edits (typo, rename, one-line config) skip straight to Review.

## When it fires (escalation is always)

Every non-trivial task runs the full loop. There is no "size heuristic" that lets you skip gates —
there's a **sizing ladder** for how much of the backlog hierarchy a task earns (see Gate 2). The
principle: **the objection to ceremony is about *free-form* machinery, not fixed structure.** Heavy
systems drown you in ad hoc agents, phase trees, and per-step files with no shape. Zeno keeps the
discipline and constrains the machinery to one fixed layout — the entire system is this skill, the
`/zeno` command, and one `.zeno/` folder per repo.

If in doubt about whether a task is trivial: it isn't. Run the loop.

## Gate 1 — Scope

**Step 0 — the Architecture Council (`zeno-council`).** Every non-trivial Scope opens with it,
before any approach is proposed. Depth follows the work: **Lite** (one card line, no questions) for
Story-tier work with no new boundary, data store, integration, security posture or NFR; **Full**
(question rounds, options, debate, recommendation) on named evidence. Its questions share
`zeno-insight`'s round format and the card's Decisions log — one backlog, not two.

**If any Full evidence applies — a new boundary, data store, integration, sensitive data, security
posture, NFR, or Feature/Epic tier — invoke the `zeno-council` skill now, before designing or writing
a card, ask any blocking questions and stop for their answers; if none block, proceed to options.** (The skill defines what blocks; do not
apply that test from memory, load the skill.) Noticing the evidence and then
designing anyway ("Council Lite+") is the failure this step exists to prevent: cold runs that logged
"new integration, sensitive data" still built the service without asking one question. If blocking
unknowns remain in a headless run (nobody to answer), its deliverable is those questions and its
assumptions; it does not implement past an unanswered blocking unknown.

**Then design via `zeno-insight`**: explore the context, weigh 2-3 approaches, get explicit
sign-off before code. When the change touches shared/public surface, **map the affected area first**
(codemaps / `graphify` when present, else grep) so the design accounts for what it touches — see
`references/impact-analysis.md`. Size the request to a card tier — ad hoc Story, Feature, or Epic
(see Gate 2's sizing ladder) — then identify which domain(s) the work touches and select the
minimum sufficient specialist(s) from **`agents/REGISTRY.md`** (often none, for small work).
Capture the outcome as the three Scope lines — **Problem / Approach / Done looks like** — on that
card.

**Gate 1 owns the vision-and-capability layer — Epics and Features — not just their Scope lines:**
- **Epic-tier work:** before this gate closes, enumerate the Epic's Features onto its
  `## Features` list — each a distinct business capability answering "what major value does this
  add?" Each Feature is its own later lifecycle item (its own Gate 1 pass when picked up, subject
  to the WIP-1 rule), not framed in this same pass.
- **Feature-tier work** (standalone, or a Feature picked off an Epic's list): before this gate
  closes, run **`zeno-workflow`**'s `zeno-ddd` to frame that Feature's domain (Bounded Context,
  subdomain classification, Entities/Value Objects, Aggregate root(s)) onto the Feature card;
  DDD framing happens at Scope, not Execution.

Story-list decomposition (FDD) and per-Story planning (ATDD/BDD/Task breakdown) are Gate 2's job —
Gate 1 stops at a framed Feature (or an enumerated Epic), never a Story list. No implementation
code before this gate closes.

## Gate 2 — Route

**Gate 2 is the sole writer of `.zeno/project.md`.** Do these in order, every time this gate runs
— not only at session start:

1. **Check the branch before touching anything.** Run `git branch --show-current` and
   `git status --short` as this gate's first action, before writing any Scope/card content or
   editing a product file. If the current branch is the repo's trunk (`main`/`master`/its default)
   and the task is non-trivial, create/switch to a working branch now, per
   `zeno-stack/zeno-git-workflow` — `.zeno/` rides along in the same diff as the rest of the
   work, so it has to land on the right branch from the start, not be moved there later. This
   closes a gap that recurred three separate times in this repo's own history (a rule stated only
   in Gate 3's prose and Gate 4's pre-flight checklist was skipped through all of Execution each
   time, because nothing forced the check at the point the risk was introduced — see
   `~/.claude/skill-observations/log.md` Observations 34/38/41).
2. **Reconcile against reality.** Check `git log` / the working tree against `project.md`'s State and
   Next step so a stale line doesn't send you redoing finished work or silently overwriting a
   change that landed outside this thread (a concurrent session, a merge since `project.md` was last
   read). Do this whenever Gate 2 is touched, including mid-session — not only when resuming a
   thread from cold.
3. **Confirm the installed skill copy is current.** In a session that has already spanned multiple
   Feature/Story cycles, check whether the installed copy of `zeno` (or any zeno method skill in
   active use) has changed since it was loaded — its file mtime is enough of a signal. If it has,
   flag the drift to the human rather than continuing on a stale copy of the methodology; which
   way to resolve it (re-read now, retrofit in-flight work, or accept the gap) is the human's call.
4. **Ensure a repo-root `./.zeno/` folder exists** — create `project.md` from
   `references/project-template.md` if absent — then write Gate 1's Scope into the right card and
   refresh `project.md`'s **Updated** date. Keep **State** and **Next step** live as you work — they
   make cross-session resume cheap. One `.zeno/` folder per repo, at the root, committed with
   the repo as durable memory.
5. **Migrate a legacy thread or an old `.project/core.md` layout, if either exists.** If the
   repo's thread predates this layout (a single `THREAD.md` or similar), run
   `references/migration.md`'s THREAD.md recipe to completion — through deleting the legacy file —
   rather than inventing a mapping or leaving it in place. If the repo instead already has the
   pre-rename `.project/core.md` layout, run `references/migration.md`'s rename recipe instead — a
   mechanical `git mv`, not a content migration, since the five-card-type model itself didn't
   change. A `start` that returns with either the legacy thread or the old `.project/` layout still
   on disk hasn't finished Gate 2.
6. **Fully plan the Story/Task backlog before this gate closes — no planning is left for Gate 3.**
   For Feature-tier work: run **`zeno-workflow`**'s `zeno-fdd` to write the Feature's complete
   ordered Story list. Then, for **every** Story on that list — not just the next one — run
   `zeno-atdd` (Acceptance Criteria) → `zeno-bdd` (Given/When/Then Scenarios) → a technical
   Task-breakdown pass, written directly by this gate (not a `zeno-workflow` dispatch): real
   implementation-step decisions per Task — which files, what approach — Engineering-owned detail,
   not a placeholder one-liner. Always end each Story's Task list with a dedicated documentation
   Task (create/update). For an ad hoc Story (no parent Feature), skip the FDD list-writing — there
   is no Feature to list — but still run ATDD → BDD → Task breakdown on that one Story. Gate 3
   opens as a pure implementation loop only once every Story reachable from this pass is planned
   this way.

`.zeno/` is a **SAFe/Lean-governed backlog**, not a single append-only file: `project.md` is the
portfolio index (Kanban board + Epic/Feature index), and each backlog item gets its own card under
`.zeno/docs/`. **Sizing ladder** (decides how much of the hierarchy a task earns):

**Sizing is a gate with a default, not a menu. Start at the smallest tier that fits the work and
climb only on named evidence** — the evidence being the work's actual shape (independently
verifiable Stories, several Execution passes, multiple subsystems), never how thorough or formal
the request sounds. **Ceremony depth follows the work, not the prompt's tone:** "run your full
process with all the gates" is a request to run the loop properly at the tier the work earns, not
a request to climb the ladder. Opening a **Feature** card carries a burden of proof — name the
two or more independently-verifiable Stories it decomposes into; if you can't, it's a Story with
a Task list. An **Epic** carries the same burden one rung up (name the Features). **Record the
chosen tier and the one-line evidence for it on the card**, so the decision is auditable instead
of implicit. Over-tiering is not a safe error: planning spends the same finite budget the
implementation needs, and a Feature card wrapping one Story's worth of work reliably ships less
than the Story would have — it just looks more impressive on disk.

- **Trivial** (typo, rename, one-line config) — no card at all, skip straight to Review.
- **Small** (one coherent behavior, fits one Execution pass) — an ad hoc **Story** card only
  (`docs/stories/STORY-<slug>.md`), no parent Feature. A Story that needs more than one sitting to
  implement still breaks into its own **Task** list (`docs/tasks/TASK-<slug>.md`) — this is the
  concrete "reduce context, small tasks per time" mechanism, and it applies independently of
  whether a parent Feature exists.
- **Large** (needs decomposition) — a **Feature** card (`docs/features/FEAT-<slug>.md`) with a
  `zeno-workflow/zeno-ddd`-framed domain and a `zeno-workflow/zeno-fdd`-written Story list, and an **Epic** card
  (`docs/epics/EPIC-<slug>.md`) only when the work genuinely spans multiple Features.
- **A Task itself too big for one sitting** earns its own **SubTask** list
  (`docs/subtasks/SUBTASK-<slug>.md`) — the same sizing discipline applied one rung deeper, not a
  separate tier of the ladder above.

## Gate 3 — Execution

By the time Gate 3 opens, planning is done. Gate 1 already framed the domain (DDD); Gate 2 already
wrote the Story list (FDD) and fully detailed every Story's Acceptance Criteria (ATDD), Scenarios
(BDD), and Task breakdown. **Gate 3 is a pure implementation loop:** pull the next `[ ]` Task (or
SubTask, if that Task has its own SubTask list) off the active Story's Task list, and run
**`zeno-workflow/zeno-tdd`**'s red/green/refactor cycle against it, one Scenario at a time, until
the Story's Task list is exhausted.

| Stage | Scope | Owner | Planned in |
|---|---|---|---|
| **TDD** — Red/Green/Refactor | once per Task (or per SubTask, if the Task has a SubTask list), looped until the Story's Task list is exhausted | `zeno-workflow/zeno-tdd` | Gate 3 (this gate) |

DDD, FDD, ATDD, and BDD no longer run here — see Gate 1 (DDD) and Gate 2 (FDD, ATDD, BDD, Task
breakdown). This applies to non-code deliverables too (documentation, skills, config): TDD's
red/green becomes absent-before/present-after evidence on the card. **Every Story's Task list ends
with a dedicated documentation Task** (planned in Gate 2): implement it via `documenting-code` /
`/docs-drift` rather than a red/green cycle, using that same absent-before/present-after evidence
pattern.

Every Task shares these duties, in this order:

1. **The branch is already handled.** Gate 2 step 1 checked/created it before Route even started —
   Execution never opens on the trunk branch. If it somehow does, that's a Gate 2 miss to fix
   there, not something to patch around here.
2. **Check blast radius before touching a public/shared symbol** and record impacted areas on the
   active card; see `references/impact-analysis.md`.
3. **Clean code is enforced here, not assumed:** load the matching **`code-standards`** leaf
   *before* writing product code — it carries the language's Clean Code/SOLID rules and its own
   pre-flight checklist, which must run before the work moves to Review. Code written without its
   leaf loaded is a red flag below, not a style preference.
4. **Load the matching `zeno-stack` leaf** for stack-specific depth (React, Python/FastAPI,
   Postgres, Redis, Docker, …) while any Task is running, and load
   **`zeno-stack/zeno-implementation-guardrails`** beside it: it stops architecture-changing or
   data-destructive steps before they are written, not after. When the work would drop or rewrite data, add
   a runtime service, or change a client-visible contract, write the matching flag by name in your reply
   (`DATA MIGRATION RISK`, `ARCHITECTURE IMPACT DETECTED`, `BREAKING API CHANGE`), say what it affects, and
   wait for authorization.
5. **Route to `zeno-debug`** when something breaks or a test won't go green — find the root cause
   before attempting any fix.
6. **Log each decision to the active card as you go, committing one logical change at a time.**
   **Committing to the working branch is your own duty, not a decision to ask about** — the
   human's authority begins at *integration* (merging, pushing to trunk, opening a PR), never at
   `git commit`. Do not read Review's merge-authority rule as a reason to leave work uncommitted:
   an uncommitted tree has no rollback points, loses the per-change record the loop runs on, and
   dies with the session. Finish each Task with its commit; arrive at Review with a clean tree.

The Kanban board's **WIP limit is 1** item outside Backlog/Closed at a time — the same "no more
than one `[~]` step" discipline zeno has always had, now expressed as a literal board rule.

## Gate 4 — Review

"Done" is gated on **exercising the change and observing it work**, verified *goal-backward*
against the closing card's *Done looks like* — not just a green typecheck. Follow **`zeno-verify`**:
run the proving command fresh, prove each deliverable, scan for stubs, self-review the diff, and —
for a diff in a domain with an Advisor-tier `agents/REGISTRY.md` match — get an independent pass
from that specialist rather than relying on self-review alone. Record the evidence in that card's **Proof**
section (rolled up into `project.md`'s Proof section), then write a 2-3 line **Outcome** close-out.
Before presenting the merge / PR / keep choice, confirm `project.md`'s **State** line names the
current branch or PR — a grep-able check (branch name or PR number present in `project.md`); a work
thread that skips a Story card still must touch this line, not just the closing Outcome. A "done"
without fresh Proof evidence is not done. **Every delivery appends a `CHANGELOG.md` entry**,
unconditionally — it is the durable, human-facing record that survives `.zeno/` card pruning,
so a purely internal change still gets a one-line entry. Separately, **always run** the
documentation check — twice over, not once: confirm each Story under the closing item actually
finished its own Gate-2-planned documentation Task (a Proof entry, not just an assumption), *and*
separately ask whether the system's documentation still holds at the closing item's own scope —
no single Story's Task owns a README's feature list, an inventory table, or an architecture note
the way the sum of several Stories can quietly drift it. If the closing item is **doc-worthy**
(public API / architecture / dependencies / setup) at that scope, reconcile via
**`documenting-code`** / `/docs-drift` as part of Review — for a purely internal item the check
still runs, it just correctly finds nothing to write. **For a closing Feature or Epic**, that same
check also asks whether a full documentation set exists for the touched component — Architecture &
Design, Technical & API Specs, User & Admin Guides — and if none does, **flags it and recommends an
Epic** rather than backfilling inline or opening one unasked; see `zeno-verify` for the full detail
and the current skill-ownership gap (no leaf yet owns User Guides specifically). Before archiving a
delivered card, **verify the merge with a real command** (`gh pr view`/`git log`), not the human's
word alone or memory of
an earlier action — a claim of "merged" that was never actually checked is exactly how a fix can
sit unmerged and unnoticed while its own observation log already calls it done.

## The zeno method skills

Zeno owns the **structure** — the loop, the persistence, the gating. The **methods** are companion
skills, each invocable on its own:

- **`zeno-council`** — the Architecture Council (Gate 1 / Scope, step 0): questions first, design
  second; Lite or Full depth; hands its card log to `zeno-insight`
- **`zeno-insight`** — design gate (Gate 1 / Scope), which now also runs DDD (Feature domain
  framing) and Epic→Features enumeration before the gate closes
- **`zeno-workflow`** — the planning-and-implementation pipeline dispatcher, routing to its five
  nested stages across three gates:
  - `zeno-workflow/zeno-ddd` — domain & architecture framing, once per Feature (**Gate 1**)
  - `zeno-workflow/zeno-fdd` — Feature Story-list decomposition, once per Feature (**Gate 2**)
  - `zeno-workflow/zeno-atdd` — business acceptance criteria, once per Story, run for every Story
    before Gate 2 closes (**Gate 2**)
  - `zeno-workflow/zeno-bdd` — Given/When/Then scenarios, once per Story, run for every Story
    before Gate 2 closes (**Gate 2**)
  - `zeno-workflow/zeno-tdd` — red/green/refactor, once per Task (or SubTask, if decomposed
    further), looped over every Task in order (**Gate 3**)
- **`zeno-debug`** — root-cause-first debugging (Gate 3 escape hatch)
- **`zeno-verify`** — goal-backward evidence gate (Gate 4 / Review)

Alongside the method skills, **`agents/REGISTRY.md`** is the specialist-selection registry — 24
bounded-domain agents (reviewers, resolvers, analysts, pipeline-stage guides), each with an explicit contract
(`agents/_agent-template.md`: mission, non-responsibilities, tools, handoff rules, proof criteria).
Selected at Scope (minimum sufficient expertise) and consulted again at Review (an independent
pass) — never spawned ad hoc outside the registry.

## Invocation — start / resume / status / review

Always resolve the repo root with `git rev-parse --show-toplevel` (fallback: `pwd`) and read/write
`<root>/.zeno/`. Dispatch on the invocation's first token (`/zeno start`, `/zeno resume`, etc.):

| Token | Behavior |
|---|---|
| `start` (or no argument and no `./.zeno/project.md`) | **First, check the repo root for a legacy thread** (`THREAD.md` or a similarly named free-form log) **and for the pre-rename `.project/core.md` layout.** If a legacy thread exists, run the THREAD.md migration recipe in `references/migration.md` to completion — including deleting the legacy file and recording the migration as a `project.md` Decisions entry — before continuing. If the old `.project/core.md` layout exists instead, run that same file's rename recipe (a mechanical `git mv`, recorded as a Decision) before continuing. `start` must never leave a legacy thread file or the old `.project/` layout in place once it returns. Then run **Gate 1 (Scope)** — `zeno-council` first, then `zeno-insight`, which sizes the request (ad hoc Story / Feature / Epic — see the sizing ladder above), enumerates an Epic's Features, and frames a Feature's domain (DDD). Create `./.zeno/project.md` from `references/project-template.md` if absent, and the sized card from the matching `epic-template.md` / `feature-template.md` / `story-template.md`, with the Scope + Goal filled in. Then run **Gate 2 (Route)**, which fully plans the backlog before stopping — a Feature's Story list (FDD) and every Story's Acceptance Criteria/Scenarios/Task breakdown (ATDD/BDD). Stop at Gate 3 and await go-ahead — Gate 3 begins as a pure implementation loop over an already-planned backlog, not a planning session. |
| `resume` (or no argument and `./.zeno/project.md` exists) | Read `project.md`'s Kanban board and find the item outside Backlog/Closed (WIP limit is 1). Print Goal / State / Next step from `project.md` and that item's card. Re-enter the loop at the pipeline stage the card's content shows it's at. Do **not** re-Scope unless the Goal has changed. **No item in flight?** Reconcile `project.md` against `git log`/the working tree, print status, then offer the Backlog cards (human picks — each re-enters at Scope) or await new work; with an empty Backlog, say so and stop. |
| `status` | Read-only. Print `project.md`'s Kanban board table, item counts by column, the active item + its stage, its last Decision, and its last Proof entry. Make no edits. |
| `review` | Jump to **Gate 4 (Review)** via `zeno-verify`: exercise the change, append the command + observed result to the closing card's Proof section (and roll a summary line into `project.md`'s Proof section), and flip that card's Status → `closed` — and `project.md`'s Status too, when the top-level item closes — only if the evidence confirms it. Move the item to the Closed column, archiving per `zeno-verify`'s finish tail. |

Write discipline: **append** to each card's Decisions and Proof sections and to `project.md`'s Proof
section — never rewrite history; **overwrite** only `project.md`'s State, Next step, Status, Updated,
and Kanban board, and a card's own Status. `start` must not skip Scope, and must not skip Gate 1's
DDD for Feature-sized work or Gate 2's FDD/ATDD/BDD/Task-breakdown before any Gate 3 TDD cycle
begins. `review` must not flip a card's Status to `closed` without a fresh Proof entry.

## The .zeno/ folder format

A repo's whole backlog, in one fixed, templated layout — not a single file, and not free-form:

```
.zeno/
  project.md                 # portfolio index: State / Goal / Decisions / Next step / Proof,
                              # plus the Kanban board and Epic/Feature index
  docs/
    epics/EPIC-<slug>.md      # optional — genuinely epic-sized work only
    features/FEAT-<slug>.md   # DDD notes + FDD Story list
    stories/STORY-<slug>.md   # ATDD criteria + BDD scenarios + Task list
    tasks/TASK-<slug>.md      # concrete technical step + optional SubTask list + TDD proof (if leaf)
    subtasks/SUBTASK-<slug>.md # optional — only when a Task is still too big for one sitting; TDD proof
    archive/                  # closed cards, git mv'd here on merge+deploy — same 5 types, not a 6th
      epics/ features/ stories/ tasks/ subtasks/
```

`project.md` is organized around five principles — **State** (current reality), **Goal** (the header's
one-liner — the success condition), **Decisions** (choices made and why), **Next step** (the
immediate action), **Proof** (verification evidence) — with the SAFe/Lean framework metadata
(Program Increment, Sprint) and the Kanban board nested under State. The canonical skeletons live in
`references/project-template.md`, `references/epic-template.md`, `references/feature-template.md`,
`references/story-template.md`, `references/task-template.md`, and `references/subtask-template.md`.
Definition-of-Ready / INVEST / story-splitting vocabulary is not reinvented here — see the sibling
skill `documentation/development-planning-standards`.

**Housekeeping for `project.md` itself, periodic, not per-close.** Across many delivery cycles,
`project.md`'s own State/Decisions narrative can accumulate many stacked, superseded entries and grow
unwieldy — each one legitimately left intact per the existing convention, but no longer all
equally relevant to read today. When that happens, the oldest entries can be moved to
`.zeno/docs/archive/core-history.md`, with a one-line pointer left behind in `project.md` at the
point they were removed from. This is deliberately **not** a step in `zeno-verify`'s per-card
finish tail — trimming `project.md` every single cycle would be premature ceremony over a file that's
usually still small. Do it periodically instead, e.g. via `zeno-stack/zeno-config-gc` or a direct
user ask, when the file has actually grown large enough to warrant it.

## Anti-ceremony — what this is NOT

- **Fixed layout, not free-form.** The only files that exist are `project.md` and cards under the
  five `docs/` subfolders (active) or their mirrored home under `docs/archive/` (closed, per
  `zeno-verify`'s finish tail), plus `docs/archive/core-history.md` for periodic `project.md`
  housekeeping — all from their canonical templates. No phase directories, no roadmap files, no ad
  hoc extra files "to organize" — if it's not one of the five card types (active or archived), it
  doesn't belong in `.zeno/`.
- **No ad hoc agent fleet — but bounded, registry-driven specialists are sanctioned.** Zeno itself
  runs inline in the main thread, and large multi-file builds run serially — this rule guards
  against unbounded ad hoc agent spawning and second `.zeno/`-like structures, not against ever
  invoking a specialist. Selecting a specialist from **`agents/REGISTRY.md`** at Scope (minimum
  sufficient expertise) or Review (an independent pass) is the one sanctioned mechanism for
  doing so — table-driven, bounded, and recorded on the card, not free-form. See
  `agents/REGISTRY.md` and `agents/_agent-template.md` for the full specialist architecture.
- One `.zeno/` folder holds the whole backlog — append to the cards that exist, never spawn a
  second `.zeno/`-like structure.
- **`.zeno/docs/archive/` is the permanent in-repo record.** Once a card's work is merged —
  and deployed, for a repo with a separate deploy step — `zeno-verify`'s finish tail archives it:
  `git mv`d into `.zeno/docs/archive/{stories,tasks,features}/`, with `project.md`'s path
  references rewritten to match and its Kanban/checklist rows staying (updated to the archive
  path, not removed). git log, the merged PR, and `CHANGELOG.md` remain the durable *cross-repo*
  record, but each card's own Proof/Decisions detail now survives *in-repo* too, at the path a
  future reader would actually look, instead of being lost to deletion. A card for work still in
  flight is never archived; only delivered ones.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Jumping to code without a Scope | Run `zeno-council` then `zeno-insight`, capture Problem / Approach / Done first |
| Proposing approaches before the council has run | `zeno-council` first (Lite is one card line); architecture is asked before it is proposed |
| "Too small to Scope" | Non-trivial → all four gates; only true one-liners skip to Review |
| A big feature crammed into one pass | Decompose with `zeno-workflow/zeno-ddd` + `zeno-workflow/zeno-fdd` into a framed domain and Story list |
| A Feature/Epic card opened for work one Story would hold | Default to the smallest tier that fits; climb only on named evidence (two or more independently-verifiable Stories), and record the tier + evidence on the card |
| Raising the tier because the request sounded formal or thorough | Ceremony depth follows the work's shape, never the prompt's tone |
| Skipping a planning stage before coding starts (e.g. a Task with no BDD scenario behind it) | Run DDD (Gate 1) → FDD→ATDD→BDD→Task breakdown (Gate 2) → TDD (Gate 3) in order; no stage is optional once its scope applies |
| Starting Gate 3 with any Story still unplanned (no ATDD/BDD/Task breakdown) | Gate 2 doesn't close until every Story reachable from this pass is fully planned — Gate 3 opens with zero planning left |
| A Story's Task list with no documentation Task at the end | Gate 2 always appends one when writing the Task breakdown — it's not optional |
| More than one item outside Backlog/Closed at a time | Respect the Kanban board's WIP limit of 1 |
| Spawning an agent outside `agents/REGISTRY.md`, or ad hoc files outside the fixed `.zeno/` layout | One inline loop, one `.zeno/` folder, five card types, specialists only via the registry |
| Invoking every agent whose domain sounds relevant | Select the minimum sufficient specialist(s), recorded on the card |
| Patching a bug without diagnosis | Route to `zeno-debug`; root cause before fix |
| Writing product code without the matching `code-standards` leaf loaded | Load the leaf first; run its pre-flight before Review — clean code is gated, not assumed |
| Editing a widely-called symbol without checking callers | Run impact analysis first (`references/impact-analysis.md`) |
| Updating `project.md`'s State only at the end | Update State + Decisions as you go |
| `project.md`'s State silent on the current branch/PR at Review | Name the branch/PR in State before presenting merge/PR/keep |
| Claiming "done" from green tests | Review goal-backward per `zeno-verify`; record the evidence |
| Closing a card with no `CHANGELOG.md` entry | Append one unconditionally — every delivery, not just doc-worthy ones |
| Skipping the documentation check because the change "looks internal" | Always run the check; only the resulting edit is doc-worthy-gated |
| Treating a Story's own documentation Task as Gate 4's documentation check | Gate 4 runs the check again at the closing item's own scope — no single Story's Task owns the system-level picture |
| Trusting self-review alone for a domain with an Advisor-tier registry match | Also get an independent pass from that specialist |
| Self-merging when Review passes | Present merge/PR/keep; the human decides integration (merge / push to trunk / PR) — not whether you may commit |
| Leaving work uncommitted because "the human decides" | Commits on the working branch are yours to make; only integration is gated. Presenting the finish menu over a dirty tree is a Gate 3 miss — commit first, then present |
| Writing Scope/card content or a product-file edit before checking the branch | Gate 2 step 1: `git branch --show-current` + `git status --short`, first action, every time |
| Following a long session's original read of `zeno` without rechecking | Gate 2 step 3: check the installed copy's currency once a session spans several cycles |
| Archiving a card on the human's word alone that it merged | Verify with a real command (`gh pr view`/`git log`) first — see Gate 4 |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "This one's simple, I'll skip the loop" | Simple tasks hide assumptions; the loop is cheap, rework isn't |
| "More planning can't hurt — I'll size it up to be safe" | It can and does: planning spends the same budget the implementation needs. Over-tiering is how a pass ends with six polished cards and zero working code — size to the work, then spend what's left building |
| "The project folder is overhead" | It's the memory that makes resume instant; skipping it loses the thread |
| "The architecture is obvious, no council needed" | Lite costs one card line and records what was checked; skipping it is how scale, ownership and consistency assumptions go unexamined |
| "I'll just fix it directly" | Undiagnosed fixes multiply bugs; Scope or `zeno-debug` first |
| "One more file won't hurt" | Ceremony is fixed at five card types — a sixth kind of file is exactly the sprawl this avoids |
| "This domain probably doesn't have a specialist" | Check `agents/REGISTRY.md` before assuming — most domain work has a row |
| "I'll just merge it myself, it's obviously fine" | The human is the sole **integration** authority — merging, pushing to trunk, opening a PR — no exceptions, however obvious it looks |
| "I shouldn't commit without asking either" | That rule is about integration, not `git commit`. Work left uncommitted has no rollback points and vanishes with the session — commit each logical change on the working branch as you go |
| "I'll create the branch once I'm ready to commit" | Three past incidents (Obs 34/38/41) show this always slips past a full Execution pass — check the branch as Gate 2's first action, not before commit |
| "I already know this skill, no need to recheck it" | A long session can outlive the copy it loaded — Gate 2 step 3 exists for exactly the session that's run long enough to make that assumption wrong |

## Red flags — stop, you're bypassing the loop

- You're editing product code and there's no Scope captured for this task.
- You're writing "Approach" text and no council line or question round is on the card.
- You've written down Full-council evidence (new integration, data store, sensitive data, boundary, NFR) and are designing or coding without having loaded `zeno-council` and resolved its blocking questions.
- There's no `.zeno/project.md` at the repo root and you're past the first change.
- You're about to spawn an agent outside `agents/REGISTRY.md`, or create a file outside the five
  defined card types.
- Two or more items are outside Backlog/Closed on the Kanban board at once.
- **You're writing product code without the matching `code-standards` leaf loaded** — clean code
  is a gated property of Execution, not an aspiration; load the leaf *before* the code, and run
  its own pre-flight checklist before handing the work to Review.
- You're about to write a Feature or Epic card and can't name the two-plus independently
  verifiable Stories it decomposes into — that's Story-tier work wearing a Feature's card.
- You're about to present the merge/PR/keep menu and `git status` isn't clean — the work you're
  asking about isn't committed yet.
- You're about to say "done" without a fresh Proof entry.
- You're about to say "done" on a diff in a registry-covered domain without an independent pass.
- You're about to say "done" on a code change whose lint/format/typecheck gates never ran.
- You're about to write Scope/card content or edit a product file and haven't run `git branch --show-current` this gate.
- A session has spanned several Feature/Story cycles and you haven't rechecked the installed skill copy for drift.

## Pre-flight checklist — run before delivering any zeno cycle

- [ ] `zeno-council` ran first at Scope (Lite line or Full rounds logged on the card), then Scope captured via `zeno-insight` (Problem / Approach / Done) before any code, on the right card.
- [ ] Gate 2 step 1 ran first: `git branch --show-current` + `git status --short` checked before any Scope/card content or file edit; branched off trunk if needed.
- [ ] Gate 2 step 2 ran: `project.md` reconciled against `git log`/the working tree this gate, not assumed current from an earlier read.
- [ ] Gate 2 step 3 ran, if the session has spanned multiple cycles: installed skill copy checked for drift.
- [ ] `./.zeno/project.md` exists at the repo root; Goal + State + Next step filled.
- [ ] The task was sized correctly (trivial / ad hoc Story / Feature+Story-list / Epic) — smallest tier that fits, climbed only on named evidence, with the chosen tier and its one-line evidence recorded on the card; and a Story too big for one sitting was broken into its own Task list (and a Task list into SubTasks, if still too big).
- [ ] Gate 1 ran DDD for Feature-tier work (and enumerated Features for Epic-tier work); Gate 2 ran FDD + ATDD + BDD + Task breakdown for every Story before Gate 3 began, each Story's Task list ending in a documentation Task; Gate 3 looped TDD over every Task in order; bugs diagnosed via `zeno-debug`; commits atomic and actually made on the working branch (a clean `git status` at Review — committing is the agent's duty, only integration is the human's).
- [ ] Product code was written with the matching `code-standards` leaf loaded, and that leaf's own pre-flight checklist was run before Review.
- [ ] The Kanban board never carried more than 1 item outside Backlog/Closed at once.
- [ ] Decisions made this session are appended to the active card's Decisions log.
- [ ] Changes to shared/public surface had their blast radius checked (impact analysis) and recorded.
- [ ] Review ran goal-backward per `zeno-verify`; evidence + Outcome recorded on the card and rolled up to `project.md`; merge left to the human.
- [ ] `project.md`'s State line names the current branch/PR before the merge/PR/keep choice was presented.
- [ ] A `CHANGELOG.md` entry was appended for this delivery, unconditionally.
- [ ] The documentation check ran (always) at the closing item's own scope: each Story's own documentation Task confirmed actually done, and separately, doc-worthy items (API/arch/deps/setup) had system docs reconciled via `documenting-code` / `/docs-drift`. For a closing Feature/Epic: a missing full documentation set (Architecture & Design / Technical & API Specs / User & Admin Guides) was flagged and an Epic recommended, not backfilled inline or opened unasked.
- [ ] Any specialist invoked came from `agents/REGISTRY.md` — minimum sufficient at Scope, an independent pass at Review where an Advisor-tier match exists.
- [ ] No ad hoc agent spawned outside the registry, no files outside the five card types, no second `.zeno/`-like structure was created.
- [ ] Cards for prior work were archived into `.zeno/docs/archive/` only after merge (and deploy, where the repo has one) was verified with a real command (`gh pr view`/`git log`) — not deleted, not left loose in the active `docs/` folders, not archived on the human's word alone or memory of an earlier action.
