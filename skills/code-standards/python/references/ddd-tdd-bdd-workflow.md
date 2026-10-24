# DDD + TDD + BDD: An Integrated Workflow for Python Event-Driven Systems

Use this reference together with `./ddd-clean-architecture.md`, not instead of it: that file
owns Python's tactical DDD patterns (value objects, entities, aggregate roots, Repository/
Unit-of-Work, domain events, Protocol-based ports) and the test pyramid/fakes-vs-mocks
baseline. This file owns what sits around and drives that tactical work — strategic domain
design, TDD/BDD as practiced disciplines, and Kafka-specific event-driven testing. Named
positions below (Evans, Vernon, Fowler, Beck, Freeman & Pryce, Khorikov, North, Adzic, Percival
& Gregory) mark real, unresolved industry debates — choose deliberately per bounded context,
don't apply one dogmatically.

**The one rule that matters most: invest in strategic DDD before tactical DDD.** Teams
that adopt "DDD-lite" — aggregates and value objects as a technical toolset while
skipping Bounded Context, Context Maps, and Ubiquitous Language — get most of the cost
and little of the value (Vernon's explicit warning in *Implementing Domain-Driven
Design*).

This file is Python + FastAPI + Kafka scoped, and deliberately holds only the *delta* over the
generic, stack-agnostic theory. For that generic theory — the Three Laws, Arrange-Act-Assert,
the test-double taxonomy, Classicist/Mockist, the Test Pyramid, Canon TDD's full procedure,
BDD's origin and three phases, the full Gherkin keyword reference, the Three Amigos, Example
Mapping, EventStorming's three flavors, and the full Context Mapping pattern table — read the
canonical treatments, which the `zeno` loop's Execution pipeline uses for any language:

- TDD theory: `zeno-workflow/zeno-tdd/references/tdd-concepts.md`
- BDD/Gherkin theory: `zeno-workflow/zeno-bdd/references/bdd-concepts.md`
- Strategic DDD (bounded contexts, context mapping, building blocks): `zeno-workflow/zeno-ddd/SKILL.md`
  and `code-standards/software-architecture/references/ddd.md`

## 1. The integrated workflow

Run these four stages per bounded context / per feature. Don't skip Stage 1 to get to
tactical code faster — that's exactly the DDD-lite failure mode above. This 4-stage sequencing
of the otherwise-generic practices *is* the Python/Kafka-specific contribution of this file.

**Stage 1 — Strategic DDD (once per context, revisited periodically).** Run an
EventStorming session (Big Picture, then Software Design — §2) with domain experts to
surface domain events, aggregates, and bounded-context boundaries. Draw a context map
and label every relationship (§2). Write down the ubiquitous language per context and
enforce it in code — a `Customer` in Billing and a `Customer` in Support are different
types unless deliberately shared. **Threshold to proceed to Stage 2**: you can name the
core domain and its invariants in the domain experts' own language.

**Stage 2 — Testing-architecture setup.** Keep the domain model dependency-free and
invert the ORM dependency (already established in `./ddd-clean-architecture.md`). Apply
Khorikov's rule as the default mocking policy: **mock unmanaged out-of-process dependencies
(Kafka, SMTP, external APIs); never mock a managed dependency (your own database) — use
the real thing in integration tests** (§4). This is the concrete resolution to a real
tension the Python DDD literature doesn't fully settle: Cosmic Python fakes the
repository even for fast service-layer tests, Khorikov would use the real database.
Recommended default for this stack: **fakes at the service layer for fast feedback,
backed by integration tests against a real (containerized) database for the
repository/UoW** — this gets Khorikov's correctness guarantee without giving up Cosmic
Python's speed.

**Stage 3 — Outside-in double-loop TDD, per feature.** Three Amigos + Example Mapping
produce concrete examples (§3); formulate the key ones as **declarative** Gherkin
scenarios in the ubiquitous language — these are the **outer loop** acceptance tests.
Write the failing acceptance test at the system boundary first. Then drop into the
**inner loop**: classical TDD (Beck's Canon TDD, §4) on the aggregates, value objects,
and domain services needed to satisfy the scenario — red-green-refactor at the minute
scale — until the outer acceptance test passes. The outer loop runs in hours-to-days,
the inner loop in minutes; don't confuse their timescales when deciding what to
automate first.

**Stage 4 — Event-driven boundary hardening.** Introduce consumer-driven contract tests
(Pact) between every Kafka producer/consumer pair and wire schema-registry compatibility
checks into CI (§5) — don't rely on end-to-end tests for this. Add the four
async-specific test categories from §5. **Threshold to invest more in E2E**: only when
contract + component tests demonstrably miss a class of integration bug — otherwise
treat E2E as the second line of defense, one test per feature at most, proving the
wiring works rather than re-verifying behavior already covered lower down.

**A subtle, still-open question**: whether to delete mock-heavy inner-loop domain tests
once the outer acceptance test provides regression cover. Default to `./ddd-clean-architecture.md`'s
answer — don't be afraid to delete a domain-model test once its functionality is
covered by a service-layer or acceptance test; a small, deliberately curated core of
domain tests is more valuable than a large, brittle one.

## 2. Strategic DDD & EventStorming (summary)

This is a Python-scoped summary and decision aid. For the full stack-agnostic treatment —
subdomain-vs-bounded-context in depth, the full per-pattern Context Mapping discussion, the
Ubiquitous Language discipline, and EventStorming's three flavors in full — see
`zeno-workflow/zeno-ddd/SKILL.md` and `code-standards/software-architecture/references/ddd.md`.
Don't re-derive that theory here.

- **Subdomain (problem space) vs. bounded context (solution space)** are not
  necessarily one-to-one. Start with one core domain and one bounded context; let
  additional contexts reveal themselves rather than pre-drawing boundaries.
- **Triage effort by subdomain type**: put your best modeling effort and full tactical
  DDD into the **core domain** — the part that differentiates the business. Supporting
  and generic subdomains can use simpler patterns, including an anemic model or
  off-the-shelf software — that's the *contextual* exception to Fowler's anemic-model
  anti-pattern, not a violation of it.
- **Context-mapping pattern, pick the narrowest fit**:

  | Pattern | Use when |
  |---|---|
  | Partnership | Two contexts/teams succeed or fail together, coordinated |
  | Shared Kernel | A common model subset is genuinely shared — use sparingly, every change needs cross-team coordination |
  | Customer/Supplier | An upstream serves a downstream that can influence its roadmap |
  | Conformist | The downstream conforms with no influence — common against a vendor or legacy system you can't change |
  | **Anti-Corruption Layer (ACL)** | Always at least consider this first; a translation layer protects your model from the upstream's. Fall back to Conformist/Shared Kernel only when translation cost is prohibitive |
  | Open Host Service / Published Language | The upstream publishes a stable, documented API/protocol (OpenAPI for REST, AsyncAPI for events) for many downstreams |

  Integrating a modern Python service against an established legacy system (an Oracle
  Retail/PL-SQL estate, or any system you don't own the roadmap for) is the textbook ACL
  case: translate the legacy schema/vocabulary at the boundary rather than letting its
  concepts leak into your bounded context's model.
- **EventStorming** (Alberto Brandolini) is the recommended discovery technique for
  event-driven systems specifically. Three flavors — **Big Picture** (explore an entire
  business line, surface inconsistencies), **Process Modelling**, **Software Design**
  (discover aggregates, commands, policies, and bounded-context boundaries). Orange
  sticky notes = domain events, always past tense. Run Big Picture before Software
  Design for a new context.

## 3. BDD as a practice (summary)

BDD is a collaboration method, not a testing tool — the value is in the discovery
conversation, not the `.feature` file. Three phases: **Discovery** (Three Amigos —
business/product + developer + tester — using Example Mapping to surface concrete
examples), **Formulation** (capture the agreed examples as Gherkin, readable by
stakeholders), **Automation** (wire scenarios to step definitions → living
documentation that stays correct because it's executable).

**Default to declarative Gherkin**, not imperative: describe behavior and outcomes
("Given I am an unauthenticated guest, When I attempt to access restricted content,
Then I am denied access"), not UI mechanics ("enter 'x' in the username field, click
Login"). Push mechanics into step definitions. One behavior per scenario; scenarios must
be order-independent; write scenarios *before* the code they describe, not after
("documentation theater" is a real failure mode).

For the full stack-agnostic theory — BDD's origin, the three phases in depth, the complete
Gherkin keyword reference, the imperative-vs-declarative debate, and the common-pitfalls list —
see `zeno-workflow/zeno-bdd/references/bdd-concepts.md`. What remains below is the
Python-specific delta: tooling.

### Tooling for Python

- **pytest-bdd** if the team already relies on pytest — it's a pytest plugin, so
  fixtures, plugins (including parallel execution via pytest-xdist), and CI integration
  are all reused directly; BDD scenarios run in the same suite as everything else. Best
  when the team already leans on pytest fixtures and mocks heavily.
- **behave** if you want the cleanest standalone Cucumber-like experience, with the
  strongest Gherkin support including data tables — matters when your requirements are
  genuinely data-heavy. Caveat: don't hide example data inside pytest-style fixtures
  when using data-table-driven specs — that defeats Specification-by-Example's whole
  point of keeping examples visible in the scenario itself.
- **Avoid lettuce** — dead since 2016, no reason to pick it for new work.

Default recommendation for a pytest-centric Python/FastAPI team: **pytest-bdd**, to keep
BDD scenarios inside the same test run, fixture ecosystem, and CI pipeline as everything
else. Switch to **behave** only if the team wants a strictly standalone
specification-and-tests separation, or the scenarios are heavily data-table-driven.

## 4. TDD as a practice (summary)

Beck's Canon TDD is the actual procedure, not just "write a failing test": (1) write a
**list** of test scenarios; (2) turn exactly one into a concrete, runnable test; (3)
change the code to make it — and every prior test — pass, without mixing in
implementation-design decisions; (4) optionally refactor; (5) repeat, adding to the list
as new cases surface. The most-skipped step is refactoring; the most common corruption
is mixing "make it pass" with "make it right" (the two-hats problem).

**Classicist by default.** Use real objects and state verification; substitute a double
only for an awkward or unmanaged collaborator. Mockist (London-school, mock every
collaborator, behavior verification) enables strict outside-in development but couples
tests to implementation, making refactors brittle — the industry has drifted toward the
classicist end for exactly this reason.

**Khorikov's actionable mocking rule** (the one to actually apply on this stack): mock
**unmanaged** out-of-process dependencies — Kafka, SMTP, external APIs, anything that
produces an externally observable side effect. Never mock a **managed** dependency —
your own application database, accessible only through your app — use the real thing.
A unit is a unit of *behavior*, not a unit of code: isolate tests from each other, not
from their own collaborators; test observable behavior through the public API, never
private methods.

For the full stack-agnostic theory — Canon TDD's procedure in depth, the classicist/mockist
debate (Fowler's "Mocks Aren't Stubs"), Khorikov's four pillars, and the test-pyramid/
fakes-vs-mocks baseline — see `zeno-workflow/zeno-tdd/references/tdd-concepts.md` and
`./ddd-clean-architecture.md`'s "Testing Strategy" section. Don't re-derive them here. What
remains below is the Python-specific delta: how TDD lands on this stack's tactical DDD patterns.

### Applying TDD to DDD's tactical patterns

- **Aggregates/entities** — test through the aggregate root's public API only, asserting
  invariants hold after each operation. Design the aggregate so invalid states are
  literally unconstructable (an unenforceable invariant in Python usually means the
  constructor/factory needs tightening, not a runtime check bolted on later). These
  tests are pure, dependency-free, and should make up the fast core of your suite.
- **Value objects** — test equality, immutability, and validation. Cheap to write, high
  value; there's rarely a reason to skip these.
- **Domain services** — test as pure functions wherever possible; if a domain service
  needs a collaborator, that's usually a signal it should be a method on an aggregate or
  entity instead.
- **Repositories** — test the *real* implementation against a real (or containerized)
  database in integration tests, per Khorikov's managed-dependency rule above; use a
  `FakeRepository` only for the faster service-layer tests, never as a substitute for at
  least one real integration test per repository.

## 5. Kafka event-driven testing discipline

No amount of unit/service-layer testing verifies that two independently deployed
services agree on a message contract — that needs its own discipline. This entire section is
Python/Kafka-specific with no analog elsewhere in the library.

### Why end-to-end tests don't cover this

An end-to-end test proves *your* service's wiring works. It does not prove that a
producer and a consumer — developed and deployed independently, possibly by different
teams — actually agree on the shape and meaning of a message. That agreement needs its
own, separate testing discipline; treating E2E as sufficient here is the single most
common event-driven testing gap.

### Consumer-driven contract testing (Pact)

Pact supports asynchronous/message-based interactions, not just synchronous HTTP. The
pattern: the **consumer** defines the contract it expects (a message shape, key fields,
required headers) as part of its own test suite; this contract is published (typically
via a Pact Broker); the **producer**'s CI pipeline verifies its actual output against
every consumer's published contract before deploying. This lets producers and consumers
evolve independently — a producer can ship a change with confidence it hasn't broken any
known consumer, without needing a shared integration environment running all services at
once.

Set this up per producer/consumer pair, not as one shared contract for a whole topic —
different consumers of the same topic may care about different fields, and a contract
should reflect what a specific consumer actually depends on, not the full message
schema.

### Schema Registry + compatibility checks

Enforce a data contract (Avro, JSON Schema, or Protobuf, whichever your registry uses)
and run schema-evolution compatibility checks as a CI gate on every producer change —
before merge, not after deploy. A compatibility break should fail the build the same way
a failing unit test does. This is a different concern from contract testing: contract
tests verify a specific consumer's expectations; schema compatibility verifies the wire
format itself hasn't broken in a way that would affect *any* consumer (removing a
required field, changing a type, etc.).

### The four async-specific test categories

Beyond the happy path, a Kafka consumer needs tests for behaviors unique to async
messaging:

1. **Idempotent consumers** — duplicate delivery is a normal Kafka occurrence
   (at-least-once delivery), not an edge case. Test that processing the same message
   twice produces the same end state as processing it once (dedup via a message ID, an
   idempotency key, or a natural aggregate-version check).
2. **Per-partition ordering** — Kafka guarantees order only *within a partition*, not
   across the whole topic. Test that same-key events (which land in the same partition)
   are processed in the order they were produced; do not assume ordering across
   different keys.
3. **Out-of-order / stale-event rejection** — even within ordering guarantees,
   redelivery or retry can present an older event after a newer one has already been
   applied. Test that the consumer rejects or safely no-ops a stale event using a
   version number or timestamp, rather than blindly applying whatever arrives.
4. **Dead-letter routing** — test that a message which repeatedly fails processing gets
   routed to a dead-letter topic/queue rather than blocking the partition or being
   silently dropped, and that the DLQ payload retains enough context to diagnose and
   replay it later.

### Test infrastructure

Use **Testcontainers** (or an embedded Kafka broker) for the small number of integration
tests that genuinely need a real broker — verifying serialization against the real
wire format, or exercising consumer-group rebalancing behavior. Keep these few and
targeted: they're slower and more environment-sensitive than the contract tests and unit
tests that should carry the bulk of your coverage. If a test can be expressed as a
contract test or a unit test against a faked producer/consumer, prefer that over spinning
up a real broker.

### Adjacency: Kafka vs. AMQP

`code-standards/rabbitmq/SKILL.md` is authoritative for AMQP-specific mechanics —
idempotent-consumer patterns via `message_id` + a dedup store, manual-ack/DLX retry topology,
Outbox/Saga/CQRS patterns applied to RabbitMQ. Apply that skill for RabbitMQ work. This section
is authoritative for what's specific to Kafka's model and has no AMQP equivalent:
per-partition ordering guarantees, schema-registry compatibility as a CI gate, and
consumer-driven contract testing across independently-deployed services. The idempotency
*concept* is shared between both brokers; the *mechanics* differ enough (partition/offset
semantics vs. AMQP's ack/DLX model) that each skill covers its own broker rather than one
trying to generalize across both.

For the tactical domain-event/message-bus pattern this testing discipline wraps around
(aggregates raising events, a bus dispatching to handlers, a handler publishing externally),
see `./ddd-clean-architecture.md`'s "Applying this to Kafka / event-driven services" part.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Adopting aggregates/value objects while skipping Bounded Context, Context Maps, and Ubiquitous Language ("DDD-lite") | Invest in strategic DDD first — it's the highest-leverage part |
| Guessing at bounded-context boundaries without a discovery session | Run EventStorming (Big Picture, then Software Design) with domain experts |
| Letting a legacy/vendor system's vocabulary leak into a new bounded context | An Anti-Corruption Layer — always consider it first |
| Mocking your own application database ("managed" dependency) | Use the real (containerized) database in integration tests |
| Never mocking Kafka/SMTP/external APIs ("unmanaged" dependencies) | Mock or fake them — their side effects are externally observable |
| Mockist-by-default (mocking every collaborator) | Classicist by default; mock only awkward/unmanaged collaborators |
| Mixing "make it pass" with refactoring in the same TDD step | Beck's two hats — pass first, refactor as a separate, deliberate step |
| Imperative Gherkin scripting UI mechanics ("click Login") | Declarative Gherkin describing behavior/outcomes; push mechanics into step defs |
| Writing Gherkin scenarios after the code is done | Write scenarios first, from the Three Amigos discovery conversation |
| Scenarios that depend on execution order or another scenario's side effects | Independent, order-agnostic scenarios |
| Treating BDD as a QA-only testing tool | The value is the discovery conversation — include a business/product voice |
| Relying on end-to-end tests to catch Kafka producer/consumer contract drift | Consumer-driven contract tests (Pact) + schema-registry compatibility checks in CI |
| Testing only the happy path for a Kafka consumer | Also test idempotency, per-partition ordering, stale-event rejection, DLQ routing |
| Restating aggregate/repository/UoW mechanics here instead of in the sibling reference | Cross-reference `./ddd-clean-architecture.md` — don't duplicate |

---

## Pre-flight checklist — run before delivering any DDD/TDD/BDD workflow artifact

- [ ] Strategic design (bounded context, ubiquitous language) is established before any
      tactical pattern was applied — not skipped in favor of jumping straight to code
- [ ] Any cross-context/legacy integration has an explicit context-mapping pattern
      named, defaulting to an ACL unless translation cost is prohibitive
- [ ] Mocking follows Khorikov's rule: unmanaged dependencies (Kafka, external APIs)
      mocked/faked; the owned database exercised for real in integration tests
- [ ] TDD steps aren't mixing "make it pass" with refactoring in the same step
- [ ] New Gherkin scenarios are declarative (behavior/outcome), not imperative (UI
      mechanics), and each covers exactly one behavior, independent of execution order
- [ ] Gherkin scenarios were written from a Three Amigos discovery conversation, not
      authored solo after the code already exists
- [ ] Every Kafka producer/consumer pair has a consumer-driven contract test and a
      schema-registry compatibility check, not just end-to-end coverage
- [ ] Kafka consumer tests cover idempotency, per-partition ordering, and stale/out-of-
      order rejection — not only the happy path
- [ ] No aggregate/repository/Unit-of-Work mechanics were restated here instead of
      pointing to `./ddd-clean-architecture.md`
