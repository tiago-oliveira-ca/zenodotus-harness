# Borrowing from `grill-me` / `grilling` (mattpocock/skills)

**Source:** [`mattpocock/skills`](https://github.com/mattpocock/skills), MIT-licensed —
`skills/productivity/grill-me/SKILL.md` (user-invoked entry point) and
`skills/productivity/grilling/SKILL.md` (the technique itself; `grill-me` just runs it). Author:
Matt Pocock. Human-facing description: *"Get relentlessly interviewed about a plan or design until
every branch of the design tree is resolved."*

This follows `zeno-insight`'s "Applying external research to the skill library" process: extract
the concrete, falsifiable technique, fit-search the existing library, default to extending over
authoring new. This document is that Scope-stage output — a proposal, not yet an edit.

## 1. What the source actually does

Two skills, one technique:

- **`grill-me`** — the user-invoked front door (`disable-model-invocation: true`). Its entire body
  is one line: *"Run a `/grilling` session."*
- **`grilling`** — the mechanism, model-invocable so it can also fire mid-task, not just on
  request.

The technique itself, distilled to falsifiable rules:

| Element | Rule |
|---|---|
| **Design tree** | Model the plan as decisions, where "every decision branches into the decisions that hang off it." |
| **Frontier** | The set of decisions whose prerequisites are already settled. Only frontier questions get asked *now*; questions blocked on an unsettled prerequisite wait for a later round. |
| **Rounds** | Work proceeds in rounds. Each round, present **all** current-frontier questions together (not one at a time), then wait for answers. |
| **Question format** | `❓ **Q[#]** - **<title>**: <body>` followed by `➡️ <recommended answer>` — every question ships a default the user can accept by saying "yes" instead of composing an answer. |
| **Self-service research** | "Finding facts is your job, never the user's." The agent dispatches sub-agents for anything discoverable in the environment; it never asks the user something it could look up. |
| **Non-blocking exploration** | A running exploration is itself an unsettled prerequisite — only the questions *downstream of that exploration* wait. Everything else in the current frontier is asked immediately, concurrently with the research. |
| **Completion criterion** | Done when the frontier is empty: every branch of the design tree has been visited, nothing left silently assumed. Execution starts only after that. |

## 2. Fit-search: where does this already live in Zeno?

`zeno-insight` is Gate 1 of the loop and already owns exactly this territory — "turn a raw idea
into an agreed design through dialogue BEFORE any code." Relevant overlap, read against
`skills/zeno-insight/SKILL.md`:

| grilling has | zeno-insight already has | Gap |
|---|---|---|
| Design tree / frontier model | Step 2, "ask one question at a time" | zeno-insight's default is stricter (one question, period) than grilling's (all *unblocked* questions per round). No explicit dependency model — "one at a time" doesn't distinguish a question with settled prerequisites from one still blocked on research. |
| Recommended-answer format | Step 5, "propose 2-3 approaches... leading with your recommendation" — but only at the *approach* level | Not applied to individual clarifying questions in step 2. Right now a clarifying question in zeno-insight is open-ended; grilling's `➡️` line makes every question fast-acceptable. |
| "Finding facts is your job, never the user's" | Implicit in the loop's general subagent conventions (`agents/REGISTRY.md`, `Explore`) | Not stated as an explicit rule *inside* zeno-insight's gate — nothing currently stops an agent from asking the user something a codebase read or a research subagent could answer instead. |
| Non-blocking exploration | Not present | zeno-insight has no guidance on running research subagents in the background *while* continuing to ask other unblocked questions. Today's implicit pattern is closer to serial: explore, then ask. |
| Explicit "frontier empty" completion criterion | Scope-exit check: "is every open decision resolved or explicitly deferred?" | Close in spirit, but not tied to a dependency structure — nothing currently forces *visiting every branch*, only accounting for decisions that came up in the dialogue. A decision that was never surfaced (because its prerequisite branch was never opened) can still slip through today. |

Conclusion: **no new skill is warranted.** This is a sharpening of `zeno-insight`'s existing
Scope-gate steps 2 and the Scope-exit check, not a new lane. Per `CLAUDE.md`'s precedence rules
and `_skill-template.md` §1, a new top-level skill is only justified when the domain fits no
existing dispatcher/leaf — here it fits `zeno-insight` exactly. Also checked against the "3 flat
method skills" pattern (`zeno-insight`, `zeno-debug`, `zeno-verify`): grilling is a *design*
technique, squarely `zeno-insight`'s lane, not a 4th sibling.

Not in scope from the source repo: `handoff`, `teach`, `to-questionnaire`, `wait-what`,
`writing-for-agents` (other `productivity/` skills in the same repo) — none were part of this
request and each would need its own fit-search if wanted later.

## 3. Proposed insertion (sketch, not yet applied)

Scoped to the smallest change that preserves `zeno-insight`'s documented shape (leaf body order,
one-line citation, no vendored-attribution apparatus):

1. **Step 2 rewrite** — replace "ask one question at a time" with a frontier-round model:
   - Build the decision/design tree implicitly as questions surface; track which are blocked on an
     unsettled prerequisite (including a still-running research subagent) vs. unblocked.
   - Each round, present **every currently-unblocked question together**, each in the
     `❓ Q# - title: body` / `➡️ recommended answer` format, so the user can accept defaults in
     bulk instead of round-tripping on each one.
   - This is a genuine behavior change from today's strict one-at-a-time — call it out to the user
     as a deliberate trade (fewer round-trips, denser messages) rather than adopt it silently.
2. **New rule, adjacent to step 4 (specialist selection)** — "Facts are your job, not the user's":
   before asking the user anything answerable by reading the repo or dispatching a research
   subagent (`Explore`, or a specialist from `agents/REGISTRY.md`), do that first. Explicitly
   permit dispatching that research **non-blockingly** — continue the current round's other
   unblocked questions while it runs; only the questions that depend on its answer wait for the
   next round.
3. **Scope-exit check, tightened** — reframe "is every open decision resolved or explicitly
   deferred?" as "is the frontier empty — has every branch of the design tree been visited?" so a
   branch that was never opened (not just a decision that was raised and dropped) is caught.
4. **Anti-pattern table / rationalization table** — add rows:
   - Anti-pattern: "Asking the user a question you could answer by reading the code or dispatching
     research" → Instead: "Self-service research first; ask only what the environment can't tell you."
   - Rationalization: "I'll just ask instead of checking the code, it's faster" → Reality-check:
     "Finding facts is your job, never the user's — a wrong guess costs a round-trip either way."
5. One-line citation next to the rewritten step 2, per the existing convention (no multi-paragraph
   attribution block): pointer to `grilling` technique, mattpocock/skills, MIT.

## 4. Open question for the user

Adopting the frontier/round model changes an existing, load-bearing rule (strict "one question at
a time") rather than purely adding to it. Two ways to land it:

- **Replace** step 2 outright with the frontier-round model (recommended — the round model
  subsumes single-question mode as the degenerate case where the frontier has one item).
- **Branch** on request size: keep strict one-at-a-time for small Story-tier scopes, switch to
  frontier-rounds only for Feature/Epic-tier scopes where the design tree is wide enough to matter.

## 5. Next step, if approved

Per `zeno-insight`'s own gate: this becomes a small Feature card (single-skill edit, no new
file) — Problem / Approach / Done-looks-like on `.zeno/docs/features/FEAT-<slug>.md` — before
touching `skills/zeno-insight/SKILL.md`. Not created yet; this document is the Scope research, the
card capture is a separate, explicit step.

## 6. What actually shipped (postscript)

Delivered as ad hoc `STORY-gate1-frontier-questioning` (Story-tier, not Feature — the sizing ladder
in `zeno/SKILL.md` puts a single-file, one-pass edit at Story), taking the "Replace" option from
§4. After the first close, direction changed from "port the technique" to "use it as a base and
make it genuinely better while staying identifiably Zenodotus" — the shipped version keeps the
frontier/rounds/`❓`/`➡️` mechanic from this proposal but adds four capabilities the source
structurally cannot have (no backlog, no specialist registry, no impact-analysis concept):
card-persisted per-round Decisions-log writes, registry-first research ordering, treating
shared-surface questions as impact-analysis lookups, and frontier-width as a card-tier sizing
signal. The Story card (STORY-gate1-frontier-questioning) predates the archive-on-merge policy and was
pruned on close — PR #19 and `CHANGELOG.md` are its durable record.
