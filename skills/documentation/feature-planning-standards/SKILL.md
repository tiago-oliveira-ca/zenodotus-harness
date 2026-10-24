---
name: feature-planning-standards
description: >
  Standards for writing a Feature List & Development Plan — naming and sizing features,
  structuring a feature-list table, building the development plan around it, prioritizing with
  MoSCoW/RICE/Kano/Value-vs-Effort, and keeping a Roadmap distinct from a Release Plan. Use when
  creating or reviewing a feature list, a product roadmap, a release plan, or when deciding what
  ships in what order. Trigger on: "feature list", "write a roadmap", "release plan", "prioritize
  these features", "MoSCoW", "RICE score", "Kano model", "value vs effort", "feature backlog",
  "development plan", "what order should we build these", "is this ready to prioritize".
---

# Feature Planning Standards

Use this skill when a set of features needs to be named, sized, recorded, prioritized, and
sequenced into a plan — the stage between a PRD's prioritized feature list and the Epics/Stories
that `development-planning-standards` breaks each feature into. A feature list with no development
plan is just a wishlist; a development plan with no feature list has no "why" underneath its
"when."

## Core Boundaries

- **Feature**: a small, client-valued function a user or stakeholder would recognize as
  meaningful and useful on its own — an outcome, not an implementation step.
- **Feature List**: a structured catalogue of features with priority, effort, dependencies, and
  ownership. Answers "what are we building, and why does it matter?"
- **Development Plan**: the schedule, methodology, and resourcing that turns the list into
  delivered work. Answers "when, how, and by whom?"
- Every feature carries a **stable ID** that threads through both halves — that's what makes this
  one coherent artifact instead of two disconnected lists.
- This skill sits **above** `development-planning-standards`: a Feature here typically becomes one
  or more Epics/Stories there once it's ready to build. Don't duplicate Epic/Story/Task structure
  or Definition of Ready/Done — see that skill for development-level breakdown.

## Feature Naming and Granularity

- **Naming template**: `<action> the <result> for/of/to a(n) <object>` — e.g. "Calculate the total
  of a sale," "Validate the password of a user." This forces features to be written as outcomes,
  not implementation steps ("Calculate the total of a sale," not "Add a `sum()` function to the
  cart module").
- **Granularity rule**: a feature should take no more than ~2 weeks; most good features are 1-3
  days. Split anything bigger — oversized features are the single most common reason estimates and
  timelines fall apart downstream.
- **Hierarchy**: group features in three tiers — **Subject Area** (e.g. "Account Management") →
  **Feature Set** (e.g. "Authenticating a user") → **Feature** (e.g. "Validate the password of a
  user"). This is what lets a list scale from 10 items to 500 without becoming unreadable, and it
  maps onto a "theme → epic → feature" structure in modern PM tooling.

## Feature List Table

Each feature gets a consistent set of fields:

| Field | What it captures |
|---|---|
| ID / Name | Stable identifier + outcome-oriented name |
| Description | What it does and the benefit it delivers |
| User story | "As a [persona], I want [goal], so that [benefit]" |
| Acceptance criteria | Testable Given/When/Then conditions for "done" |
| Priority | MoSCoW category or a numeric score (see Prioritization below) |
| Effort estimate | Story points, T-shirt size, or person-days |
| Dependencies | Other features/systems this relies on |
| Owner | Who is accountable |
| Status | Not started / In design / In build / Done |
| Target release | Which phase/sprint/version it ships in |
| Success metric | The measurable outcome that proves it worked |

Acceptance criteria and success metric are the two fields teams most often write badly:
- **Acceptance criteria** must be specific and measurable ("page loads within 2 seconds"), not
  vague ("loads quickly"), and must not just restate the user story in different words.
- **Success metric** guards against shipping features nobody uses — feature-adoption data across
  many products has repeatedly found the large majority of shipped features are rarely or never
  used. A feature with no success metric is a feature nobody will notice if it fails.

## Development Plan Structure

1. Scope & objectives, tied to real business goals
2. Methodology (Agile/Scrum, Kanban, Waterfall, or a hybrid) and why
3. Team & roles, including QA and any external groups
4. Work breakdown — features decomposed into phases → sprints → tasks
5. Timeline & milestones — realistic, phase-by-phase; reserve milestones for genuinely major
   events (a release, a demo), not every task
6. Resourcing — people, budget, tooling
7. Technical approach — architecture, integration points, non-functional requirements (bring in
   from the start, not as a late afterthought)
8. Risks & mitigations
9. Dependencies
10. QA / testing & release strategy

### Roadmap vs. Release Plan

These get conflated constantly — keeping them separate is one of the most valuable disciplines
here:

- **Roadmap** — strategic and loose: themes, goals, rough timeframes ("Q2"). Readable by an
  executive in 30 seconds.
- **Release Plan** — tactical and specific: named features in named sprints with expected ship
  dates. This — or the feature list itself — is where granular detail lives.

**Rule of thumb: keep feature-level detail out of the roadmap.**

## Prioritization

Four frameworks cover almost every situation:

| Framework | What it does | Best when |
|---|---|---|
| MoSCoW (Must/Should/Could/Won't) | Buckets features into four priority tiers | Managing stakeholder expectations, defining release scope quickly |
| RICE (Reach × Impact × Confidence ÷ Effort) | One comparable numeric score per feature | You have or can estimate usage data and a shared goal metric |
| Kano Model | Classifies as Basic / Performance / Delighter by user satisfaction | You can survey users and want to balance "must exist" against "wow factor" |
| Value vs. Effort (2×2) | Plots value against effort to spot quick wins | You need a fast first pass with minimal data |

**MoSCoW only works if the buckets are honest.** Cap "Must-have" at roughly **60% of total
effort** — if 80-90% of the list is "Must-have," nothing has actually been prioritized. Frameworks
layer: score everything with RICE, then sanity-check the top items against a Value/Effort plot.

## Traceability

- **Shared front matter** — one set of goals, personas, and success metrics governs both the
  feature list and the development plan, so nothing in the plan contradicts the list's "why."
- **Stable IDs** — every feature keeps the same ID from the list, through the plan, into whatever
  ticketing system executes the work (Epics/Stories in `development-planning-standards`).
- **Two-way linkage** — a feature's status is visible from both directions: the plan shows which
  features are in this sprint; the feature list shows which sprint/release each feature belongs to.
- For audit-grade rigor (regulated or high-stakes work), add a Requirements Traceability Matrix —
  this is a **different RTM** than `testing/software-test-specification`'s requirement↔test-case
  matrix; don't conflate the two. This skill's RTM maps requirement → feature → status; the testing
  skill's maps requirement → test case → execution result. Cross-reference both when a feature
  needs full requirement-to-test traceability.

Without shared IDs and two-way linkage, teams end up maintaining "truth" in two places that
quietly drift apart — a roadmap that looks fine while the sprint board tells a different story.

## Writing Rules

- Name every feature as an outcome (`<action> the <result> for a(n) <object>`), never an
  implementation step.
- Enforce the ~2-week / 1-3-day granularity rule at write time, not after estimation reveals the
  problem.
- Every feature needs a success metric before it's considered ready to prioritize — "shipped" is
  not the same as "valuable."
- Keep the roadmap thematic; keep feature-level detail in the release plan or feature list.
- A feature list/plan is a living artifact — assign an owner and a review cadence (each sprint or
  release), or it goes stale and erodes trust.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Dumping the full feature list into the roadmap | Roadmap = strategy; feature list = detail — keep the levels separate |
| Marking almost everything "Must-have" | Enforce the ~60% Must-have cap; prioritization is a forcing function |
| Acceptance criteria that just restate the user story | Write specific, measurable, testable conditions |
| Features listed with no success metric | Outcomes matter more than outputs — attach a metric before calling it ready |
| Letting the document go stale after sign-off | Assign an owner and a recurring review cadence |
| One person writing the whole document alone | Feature lists/plans need engineering + product + QA input to be realistic |
| Splitting "truth" across multiple tools with no shared ID | Traceability requires stable IDs and two-way linkage |
| Ignoring non-functional requirements until late | Bring them into the development plan from the start |
| Naming a feature as an implementation step | Use the outcome-oriented naming template |

## Review Workflow

1. Confirm every feature is named as an outcome and sized within the granularity rule.
2. Confirm every feature has acceptance criteria, a success metric, and a stable ID.
3. Check that "Must-have" doesn't exceed roughly 60% of total effort.
4. Confirm the roadmap stays thematic and doesn't leak feature-level detail.
5. Confirm the development plan's ten components are all present, not just timeline and tasks.
6. Confirm traceability: every feature's ID is unchanged from list to plan to (if applicable) RTM.

## Pre-flight checklist — run before delivering any feature list or development plan

- [ ] Every feature is named as an outcome and sized to ~1-3 days (never more than ~2 weeks).
- [ ] Every feature has a stable ID, acceptance criteria, and a success metric.
- [ ] Priority was assigned via a named framework (MoSCoW/RICE/Kano/Value-vs-Effort), not by feel.
- [ ] "Must-have" doesn't dominate the list (~60% effort cap respected).
- [ ] The Roadmap stays thematic; feature-level detail lives in the Release Plan or feature list.
- [ ] The Development Plan covers all ten components, including risks and NFRs, not just tasks.
- [ ] An owner and review cadence are assigned so the document doesn't go stale.
