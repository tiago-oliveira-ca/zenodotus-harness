# Software Development Documentation Lifecycle

## Overview

A mature software delivery process moves from business intent to requirements,
architecture, implementation, testing, and operations. Each stage produces a specific
artifact type, owned by a specific role, that traces back to the business goal that
justified the work. This reference is the canonical process description for the
`documentation` dispatcher — load it whenever a task spans multiple document types, needs
the full sequence, or needs the governance/traceability model.

## Lifecycle

```
BRD
 |
 v
PRD
 |
 v
FRD (FSD) + NFR
 |
 v
TRD / SRS  (optional — consolidates FRD+NFR into one verification-ready document)
 |
 v
SAB
 |
 v
SAD
 |
 +--> ADRs (continuous)
 |
 v
Feature Planning (Feature List + Development Plan)
 |
 v
Development Planning (Epics + Stories + Tasks)
 |
 v
Implementation
 |
 v
Code Review
 |
 v
Testing
 |
 v
Deployment
 |
 v
Operations
 |
 +----------------+
                  |
                  v
         Design Improvements  (feeds back into BRD/PRD/SAB/SAD)
```

Architecture defines **intent** (SAB/SAD/ADR). Development planning turns intent into
actionable work (Epics/Stories/Tasks). Implementation proves the intent is buildable. Code
review checks the implementation against both the requirement and the architecture. Testing
proves quality. Operations feedback closes the loop back into design — a mature process
does not treat Operations as the last stage, it treats it as the input to the next BRD/PRD/SAD
revision.

## Stage Reference

| Stage | Purpose | Owner | Key Question | Skill in this repo |
|---|---|---|---|---|
| BRD | Define why the initiative exists | Business / Product Owner | Why are we building this? | `business-requirements-standards` |
| PRD | Define what the product should deliver | Product Owner | What should the product do? | `product-requirements-standards` |
| FRD / FSD | Define detailed system behavior | Product / BA | How should the system behave? | `functional-specification-standards` |
| NFR | Define quality attributes | Architect / Engineering | How well must it perform? | `non-functional-requirements-standards` |
| TRD / SRS | Optional: consolidate FRD+NFR into one technically precise, verification-ready document with traceability IDs | Engineering / Architect | Is every requirement specific enough to build and test against? | `technical-requirements-standards` |
| SAB | Provide a high-level architecture view | Solution Architect | What is the proposed solution? | `solution-architecture-standards` (blueprint tier) |
| SAD | Define the detailed technical architecture | Solution Architect | How will the solution be built? | `solution-architecture-standards` (formal tier) |
| ADR | Record a significant technical decision (continuous, alongside SAB/SAD/implementation) | Solution Architect / Tech Lead | Why was this decision made? | `architecture-documentation-and-decision-records` |
| Feature Planning | Name, size, and prioritize features into a Feature List and Development Plan | Product Owner | What are we building, and in what order? | `feature-planning-standards` |
| Development Planning | Break architecture components into Epics, Stories, and Tasks | Product Owner / Tech Lead | What work proves this component is done? | `development-planning-standards` |
| Implementation | Build the system per FRD/NFR/SAD | Engineering | Does the code match the design? | `code-standards` (routes by language/framework) |
| Code Review | Validate the implementation against requirement, architecture, and standards | Engineering (peer review) | Does this honor the requirement and the architecture? | `code-standards` (standards) + `/code-review` (review process) |
| Testing | Verify behavior and quality attributes | QA / Engineering | Does it work and hold up under load? | `testing` (routes to test specification standards) |
| Deployment | Ship the verified system | DevOps / Platform | How does this reach production safely? | `github-circleci-standards` (CircleCI) / `zeno-stack/zeno-deployment-patterns` (GitHub Actions, strategy, rollback) |
| Operations | Run and support the system in production, and feed learnings back into design | SRE / Support | Is it healthy, and what should the next design revision fix? | `operations-standards` |

Any document review or rewrite request, regardless of stage, routes to
`document-writer-reviewer`.

## ADR Template

ADRs use the template and lifecycle rules owned by
`../architecture-documentation-and-decision-records/SKILL.md` — load that skill when writing
or reviewing an ADR rather than duplicating its template here. In brief, every ADR states the
decision, the context that forced it, the options considered, the consequences, and a status
(`Proposed / Accepted / Rejected / Superseded / Deprecated`).

## Design → Development Breakdown

Architecture documents do not implement themselves — each design component should become
actionable development work before implementation starts. Break it down explicitly rather
than letting engineers reverse-engineer scope from a SAD:

```
Design Component (from SAD)
      |
      v
Epic  (one per component/capability)
      |
      v
Stories  (one per user-facing or system behavior)
      |
      v
Tasks  (concrete implementation steps)
```

Example:

```
Design Component: Order Processing Service
  Responsibilities: receive orders, validate payload, publish events, persist status

Epic: Order Processing Service

Stories:
  1. Create order API endpoint
  2. Implement validation rules
  3. Publish order-created event
  4. Persist order status

Tasks (under Story 3):
  - Create database migration
  - Implement Kafka producer
  - Add unit tests
```

A Story should be traceable to the FRD/NFR requirement it implements and the SAD component
it belongs to — if a Story can't name both, it's scope that snuck in without a design basis.

For full standards on writing Epics/Stories/Tasks, Definition of Ready/Done, and story
splitting patterns, see `../development-planning-standards/SKILL.md`.

## Agile Ceremonies Connecting Design and Development

These checkpoints are where design and development actually meet. Each has a distinct
question to answer — don't collapse them into one generic "sync":

| Ceremony | When | Reviews | Key Question |
|---|---|---|---|
| Architecture Review | Before development starts | SAD changes, ADRs, technical risks, dependencies | Is the design sound enough to plan against? |
| Sprint Planning | Start of each sprint | Requirements, acceptance criteria, technical tasks, dependencies | What can the team commit to this sprint? |
| Design Review | During implementation | Proposed implementation, technical tradeoffs, risks | Does the chosen approach still match the architecture's intent? |
| Code Review | Per pull request | Requirement alignment, architecture alignment, coding standards, security | Does this change honor the requirement and the design? |

## Change Management

Architecture is a living artifact, not a one-time deliverable. When a significant change is
identified after design has been baselined, follow this loop instead of quietly patching
code around a stale design:

```
Issue Identified
      |
      v
Architecture Review
      |
      v
ADR Created or Updated
      |
      v
SAD Updated
      |
      v
Implementation Changed
```

Skipping straight from "Issue Identified" to "Implementation Changed" is how SADs and ADRs
go stale — the ADR/SAD update is what keeps the traceability model (below) honest.

## Ownership Model

| Artifact | Owner |
|---|---|
| BRD | Business Owner |
| PRD | Product Owner |
| FRD / NFR | Product Owner / Business Analyst |
| SAB | Solution Architect |
| SAD | Solution Architect / Technical Architect |
| ADR | Architect / Engineering Lead |
| Feature List | Product Owner |
| Epics / Stories | Product Owner |
| Tasks / Code | Engineering |
| Tests | QA / Engineering |
| Runbooks | Operations / Engineering |

## Documentation Governance

Every document produced at any stage should carry this metadata:

| Attribute | Example |
|---|---|
| Owner | Solution Architect |
| Version | 1.0 |
| Status | Draft / Approved |
| Last Review Date | YYYY-MM-DD |
| Review Frequency | Annual or major change |

A document must be revised when:

- Architecture changes
- Integrations change
- Requirements change
- Operational procedures change

## Traceability Model

```
Business Goal
      |
      v
Requirement
      |
      v
Architecture Decision
      |
      v
Implementation
      |
      v
Test Case
      |
      v
Operational Metric
      |
      +--> feeds back into the next Business Goal / Requirement / Architecture Decision
```

Every artifact below the BRD should be able to answer "which upstream need does this serve?"
and "which downstream artifact verifies or implements this?" A requirement, decision, or test
that cannot answer both questions is an orphan and should be flagged during review.

The loop does not end at "Operational Metric" — an alert threshold breach, a recurring
incident, or a usage pattern the PRD didn't anticipate is itself a new upstream input. Route
it back through Change Management (above) rather than fixing it silently in code.

### House requirement-ID grammar

`<TYPE>-<NNN>` — `BR` (business requirement, BRD), `PRD` (product capability), `FR`
(functional requirement), `NFR` (quality requirement), `TR` (technical requirement, TRD —
including NFRs folded inline into a TRD). One namespace per project, sequential within each
type, zero-padded to 3 (`BR-003`, `FR-012`, `TR-004`).

- **IDs are immortal:** never renumbered, never reused. A dropped requirement keeps its ID
  with status `Dropped`; a split one is marked `Superseded-by: FR-019, FR-020`. Never use
  positional/dotted sub-IDs (`FR-012.1`) — if a requirement needs children it isn't atomic.
- **Down-links only are written; up-coverage is checked.** Each child artifact declares its
  parents (`Trace: BR-001` on a PRD entry, `Trace: PRD-002` on an FR); "what implements
  BR-003?" is answered by `grep -rn "BR-003"`. Engineering-imposed requirements with no
  business parent are marked `Trace: derived`, never given a fake parent.
- **The bridge to the zeno backlog is one field:** a Feature card carries
  `**Implements:** PRD-NNN`, a Story card `**Implements:** FR-NNN[, NFR-NNN]`, and each BDD
  scenario name is suffixed `[FR-NNN]` — so the story card's Proof section doubles as
  test-level traceability with no separate register.
- **The RTM is generated-or-checked, never trusted:** one markdown table at
  `docs/requirements/rtm.md`, one row per FR/NFR, every hop re-derivable by grep.

```markdown
| ID | Requirement (short) | Trace up | Story | Scenario / test | Status |
|---|---|---|---|---|---|
| FR-004 | Alert fires ≤5 min after matching listing published | PRD-002 ← BR-001 | STORY-alert-dispatch | "New match triggers alert [FR-004]" → tests/alerts/test_dispatch.py | Verified |
```

Orphan check before approval, both directions: every ID below the BRD answers "which
upstream ID?" (else it's scope that snuck in), and every Must-level ID appears in at least
one downstream artifact (zero grep hits downstream = unbuilt promise).

### Proportionality — when to skip or merge layers

A document layer earns separate existence only when it has a **distinct approver or a
distinct decision** from the layer above; otherwise merge it upward as a titled section —
but never merge away the ID grammar, which is what feeds the RTM and the story-card
`Implements:` lines.

| Work size | Doc chain |
|---|---|
| Trivial | None — zeno skips to Review |
| Story-sized | No BRD/PRD/FRD: the story card IS the FRD (ACs + scenarios); `Trace: derived` unless a chain already exists |
| Feature-sized | One feature one-pager at `docs/requirements/<feat-slug>.md`: 3-line business intent (mini-BRD) + PRD-NNN capability list + FR/NFR entries with ACs — layers merged, IDs intact |
| Epic-sized | Standalone PRD with a one-page BRD section at its top; FRD per feature or sectioned |
| External sponsor / compliance / contract | Full chain: standalone BRD (its approver is not the PM), PRD, FRD+NFR, optional TRD |
| Any size, significant technical decision | An ADR, always — orthogonal to which layers were merged |

### Worked Example

```
Requirement:    Orders must be processed within 5 minutes.
Design:         Kafka + Worker Services.
Implementation: Retry mechanism and consumer processing logic.
Testing:        Load test processing time.
Monitoring:     Alert when queue age exceeds threshold.
```

If the monitoring alert fires in production, that's a new Issue Identified — feed it back
through Change Management, not a silent hotfix.
