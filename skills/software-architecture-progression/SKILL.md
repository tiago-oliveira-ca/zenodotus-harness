---
name: software-architecture-progression
description: >
  Guides system-level architectural evolution through five stages: Modular Monolith -> DDD
  Bounded Contexts -> Clean/Hexagonal internals -> Event-Driven integration -> Selective
  Microservices. Use whenever the question is *which* architectural style to apply and *when* —
  structuring a new system, splitting into microservices, applying DDD at project level,
  introducing events. Trigger on: "how should I architect this", "should we split this into
  microservices", "where do bounded contexts live", "is our monolith getting too big", "monorepo
  vs microservices", "when to extract a service", "how to evolve our architecture", system
  design discussions, or greenfield architecture planning.
---

# Pragmatic Architecture Progression

The right architecture is the *simplest one that solves today's problem while keeping
tomorrow's options open*. This skill encodes a pragmatic, staged progression that
resists the gravitational pull of premature complexity.

The most expensive architectural mistake is advancing stages too early — not staying
behind. Rolling back a microservices split costs orders of magnitude more than delaying
one.

---

## The Five Stages at a Glance

```
Stage 1 ──► Stage 2 ──► Stage 3 ──► Stage 4 ──► Stage 5
Modular      DDD          Clean/       Event-       Selective
Monolith  ►  Bounded   ►  Hexagonal ►  Driven    ►  Microservices
             Contexts     Internals    Integration  (only if needed)
```

Each arrow has an **entry gate** — a concrete, observable condition that justifies
crossing it. Do not cross a gate without passing its test.

Stages 1–3 are the default target for most systems. Stage 4 is introduced where async
behavior is genuinely needed. Stage 5 applies to individual modules, not the whole
system at once.

---

## Stage 1 — Modular Monolith

**What it is:** A single deployable unit divided into cohesive, loosely-coupled modules.
Each module owns its data, its business logic, and its public interface. Modules call
each other through well-defined APIs, not by reaching into each other's internals.

**Why start here:**
- One deployment surface, one operational model, one CI pipeline.
- Refactoring module boundaries is cheap — it is just moving code.
- The most valuable insight from distributed systems research is that network hops are
  expensive. A modular monolith eliminates them until they are truly necessary.

**Structure pattern:**
```
src/
  orders/           ← module boundary
    api.py          ← public interface (only thing other modules may import)
    models.py
    service.py
    repository.py
  inventory/
    api.py
    ...
  shared/
    events.py       ← cross-cutting event types (not handlers)
    exceptions.py
```

**Rules for this stage:**
- Modules communicate only through their `api` (or `public`) interface. Cross-module
  imports into internal files are a boundary violation.
- Each module owns its database tables or schema. No joins across module boundaries.
  Use IDs to reference other modules' aggregates.
- If you are tempted to share a database table between two modules, you have found a
  boundary problem — resolve the boundary, not the join.

**Gate to Stage 2** — Cross when you can answer yes to *most* of:
- [ ] The team uses inconsistent or ambiguous names for the same concepts across modules
- [ ] Business rules that span modules are hard to reason about or keep consistent
- [ ] A new team member struggles to understand what each module "owns" in business terms
- [ ] You are building a system with multiple long-lived domain concepts, not just CRUD

---

## Stage 2 — DDD Bounded Contexts and Ubiquitous Language

**What it is:** Apply Domain-Driven Design at the module level to define explicit
*Bounded Contexts* — areas of the domain where a model is coherent, terms are precise,
and a shared language (Ubiquitous Language) is established.

**Why add this:**
- Names are the most expensive bugs. When "Order" means different things to the billing
  team and the fulfillment team, every conversation carries hidden translation cost.
- Bounded Contexts make that cost visible and manageable. They do not eliminate
  difference — they *name* it.

**Context map patterns (use the simplest that fits):**

| Pattern | When to use |
|---|---|
| **Shared Kernel** | Two contexts share a small, stable model subset |
| **Customer-Supplier** | One context produces data the other consumes (upstream/downstream) |
| **Anti-Corruption Layer (ACL)** | Translating between a context you own and one you don't |
| **Open Host Service** | Publishing a stable API for many downstream consumers |

**How to apply:**
1. Run an **Event Storming** or domain walkthrough for each candidate module.
2. For each context, produce a mini-glossary (the Ubiquitous Language) — 10–20 terms,
   what they mean *in this context*, and what they do *not* mean.
3. Draw the **Context Map**: mark relationships and translation points between contexts.
4. A bounded context maps 1:1 to a module in Stage 1. Rename and restructure modules
   to align with discovered context boundaries.

**Gate to Stage 3** — Cross when:
- [ ] Bounded contexts are defined and agreed with domain experts/product owners
- [ ] Each module has a published Ubiquitous Language
- [ ] Context relationships are documented in a Context Map

---

## Stage 3 — Clean / Hexagonal Internals

**What it is:** Apply Clean Architecture or Hexagonal Architecture *inside each module*.
The domain model becomes the center of gravity. All infrastructure (DB, HTTP, messaging)
is pushed to the edges and accessed through ports (interfaces).

**Why add this:**
- Testability: domain logic can be tested without spinning up databases or message
  brokers.
- Replaceability: swapping a database or message broker does not touch domain code.
- The discipline of hexagonal architecture prevents the most common long-term maintenance
  failure: infrastructure concerns bleeding into business logic.

**Layer structure (per module):**
```
orders/
  domain/           ← pure business logic, zero framework imports
    order.py        ← aggregate root
    events.py       ← domain events (plain objects)
    ports.py        ← repository/service interfaces
  application/      ← orchestration, use cases
    place_order.py
    cancel_order.py
  infrastructure/   ← adapters implementing ports
    postgres_order_repository.py
    kafka_event_publisher.py
  api.py            ← module's public interface (calls application layer)
```

**The Dependency Rule:** `domain` has no imports from `application` or `infrastructure`.
`application` imports from `domain` only. `infrastructure` imports from both.
Violations in this direction are always bugs.

Read `code-standards/software-architecture/SKILL.md` for detailed patterns for aggregates,
value objects, use cases, repositories, and domain events at this layer.

**Gate to Stage 4** — Cross a module into event-driven integration *only* when:
- [ ] Two modules need to react to each other's state changes asynchronously
- [ ] You need to decouple the timing of two operations (e.g., email after order placed)
- [ ] A module needs to publish state changes to unknown consumers (open-closed principle)
- [ ] You have identified a consistency boundary problem (eventual consistency is acceptable)

---

## Stage 4 — Event-Driven Integration

**What it is:** Modules communicate through domain events published to a message broker
(Kafka, RabbitMQ, SNS/SQS) instead of direct API calls, where the operation is
genuinely asynchronous or where the producer should not know about its consumers.

**Why add this (and only where needed):**
- Events decouple the *timing* of operations. The Order module does not need to wait
  for the Notification module to send an email.
- Events decouple the *knowledge* of consumers. Adding a new consumer (e.g., Analytics)
  does not change the producer.
- The cost: operational complexity rises substantially. A message broker is another
  system to deploy, monitor, and reason about failure modes for.

**Apply event-driven integration surgically, not globally.**

**Decision matrix:**

| If the operation is... | Use... |
|---|---|
| Synchronous, caller needs the result | Direct module API call |
| Fire-and-forget, timing matters | Domain event + async handler |
| Needs to span multiple modules transactionally | Saga or Process Manager pattern |
| Driven by external system state change | Consumer group + idempotent handler |

**Event design rules:**
- Events are named in **past tense**: `OrderPlaced`, `PaymentFailed`, `ItemShipped`.
- Events carry enough data for consumers to act without querying back: include IDs and
  the relevant state at the time of the event.
- Events are **immutable** and **versioned**. Once published, an event's schema must
  not break existing consumers.
- Consumers must be **idempotent**: processing the same event twice produces the same
  result as processing it once.
- Use a **transactional outbox** pattern to prevent the dual-write problem (persisting
  and publishing in one atomic unit).

**Event schema example:**
```python
@dataclass(frozen=True)
class OrderPlaced:
    event_id: str          # UUID, used for idempotency
    event_version: str     # "1.0"
    occurred_at: datetime
    order_id: str
    customer_id: str
    total_amount: Decimal
    currency: str
    items: list[OrderItem]
```

**Gate to Stage 5** — Extract a module into a microservice *only* when:
- [ ] The module has a demonstrably different *scaling profile* from the rest of the
     monolith and the cost of scaling everything is measurable and high
- [ ] The module needs to be *deployed independently* due to release cadence mismatches
     or team ownership boundaries
- [ ] The module has fundamentally different *runtime requirements* (e.g., GPU workloads,
     special compliance isolation, different language/runtime)
- [ ] The team *owning the module* is large enough to own its full operational stack
     (oncall, CI/CD, observability)
- Comfort with event-driven integration (Stage 4) is a prerequisite: distributed
  transactions are harder, not easier, in microservices

---

## Stage 5 — Selective Microservices

**What it is:** Extract individual modules that have passed the Stage 4 gate into
independent, separately-deployed services. The rest of the system remains a monolith.

**Why selective (not wholesale):**
- Most modules do not qualify for extraction. Forcing everything into microservices
  because one module needs it is the most common architectural mistake in modern systems.
- A selective extraction preserves the operational simplicity of the monolith for the
  90% of modules that do not benefit from independence.

**Extraction checklist:**
- [ ] The module already has clean internal boundaries (Stage 3 applied)
- [ ] The module communicates with the rest of the system only through its public API
     and/or events (no internal imports from other modules)
- [ ] You have defined the inter-service contract (API schema, event schema) and it is
     stable
- [ ] The service has its own data store and does not share tables with the monolith
- [ ] CI/CD pipeline, observability (metrics, tracing, logs), and oncall runbook exist
     for the new service *before* extraction

**Anti-patterns to refuse:**
- Extracting a module *hoping* to define clean boundaries afterward
- Sharing a database between the extracted service and the monolith
- Extracting a module because it is "interesting" or "new technology"
- Extracting everything at once ("big bang microservices")

---

## How to Use This Skill

### Inside the zeno loop

`zeno-council` runs first at Scope and decides, from the stated requirements, whether the next stage
is earned; this skill supplies the staging model it consults. If they disagree on whether to advance a
stage, the council's requirement-backed recommendation wins.

### For new systems

Start at Stage 1. Apply Stage 2 when the team agrees on bounded contexts. Apply Stage 3
immediately after Stage 2 — it is low-cost and pays dividends for the life of the system.
Hold at Stage 3 until a concrete async need arises.

### For existing systems

1. **Identify where the system is today** — read through the stages and match the
   current codebase to the description that fits best.
2. **Identify the pain the user is experiencing** — name the specific problem (e.g.,
   "can't deploy order module without testing everything", "two modules share a table").
3. **Check the gate for the next stage** — does the pain map to a gate condition?
   If yes, advance. If not, the problem may be fixable within the current stage.
4. **Advance one stage at a time** — skipping stages compounds technical debt rather
   than eliminating it.

### For architecture reviews

Score each module against its current claimed stage:
- Does the module structure match the stage description?
- Are the gate conditions for the current stage clearly met?
- Are there any regressions (e.g., Stage 3 module with infrastructure leaking into domain)?
- Is there premature complexity (e.g., microservices without event-driven integration)?

---

## Anti-pattern quick reference

| Anti-pattern | Symptom | Correction |
|---|---|---|
| **Stage inflation** | "We use microservices because we do DDD" | Check the Stage 4 gate. Microservices require specific justification, not just good architecture. |
| **Boundary avoidance** | Modules import from each other's internals | Enforce `api.py` contracts. Treat cross-module internal imports as build-time errors. |
| **God context** | One bounded context owns 80% of the domain | Re-run Event Storming. The context is likely two or three contexts with a naming problem. |
| **Event overuse** | Every state change publishes an event | Direct API calls are fine for synchronous, result-dependent operations. |
| **Premature extraction** | Extracting a module with messy boundaries | Apply Stage 3 first. Never extract a module you wouldn't be confident unit testing. |
| **Shared database** | Multiple services write to the same tables | Each bounded context/service must own its data. Migrate before extracting. |
| **Extract-then-define** | Extracting a module *hoping* to define clean boundaries afterward | Define the boundary first (Stage 3); extract only a module you could already unit-test in isolation. |
| **Résumé-driven extraction** | Extracting a module because it is "interesting" or uses new technology | Extraction needs a concrete scaling/ownership/deploy-cadence justification, not novelty. |
| **Big-bang microservices** | Extracting everything at once | Extract one service at a time, each with its own data and a proven boundary. |

---

## Relationship to the `software-architecture` Standards

This skill governs **system topology** (how many deployables, how modules communicate,
when to split). The `software-architecture` standards under `code-standards` govern **code
structure within a module** (aggregates, use cases, repository pattern, SOLID). They are
complementary.

Apply this skill first (decide the system shape), then read
`code-standards/software-architecture/SKILL.md` inside each module (decide the code shape).

---

## Pre-flight checklist — run before delivering any architecture-stage recommendation

- [ ] The current stage was matched against the actual codebase, not the team's claimed stage.
- [ ] The specific pain point was named (not just "this feels messy") and checked against the
  next stage's gate condition.
- [ ] Advancement is by exactly one stage — no skipping.
- [ ] None of the anti-patterns above apply to the recommendation (stage inflation, boundary
  avoidance, god context, event overuse, premature extraction, shared database, extract-then-define,
  résumé-driven or big-bang extraction).
- [ ] For a review: the module was scored against its current claimed stage, including
  checking for regressions and premature complexity.
- [ ] System-topology concerns (this skill) were kept separate from in-module code-structure
  concerns (`code-standards/software-architecture`) — not conflated in the recommendation.
