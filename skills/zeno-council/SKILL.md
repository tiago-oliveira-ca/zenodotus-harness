---
name: zeno-council
description: >
  The Architecture Council that opens the zeno loop's Scope, before zeno-insight. A review board of
  eight inline roles (Chief Architect, Business/Domain, Application, Data, Platform/Cloud, Security,
  SRE, Challenger) that questions first, designs second, challenges the design, compares options and
  documents decisions. Depth scales: Lite (one card line) for work with no architecture impact, Full
  (interview, options, debate, trade-offs, recommendation) when a boundary, data store, integration,
  security posture or NFR is in play. Trigger on: "architecture council", "architecture review",
  "which architecture", "design this system", "system design", "monolith or microservices", "should
  this be a service", "architecture decision", "trade-off analysis", "readiness gate", or any new
  system/component/integration entering Scope.
---

# Zeno Council — question first, design second

This is Gate 1, step 0 of the zeno loop. It runs **before** `zeno-insight` on every non-trivial
Scope. Its job is to make architecture decisions explicit, defensible and traceable: surface the
unknowns that could change the architecture, get them answered or recorded as assumptions, and only
then compare options. The Chief Architect speaks for the council; the user never sees eight
overlapping monologues.

**Iron Law: NO ARCHITECTURE IS PROPOSED UNTIL EVERY UNKNOWN THAT COULD CHANGE IT HAS BEEN ASKED OR
RECORDED AS AN ASSUMPTION.** The council must not invent requirements.

## Depth — Lite or Full (default down)

Start at **Lite**. Climb to **Full** only on named evidence, and record the evidence on the card.

| Depth | When | Output |
|---|---|---|
| **Lite** | Story-tier work that adds no new boundary, data store, integration, security posture or NFR | Chief Architect pass only. No questions to the user. One line on the card: `Council (Lite): no architectural unknowns — checked boundary, data, integration, security, NFR.` |
| **Full** | Any of: a new system or component; a new boundary, integration or data store; sensitive data or a security-posture change; a cross-cutting NFR (scale, availability, compliance); Feature or Epic tier | The phases below, in order |

Depth follows the shape of the work, never the tone of the request: "run the full council" on an
off-by-one fix is still Lite, and a one-sentence request that adds a queue between two components is
Full. A trivial edit (typo, rename, one-line config) skips the loop, council included.

## The roles (inline personas, one thread)

| Role | Owns | Skeptical of |
|---|---|---|
| **Chief Architect / Moderator** | Question backlog, de-duplication, the readiness decision, the debate, the recommendation, the decision log | Invented requirements |
| **Business & Domain** | Goal, actors, workflows, capabilities, bounded contexts, invariants, ownership. Evaluates DDD applicability (hands off to `zeno-workflow/zeno-ddd`) | Boundaries drawn around tech instead of language |
| **Application** | Boundaries, monolith vs services, APIs, sync vs async, coupling/cohesion, developer experience | Unnecessary distribution; microservices without a concrete reason |
| **Data** | Ownership, aggregates, transactional boundaries, consistency, reporting, lifecycle/retention | Event sourcing, CQRS, distributed transactions without justification |
| **Platform / Cloud** | Deployment model, environments, networking, scalability, IaC, operational complexity | Anything heavier than the simplest platform that meets requirements |
| **Security** | Trust boundaries, sensitive data, authn/authz, secrets, encryption, threat model, compliance, audit | Controls out of proportion to actual risk |
| **SRE / Operations** | Availability, SLI/SLO, failure handling, SPOFs, observability, backup/restore, RPO/RTO, rollback, on-call burden | Designs the team cannot operate |
| **Challenger** | Adversarial review. Proposes nothing initially; attacks assumptions, complexity, hidden coupling, lock-in, distributed monoliths, unrealistic scale/team assumptions | Every proposal, including the leading one |

Roles are sections of this skill, not spawned agents (`agents/REGISTRY.md` is unchanged).

## Phase 1 — Discovery (Full)

Each relevant role reads the request and the repo (existing code first, via `zeno-insight` step 1 /
`zeno/references/impact-analysis.md`) and the Chief Architect consolidates. Classify every relevant
statement — never treat an unprovided fact as given:

`FACT` (user stated) · `ASSUMPTION` (likely, unconfirmed) · `UNKNOWN` (needed to decide) ·
`CONSTRAINT` (technology, organization, regulation, money, operations) · `DECISION` · `RISK`.

Do not paste the duplicated per-role analysis at the user.

## Phase 2–3 — Question backlog and interview (Full)

Keep a backlog of questions: id, category, question, requested_by, impact (`CRITICAL`/`HIGH`/
`MEDIUM`/`LOW`), status, answer. Categories: business, users, workflows, functional, performance,
scale, availability, reliability, data, consistency, integrations, APIs, security, privacy,
compliance, deployment, infrastructure, networking, team, support, cost, migration, legacy,
observability, disaster recovery.

- **Use `zeno-insight`'s round format** — `❓ Q<#> - <title>: <body>` with a `➡️ <recommended answer>`
  line — so there is one question loop, not two. At most **7** per round, **3–5** preferred, ordered by
  architectural impact. Say briefly why a question matters.
- **Never ask what the repo, the card or a prior round already answers**, and never ask a low-impact
  question while a high-impact unknown is open.
- **Log each round to the active card's Decisions log as it closes** (questions, answers, newly
  classified facts/assumptions). `zeno-insight` then reads that log and asks only the remaining
  non-architectural frontier.
- **Ask the blocking questions, then stop.** If any blocking unknown remains, ask it, end the turn and wait. Do not
  design, write code or create implementation cards past an unanswered *blocking* unknown (see the
  blocking test below). In a headless run (nobody can answer), the round of blocking questions plus
  the assumptions you would otherwise proceed on *is* the deliverable; "the request said implement
  it" does not lift this.
- After answers: update facts, drop resolved unknowns, add new ones, re-rank, ask the next round. Stop
  when the readiness gate passes — not indefinitely. An unanswered item that does not materially affect
  the architecture becomes a recorded `ASSUMPTION`; an unanswered unknown blocks the gate only if it passes the blocking test.

## What blocks — the blocking test

The impact label (`CRITICAL`/`HIGH`/…) ranks questions; it does not decide whether to stop. An unknown
**blocks** only if some plausible answer would (a) change which option you would recommend, or (b) add a
hard requirement: compliance scope, handling of sensitive or regulated data, an irreversible or
destructive choice, or a new external runtime dependency the user has not accepted. Ask those.

Every other unknown, however it was rated, is recorded as an `ASSUMPTION` with the default you used, and
carried into the recommendation as a "revisit if wrong" condition. Example: SSO protocol (OIDC vs SAML)
or the exact cloud account changes an implementation detail, not which architecture wins, so assume it.
Whether raw card numbers reach the servers changes the compliance scope, so ask it.

When the user says the requirements are settled and asks for proposals, ask only the blocking
questions (usually none to three). If none block, go straight to options in the same reply, with the
assumptions listed first. Stating "settled" never lets sensitive-data handling or a destructive
operation be assumed.

## Readiness gate

Design may begin when these are clear enough that what remains unknown cannot change a major
decision: primary goal · users/actors · critical workflows · important integrations · expected scale ·
availability · data ownership · consistency · security · regulatory · deployment environment · major
technical constraints · team capability · budget sensitivity · operational expectations. Not every item
must be known; unresolved items must not materially block a decision.

## Phase 4 — Independent options (Full)

At least **2** viable options, **3** when meaningfully different approaches exist (e.g. modular
monolith, service-oriented, event-driven, serverless, hybrid — do not force categories). Each states:
boundaries, main components, data ownership, communication, deployment, scalability, reliability,
security, dependencies, operational complexity. Do not converge early.

## Phase 5 — Debate

Each role reviews the other options from its specialty (Data: transactions, consistency, ownership;
SRE: availability, deploy, failure, burden; Security: trust boundaries, authn/z, secrets). The
Challenger attacks every option. **The Chief Architect does not choose before this finishes.**

## Phase 6 — Trade-offs

Compare on: architectural and implementation complexity, scalability, reliability, availability,
maintainability, security, operational burden, cost, developer experience, team fit, lock-in, migration
difficulty, observability, testing complexity. Use qualitative ratings (Low/Medium/High); do not
manufacture precise scores without evidence.

## Phase 7 — Recommendation

Chief Architect writes: **Recommended architecture** · **why it was selected** (the decisive
trade-offs) · **why alternatives were rejected, and when each would become appropriate** · **key
assumptions** · **major risks** · **future triggers** (conditions that justify revisiting; numeric
thresholds only if requirements or measurements support them). This is the architecture-level input to
`zeno-insight` step 5; `zeno-insight` keeps code-level approach choices and the sign-off.

## Rules that bind every phase

- **Simplicity.** Complexity must be earned. No microservices, Kubernetes, Kafka, event sourcing, CQRS,
  service mesh, distributed databases, multi-region or custom infrastructure without a concrete
  requirement that justifies it. Existing technology is not by itself a reason to use it.
- **Technology selection** comes after requirements. For each important choice: the problem it solves,
  why it fits, alternatives considered, operational implications, lock-in.
- **Team reality.** Size, skills, delivery/ops maturity, on-call. An architecture the team cannot operate
  is a poor architecture.
- **Cost** is total cost of ownership — cloud, engineering, operations, maintenance, monitoring,
  incidents, licensing, data transfer, vendor dependency — not raw infrastructure.

## Deliverables — only when they earn their place

System context · containers · components (rarely) · data · integration · deployment · security ·
observability · failure scenarios (DB down, broker down, external API down, consumer failure,
partition, bad deploy, auth provider down — only the relevant ones). Record the substance on the
active card; no new `.zeno/` file types. Diagrams follow `puml-diagrams` (PlantUML, not Mermaid).
At **Feature or Epic tier**, important decisions also get an ADR (Status, Context, Options Considered,
Decision, Rationale, Consequences, Revisit When) written to `documentation`'s ADR standard
(`documentation/architecture-documentation-and-decision-records`); an ad hoc Story's decisions stay in
the card's Decisions log.

## Boundaries with neighbouring skills

- `zeno-stack/zeno-implementation-guardrails` — the Execution-time tripwire (`ARCHITECTURE IMPACT
  DETECTED`) lives there; when it fires mid-implementation, the decision comes back here at Full depth.
- `zeno-insight` — the council runs first; insight reads the council's card log, asks only what remains,
  and owns code-level approach and sign-off. Neither restates the other's steps.
- `software-architecture-progression` — consult it for the staging model (monolith → bounded contexts →
  events → selective services); the council decides *whether the requirements earn the next stage*.
- `zeno-workflow/zeno-ddd` — the council precedes it; DDD frames a Feature's domain once the
  architecture direction is set.
- `engineering:architecture` / `engineering:system-design` (plugins) — inside the zeno loop the council
  wins. Plugin files are never edited.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Proposing an architecture before checking what blocks | Classify, apply the blocking test, and ask any blocking questions; if none block, proceed with recorded assumptions |
| A full eight-role council on a one-file fix | Lite: one card line; climb only on named evidence |
| Raising depth because the request sounded formal | Depth follows the work's shape, not the prompt's tone |
| Treating a missing fact as given | Mark it `ASSUMPTION` or `UNKNOWN`; ask or record |
| Asking more than 7 questions, or low-impact ones first | ≤7 per round, 3–5 preferred, ordered by impact |
| A second question loop beside `zeno-insight` | Same `❓ / ➡️` format, one backlog, logged to the card |
| Re-asking what a prior round or the repo already answered | Read the card's Decisions log and the code first |
| Microservices / Kafka / CQRS / k8s because they are familiar | Name the requirement that earns it, or drop it |
| One option, or options that differ only in vendor | At least 2 meaningfully different options |
| Choosing before the Challenger has attacked | Debate completes first |
| Precise scores with no evidence | Qualitative ratings |
| Spawning eight agents | Inline persona sections in one thread |
| A new ADR/decision file under `.zeno/` | Card Decisions log; ADR format only at Feature/Epic tier |
| Mermaid diagrams | `puml-diagrams` |
| Questioning forever | Stop at the readiness gate; record the rest as assumptions |
| Writing questions as plain prose or `Q1 - …` without the `❓` / `➡️` markers | Use `zeno-insight`'s exact round format so `zeno-insight` and the card log can read it |
| Rating every unknown `CRITICAL` so the gate never opens | Apply the blocking test; non-blocking unknowns become assumptions |
| Proposing options while an unknown that changes the winner is still open | It blocks: ask it first |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "The request is obvious, I'll just propose the design" | Obvious requests hide scale, ownership and consistency assumptions; Lite takes one line, skipping takes an afternoon |
| "They said the full council, so it's Full" | Depth follows the work. Record Lite and the evidence |
| "It's a small change, so the council doesn't apply" | Check the five Lite conditions; a new queue, store or integration is Full whatever the size |
| "I'll ask everything now so I don't forget" | Highest-impact first, ≤7 per round; later questions depend on earlier answers |
| "Microservices will scale later" | Scale is a requirement or it is not. Name it or drop it |
| "The team knows Kafka" | Existing technology is not a requirement. Justify it from the requirements |
| "The user didn't answer, so I'll treat my guess as fact" | Record `ASSUMPTION`; a skipped unknown that passes the blocking test blocks the gate |
| "Hosting and SSO are CRITICAL, so I can't propose anything" | Labels rank questions; the blocking test decides. If no plausible answer changes which option wins, assume and proceed |
| "They said the requirements are settled, so I'll assume the sensitive-data handling too" | "Settled" never licenses assuming card, personal or regulated data handling, or a destructive operation |
| "The request says implement it, so I'll note the risks and build with stated assumptions" | Full evidence requires loading this skill and applying the blocking test. If an unknown blocks, ask and stop; a headless run delivers those questions and its assumptions. If none block, proceed to options with recorded assumptions, then hand off to insight for sign-off before code |
| "I'll skip the Challenger, the options are fine" | The Challenger is the check on your own enthusiasm |

## Red flags — stop, you're about to bypass the council

- You're writing "Approach" text and no council line or question round is on the card.
- You've listed an architecture before the readiness gate passed.
- You're about to recommend a heavyweight technology and cannot name the requirement behind it.
- A question you're about to ask is answered by the repo or an earlier round.
- Your options differ only by vendor, or there is one.
- You're running Full on a change with none of the Full triggers, or Lite on one that adds a boundary.
- You've labelled it "Lite+" or "Full-lite" and are building. There is no such depth: Full evidence requires this skill; blocking unknowns require questions and a stop before options or code.

## Pre-flight checklist — run before delivering any architecture recommendation

- [ ] Depth chosen (Lite/Full) with the named evidence recorded on the card.
- [ ] Lite: one card line naming what was checked; no questions asked.
- [ ] Full: statements classified FACT / ASSUMPTION / UNKNOWN / CONSTRAINT / DECISION / RISK; nothing invented.
- [ ] Questions asked in `zeno-insight`'s round format, ≤7 per round, highest impact first, each with a recommended default; each round logged to the card.
- [ ] Readiness gate passed: every unanswered unknown either failed the blocking test and is a recorded assumption, or was asked; no open blocking unknown.
- [ ] At least 2 meaningfully different options with boundaries, data ownership, deployment, reliability, security and operational complexity.
- [ ] Debate completed — every role reviewed the options and the Challenger attacked each.
- [ ] Trade-off table uses qualitative ratings tied to the stated requirements.
- [ ] Recommendation states why, rejected alternatives and when they would fit, assumptions, risks and revisit triggers.
- [ ] No unearned microservices, Kubernetes, Kafka, event sourcing, CQRS, service mesh, distributed DB or multi-region.
- [ ] Team capability and total cost of ownership considered, not just infrastructure.
- [ ] Output lives on the card; ADR written only at Feature/Epic tier in `documentation`'s format; diagrams in PlantUML.
- [ ] Hand-off made: `zeno-insight` reads the card log and asks only the remaining frontier.
