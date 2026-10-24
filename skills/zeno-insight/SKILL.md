---
name: zeno-insight
description: >
  The design gate of the zeno loop's Scope, after zeno-council. Turn a raw idea into an agreed design
  through dialogue BEFORE any code: explore context, ask the current frontier of clarifying
  questions one round at a time, propose 2-3 approaches with a recommendation, present the design
  with approval checkpoints, get explicit sign-off. Decompose bundled requests; hand genuinely
  large work to zeno-workflow's zeno-ddd +
  zeno-fdd. No implementation until the design is captured on the right .zeno/ card. Trigger
  on: "brainstorm", "let's design", "how should I approach", "what's the design", "help me
  scope", "before we code", "think through this", "Scope this", "design first", "weigh the
  options", "what are the trade-offs".
---

# Zeno Insight — design before code

This is Gate 1 of the zeno loop. Its job is to convert a rough idea into a design both you and the
user agree on, **before** a line of implementation exists. Skipping it is how hidden assumptions
become expensive rework.

**Iron Law: NO CODE UNTIL THE DESIGN IS APPROVED.** The gate closes only when the user has signed
off on the design and it is captured on the right card under `.zeno/docs/`. "Obviously simple"
does not exempt a task — simple tasks are where unstated assumptions hide.

## The gate (do these in order)

0. **The council has already run.** `zeno-council` opens Scope before this gate. Read the active
   card's Decisions log first: the council's Lite line or Full rounds (questions, answers, classified
   facts and assumptions) are the architecture backlog. Do not restate its phases or re-ask its
   questions; steps 2 and 5 below pick up where it leaves off.
1. **Explore the context first.** In an existing repo, read the relevant code and learn its patterns
   before proposing anything — prefer codemaps / `graphify query` to map the affected area over blind
   file-reading when they're available (`zeno/references/impact-analysis.md`). Never design in a
   vacuum when a codebase exists.
2. **Ask the current frontier, one round at a time — and persist it.** Track clarifying questions
   as a design tree — every decision branches into the decisions that hang off it. A question is
   *frontier* once its prerequisites are settled; a question still blocked on an unsettled
   prerequisite (including a still-running exploration) waits for a later round — it is not asked
   early, and it does not hold up the rest of the current round. Each round, present every frontier
   question together (most rounds surface one; a wide tree surfaces several), each formatted as
   `❓ Q<#> - <title>: <body>` with a `➡️ <recommended answer>` line, so the user can accept the
   default instead of composing an answer. Prefer concrete choices over open prompts. As each round
   closes, append its questions and resolutions to the active card's Decisions log immediately —
   not batched until gate-exit — so the tree's state survives a compaction or a session break
   mid-gate; the card, not the conversation, is the durable copy of the tree.

   *Example round* (illustrative — the real questions and defaults depend on the task at hand, not
   this shape):
   > ❓ Q1 - Storage backend: Should sessions persist to disk or stay in-memory?
   > ➡️ Disk-backed — survives restarts, and fits the existing `.zeno/` card-persistence pattern.
   >
   > ❓ Q2 - Auth scope: Should this endpoint require auth, or is it public?
   > ➡️ Require auth — matches every other write endpoint in this service.

   **A long frontier is sizing evidence, not just something to push through.** If a single card's
   frontier is still running past roughly 4-5 rounds, that round count is itself a signal to
   revisit step 3 — the request may belong at Feature tier, not the ad hoc Story it was sized as —
   rather than something to keep grinding through round by round. Within a round, a low-stakes or
   cosmetic branch doesn't need full round ceremony either: resolve it with the recommended default
   noted inline and move on, reserving full rounds for branches whose answer actually changes the
   design.
   **Finding facts is your job, never the user's:** before asking anything the environment could
   answer, look it up, in this order — a repo read; then, if the domain has one, the matching
   specialist from **`agents/REGISTRY.md`** (the same table step 4 draws from — check it here too,
   not only at specialist-selection time); a running exploration (`Explore` or otherwise) for
   anything with no registry match; and when the frontier question concerns shared/public surface,
   that self-service research **is** the impact-analysis pass (`zeno/references/impact-analysis.md`),
   not a separate later step. Dispatch this non-blockingly and keep asking the round's other
   unblocked questions while it runs; only the questions downstream of that research wait for the
   next round. *(Frontier/rounds core idea adapted from `grill-me`/`grilling`, mattpocock/skills,
   MIT; card-persisted tree, registry-first research, and impact-analysis wiring are zeno-native —
   grill-me has no backlog to persist a tree to.)*
3. **Check the scope, and size the card.** If the request bundles several independent subsystems,
   stop and split it into separate efforts. A root frontier that already spans several independent,
   unrelated branches (step 2) is itself sizing evidence, not just a subsystem count — treat it as a
   signal toward Feature/Epic tier even when the request reads as one sentence. **The signal runs
   both ways, and the default is down:** a frontier that closes in a round or two, over a blast
   radius of one or two files, is evidence the work is Story-tier — stay there, and don't let a
   formally-worded request ("run your full process, all the gates") climb the ladder on tone alone.
   Escalating costs the budget the implementation needs; per `zeno`'s ladder, a Feature card
   requires naming the two-plus independently-verifiable Stories it holds, and the chosen tier
   plus its evidence gets recorded on the card. Then pick the right
   card tier: a small, single-behavior change gets an ad hoc Story (no Epic/Feature file at all);
   one coherent effort too big for a single Execution pass gets a Feature card, and hands off to
   **`zeno-workflow`**'s `zeno-ddd` then `zeno-fdd` stages to decompose it into a Story list;
   genuinely epic-sized work spanning multiple Features gets an Epic card first.
   Don't try to design it all at once.
4. **Identify domains, select specialists.** (A distinct `agents/REGISTRY.md` lookup from step 2's
   research check — step 2 uses the registry to find facts you'd otherwise have to ask the user;
   this step uses it to select who implements.) Name the technology/practice domain(s) the work
   actually touches, look them up in `agents/REGISTRY.md`, and select the **minimum sufficient**
   specialist(s) — not every agent whose domain is tangentially related. This is bounded,
   table-driven selection (the registry's sanctioned mechanism), distinct from spawning an ad hoc
   agent outside it. A one-file bugfix may need none; a cross-cutting change may need two or three.
   Record the selection on the card alongside the Scope lines so Execution and Review know who to
   consult without re-deriving it.
5. **Propose 2-3 approaches.** For anything non-obvious, lay out options with trade-offs, leading with
   your recommendation and why. One option is not a choice. Architecture-level choices (boundaries,
   data ownership, deployment, integration style) come from the council's Full recommendation on the
   card — present it, don't re-derive it; options here cover the code-level approach.
6. **Present the design in sections, with checkpoints.** Walk through architecture, components, data
   flow, error handling, and testing — one section at a time, each scaled to its complexity — pausing
   for agreement after each.
7. **Get explicit sign-off, then capture Scope.** Do not slide from design into code. When the user
   approves, distill it to the three Scope lines — Problem / Approach / Done looks like — on the
   Epic or Feature card sized in step 3 (`docs/epics/EPIC-<slug>.md` or
   `docs/features/FEAT-<slug>.md`, from `zeno/references/epic-template.md` /
   `zeno/references/feature-template.md`), and hand to Execution (or `zeno-workflow`'s `zeno-ddd`/`zeno-fdd` first, for multi-step work).

## Applying external research to the skill library

When the "raw idea" is an external source — a paper, spec, or RFC — rather than a feature
request, step 1 ("explore the context") means two things, not one: read the source and extract
the concrete, falsifiable technique (not a paraphrase), *and* run a fit-search across the
existing skill library for where it applies — `zeno-stack/zeno-find-skills` locally,
`zeno-stack/zeno-skill-scout` for external prior art — before drafting anything new. Default to
extending an existing skill's content over authoring a new one, the same overlap-check already
required before creating a skill (`_skill-template.md`). Scope each resulting edit to the
smallest insertion that preserves the target skill's documented shape (leaf body order, one-line
citation, no vendored-attribution apparatus), and cite the source in that one line.

## Scope-exit check (before leaving this gate)

- **Does the approach actually reach the goal?** Walk the design against "Done looks like" — if a
  deliverable has no path in the design, the design is incomplete.
- **Is the frontier empty, and is it on the card?** Every branch of the design tree must be
  visited — not just the decisions that happened to come up — and each one must already be in the
  card's Decisions log (written per round, per step 2 — this check should find nothing left to
  transcribe) with an outcome, a `[deferred]` marker, or an explicit "at Claude's discretion." A
  branch never opened is as costly as a decision silently dropped; a decision only in the
  conversation and not yet on the card is functionally still open.

## Design philosophy

- **Isolation and clarity.** Prefer small, single-purpose units with clear interfaces. A component
  you can't describe in a sentence is too big.
- **Fit the existing grain.** Adopt the codebase's conventions; fold in only improvements that serve
  *this* goal. Insight is not a licence for unrelated refactoring.
- **Right-size the ceremony.** A small change gets a one-paragraph design; a big one gets `zeno-workflow`'s `zeno-ddd`/`zeno-fdd`.
  The gate always runs; its output scales to the task.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Proposing a design without reading the existing code | Explore the repo and its patterns first |
| Re-asking a question the council already logged, or re-deriving its architecture options | Read the card's Decisions log first; ask only the remaining non-architectural frontier |
| Dumping every question in the design tree at once | Ask only the current frontier — later branches wait for their round |
| Asking the user something the repo or a research subagent could answer | Self-service research first, dispatched non-blockingly — ask only what the environment can't tell you |
| Treating impact analysis as a separate step from frontier research | A frontier question on shared/public surface *is* an impact-analysis lookup — run it as the self-service research |
| Keeping the frontier only in conversation memory | Log each round's questions + resolutions to the card as it closes, not batched until gate-exit |
| Presenting a single approach as the plan | Offer 2-3 options with trade-offs + a recommendation |
| One giant design wall, take-it-or-leave-it | Section-by-section, approval checkpoint on each |
| Designing several subsystems at once | Decompose; hand large single efforts to `zeno-workflow`'s `zeno-ddd`/`zeno-fdd` |
| Sliding from design into writing code | Stop at approved design; capture Scope, then Execution |
| Dropping a decision raised in the dialogue | Every decision → Decisions log (resolved or `[deferred]`) |
| Invoking every agent whose domain sounds relevant | Select the minimum sufficient specialist(s) from `agents/REGISTRY.md` |
| Grinding through 6+ rounds on a Story-tier card | A long frontier is sizing evidence — revisit step 3, consider Feature tier |
| Opening a Feature/Epic card after a 1-2 round frontier over one or two files | The signal runs both ways — a short frontier is evidence the work is Story-tier; size down, name the tier's evidence on the card |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "This is too simple to need a design" | Simple tasks hide the assumptions; a one-paragraph design still closes the gate |
| "I'll design as I code, it's faster" | Design-as-you-code is how scope creeps and rework lands; sign off first |
| "The user clearly wants me to just start" | Approval is one message; a wrong build is an afternoon |
| "I'll remember that open question" | Unwritten decisions vanish on compaction; log it |
| "I don't need to check the registry, I know which agent fits" | Check `agents/REGISTRY.md` anyway — it's the record of what's minimum-sufficient, not a formality |
| "This paper's finding needs a new skill" | Fit-search existing skills first; extend one over authoring a new skill by default |
| "I'll just ask instead of checking the code, it's faster" | Finding facts is your job, never the user's — a wrong guess costs a round-trip either way |
| "I'll ask everything in the tree now so I don't forget" | Later branches are blocked on unsettled prerequisites; asking early just produces guesses — wait for their round |
| "I'll write the whole tree to the card at the end" | A round can end mid-compaction; log each round as it closes, not only at gate-exit |
| "I already checked the registry at step 4, no need to re-check for research" | Step 4 selects who *implements*; step 2's research check is separate and comes first, per question |
| "I'm almost through the tree, no need to re-size now" | Round count past ~4-5 is itself the signal step 3 asks you to watch for — re-check tier, don't just push through |

## Red flags — stop before you leave Scope

- You're reaching for the editor before the design is approved.
- You've asked zero clarifying questions on a non-trivial request.
- A "Done looks like" deliverable has no home in your design.
- A decision came up in the dialogue and isn't written down.
- You've moved to proposing approaches without naming the domain(s) touched or checking `agents/REGISTRY.md`.
- You're asking a question the codebase or a dispatched subagent could answer instead.
- You're about to ask a question whose prerequisite is still an unsettled, unopened branch.
- A round just closed and its questions/resolutions aren't on the card yet.
- A frontier question touches shared/public surface and you haven't run impact analysis on it.

## Pre-flight checklist — run before delivering any insight session

- [ ] `zeno-council` ran first (Lite line or Full rounds on the card) and its log was read before any question was asked.
- [ ] Existing code/context explored before any approach was proposed.
- [ ] Clarifying questions asked by frontier round — never the whole tree at once, never blocked on an unsettled prerequisite — focused on purpose / constraints / success.
- [ ] No question asked that self-service research (repo read, `agents/REGISTRY.md` specialist, or a dispatched exploration) could have answered instead; shared/public-surface questions had impact analysis run as that research.
- [ ] Each round's questions and resolutions were appended to the card's Decisions log as the round closed, not held until gate-exit.
- [ ] Multi-subsystem requests decomposed; large single efforts handed to `zeno-workflow`'s `zeno-ddd`/`zeno-fdd`.
- [ ] Domains identified and the minimum sufficient specialist(s) selected from `agents/REGISTRY.md` (or none, if the work needs none).
- [ ] 2-3 approaches offered with trade-offs and a clear recommendation.
- [ ] Design presented in sections, each approved; explicit sign-off obtained before code.
- [ ] Approach checked against the goal; the frontier is empty — every branch visited, each resolved or `[deferred]` in the log.
- [ ] Card tier sized correctly (ad hoc Story / Feature / Epic) before Scope was written.
- [ ] Approved design distilled to Problem / Approach / Done looks like on the sized card.
