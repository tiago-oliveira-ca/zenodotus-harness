# Python DDD, Clean Architecture, SOLID & Design Patterns

This supersedes the generic `code-standards/software-architecture` skill for Python — read this
file first for Python architecture/domain-modeling decisions and fall back to the generic skill
only for concerns not covered here.

Scope: idiomatic Python 3.11+. General Python style (PEP 8/20/257, naming, typing, exceptions,
testing mechanics) is covered by the parent `../SKILL.md` — read it first. This file only
covers architecture and domain modeling: when to introduce it, and how it maps onto Python
specifically.

Primary references, cited throughout: Percival & Gregory, *Architecture Patterns with Python*
(O'Reilly, 2020; free at cosmicpython.com — first edition only, no second edition exists as of
this writing) and Leonardo Giordani, *Clean Architectures in Python* (2nd ed., free at
thedigitalcatbooks.com). Library version numbers below were verified against PyPI in
mid-2026 — re-check before citing an exact version to a user; maintenance status drifts faster
than this file is updated.

## Adopt this as a spectrum, not a religion

The right amount of architecture is a function of how much real domain complexity exists, not
a fixed stack to apply everywhere:

- **FastAPI microservices and Kafka event handlers with real business invariants** — the full
  stack (decoupled domain model, service/handler layer, Repository + Unit-of-Work, manual DI
  composition root) earns its keep.
- **Airflow DAGs and most ETL** — keep it lightweight. Extract pure, unit-testable
  transformation functions and skip the onion; see the "Applying this to Airflow / ETL" part of
  the Testing Strategy section below for what this looks like concretely.
- **CRUD-heavy or thin orchestration code anywhere** — the lightweight path applies regardless
  of framework. Don't introduce aggregates, repositories, or extra layers because this file
  exists; introduce them because a concrete invariant or swap-of-infrastructure need showed up.

## How to use this file

| Task focus | Where |
|---|---|
| SOLID applied to Python specifically, the GoF pattern catalogue collapse, dependency-injection approaches ranked with library maturity | The "SOLID in Python, the Pattern-Catalogue Collapse, and Dependency Injection" section below |
| Testing strategy (fakes vs. mocks), applying this to FastAPI/Kafka/Airflow concretely, and the over-engineering counterarguments | The "Testing Strategy, Applying This to FastAPI/Kafka/Airflow" section below |
| Strategic DDD (bounded contexts, context mapping, EventStorming), TDD-as-practice (Canon TDD, classicist/mockist), BDD/Gherkin, Kafka-specific event-driven testing | sibling reference `./ddd-tdd-bdd-workflow.md` — read it alongside this file, not instead of it |

Read the SOLID/Patterns section before recommending a design pattern or a DI framework. Read the
Testing Strategy section before writing the test suite for a service-layer/domain design, or
before deciding how much architecture an Airflow DAG needs.

## Python collapses most of the ceremony

Duck typing and first-class functions absorb a large fraction of what Java-style Clean
Architecture needs explicit machinery for. Where the classical OO formulation of a principle
or pattern conflicts with Python idiom, **the Python idiom wins** — but say why, so the user can
disagree deliberately rather than inherit a Java-shaped rule silently:

- Strategy, Command, Factory, and Template Method are largely invisible in Python — a function,
  closure, or `functools.partial` replaces the class hierarchy (Peter Norvig 1996, Alex
  Martelli 2007, Brandon Rhodes' python-patterns.guide). See the SOLID/Patterns section below
  for the full mapping.
- `typing.Protocol` (PEP 544, structural subtyping — "static duck typing") replaces most
  interface-heavy Dependency Inversion. An adapter satisfies a port without inheriting from it;
  your type checker verifies conformance statically while the dependency arrow still points
  inward at runtime.
- Modules are singletons (cached in `sys.modules` on first import) — don't hand-roll a
  `__new__`-based Singleton class.
- SOLID still applies, but as **design questions** ("which change forces this unit to change?",
  "can I test this without the real DB?"), not as a mandate for class hierarchies. Duck typing
  makes ISP and DIP partly free; don't scatter interfaces everywhere just because Java does.

## Dependency inversion without formal interfaces

The dependency rule is the load-bearing idea, independent of language: **source-code
dependencies point only inward** — infrastructure → application → domain, never the reverse.
Your domain must not import FastAPI, SQLAlchemy, or a Kafka client library.

In Python you have three idiomatic ways to define a **port** (the contract your core code
depends on) — pick based on how much you need to lean on the type checker:

| Approach | When to use |
|---|---|
| Pure duck typing (no declared type at all) | The port is just the method names/signatures your core expects; smallest, most Pythonic for a single obvious adapter |
| `typing.Protocol` | **Default choice.** Structural subtyping — adapters conform without inheriting; static verification via mypy/pyright without runtime coupling |
| `abc.ABC` | You want shared default-method implementations, a real hierarchy, or `isinstance` checks |

```python
from typing import Protocol

class BatchRepository(Protocol):          # the PORT — a structural contract
    def add(self, batch: "Batch") -> None: ...
    def get(self, reference: str) -> "Batch": ...

class SqlAlchemyRepository:               # an ADAPTER — no inheritance needed
    def __init__(self, session): self.session = session
    def add(self, batch): self.session.add(batch)
    def get(self, reference): return self.session.query(Batch).filter_by(ref=reference).one()

class FakeRepository:                     # an in-memory ADAPTER for fast tests
    def __init__(self, batches): self._batches = set(batches)
    def add(self, batch): self._batches.add(batch)
    def get(self, reference): return next(b for b in self._batches if b.reference == reference)
```

**Don't let the ORM invert the relationship back onto you.** Making the domain model inherit
from a SQLAlchemy declarative base couples the domain to persistence. Prefer SQLAlchemy's
imperative/classical `mapper` so the ORM imports the domain model, not the other way around —
"the ORM depends on the domain, and not the reverse" is the concrete test for whether inversion
actually held.

## Project layout

A pragmatic `src`-layout, adapted from cosmicpython:

```text
src/yourapp/
    domain/          # model.py — entities, value objects, events; NO external imports
    adapters/         # repository.py, orm.py, email.py — concrete infrastructure
    service_layer/    # services.py / handlers.py, unit_of_work.py, messagebus.py
    entrypoints/       # fastapi_app.py, kafka_consumer.py — thin, no business logic
    bootstrap.py       # composition root: wires real adapters into handlers
tests/
    unit/              # domain + service layer, against fakes
    integration/       # repository/UoW against a real DB
    e2e/               # a handful of real HTTP/Kafka round-trips
```

Keep `entrypoints/` thin: parse and validate at the boundary (Pydantic), call a service-layer
function, translate domain exceptions to the transport's error shape. If a path operation or
consumer function contains an `if` on business state, that rule escaped the domain — push it
back into the aggregate.

## DDD tactical patterns map cleanly onto Python

| Pattern | Python idiom |
|---|---|
| Value object | `@dataclass(frozen=True)` — free structural `__eq__`/`__hash__`, immutable |
| Entity | A mutable class with identity-based equality (`__eq__`/`__hash__` on an ID field, not all fields) |
| Aggregate root | An entity that owns child objects and enforces invariants; the only thing referenced by ID from outside |
| Domain service | A plain module-level function — "not everything has to be an object" |
| Domain event | A simple (often frozen) dataclass |
| Repository | A dict-like abstraction over persistence — see Repository & Unit of Work below |
| Unit of Work | A context manager — see below |

```python
from dataclasses import dataclass

@dataclass(frozen=True)          # VALUE OBJECT: identity == value, hashable for free
class OrderLine:
    order_reference: str
    sku: str
    quantity: int

class Batch:                     # ENTITY / AGGREGATE ROOT: identity-based equality
    def __init__(self, ref: str, sku: str, qty: int):
        self.reference = ref
        self.sku = sku
        self._purchased_quantity = qty
        self._allocations: set[OrderLine] = set()

    def __eq__(self, other):
        return isinstance(other, Batch) and other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def allocate(self, line: OrderLine):          # invariant enforced on the aggregate root
        if line.sku == self.sku and self.available_quantity >= line.quantity:
            self._allocations.add(line)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - sum(l.quantity for l in self._allocations)
```

Note `Batch.allocate` is behavior, not a setter — the invariant (`sku` must match, quantity
must be available) lives with the data it protects, not in a caller that pokes at attributes.

### Value objects: dataclass vs. attrs vs. pydantic

Don't reach for the same tool everywhere — tier by where the object sits:

| Tool | Use for | Why |
|---|---|---|
| `@dataclass(frozen=True)` | Internal domain value objects (default choice) | Stdlib, zero dependencies, free structural equality/hash. Caveat: SQLAlchemy's classical `mapper` mutates the class at runtime — you may need `unsafe_hash=True` when mapping a frozen dataclass |
| `attrs` (`@define`, `frozen=True`) | Internal domain objects that need validators/converters without validation-on-every-access cost; memory-sensitive high-volume objects (`slots=True` cuts memory materially vs. plain dataclasses) | Faster than dataclasses, opt-in validation, `evolve()` for immutable updates |
| `pydantic` v2 | Boundary DTOs only — HTTP request/response models, Kafka message schemas, settings | Validation-first, coercion, JSON-schema, native FastAPI integration — but validation is never free and models are heavier per-instance than dataclasses/attrs |

A layered strategy — pydantic at the edges, dataclasses/attrs for internal domain objects,
`cattrs` to bridge between them when needed — avoids paying pydantic's validation cost on
objects that live entirely inside a transaction boundary you already control.

## Aggregates, domain events, and the message bus

An aggregate is a **consistency boundary**: one entity (the root) owns child objects and
enforces invariants; external code references other aggregates by ID only, never by direct
object reference. This is also your **concurrency boundary** — pair aggregates with an
optimistic-concurrency version number rather than table-wide locks:

```python
# Optimistic concurrency at the aggregate boundary
UPDATE orders SET status = :new_status, version = version + 1
WHERE order_id = :order_id AND version = :expected_version;
-- SQL%ROWCOUNT/rowcount == 0 → raise a concurrency conflict, don't silently retry blind
```

This matters directly for Kafka consumers processing in parallel: version numbers let two
consumers racing on the same aggregate fail loudly and retry, instead of one silently
clobbering the other's write.

Represent domain events as plain (often frozen) dataclasses; a simple in-process message bus
dispatches them to handlers. This is the natural bridge to an event-driven architecture:
internal domain events → published Kafka events; consumed Kafka messages → commands dispatched
on the bus → handler runs inside a Unit of Work → domain emits new events → publish.

## Repository & Unit of Work

**Repository** — an abstraction over persistent storage that looks like an in-memory
collection (`add`, `get`); see the `BatchRepository`/`SqlAlchemyRepository`/`FakeRepository`
trio above.

**Unit of Work** — an abstraction over atomic operations. Implement it as a **context
manager**: it opens on `__enter__`, rolls back by default on `__exit__` (safe by default —
nothing commits unless the caller explicitly asks), and exposes `commit()`.

```python
from typing import Protocol

class AbstractUnitOfWork(Protocol):
    batches: BatchRepository
    def __enter__(self) -> "AbstractUnitOfWork": ...
    def __exit__(self, *args) -> None: ...        # rolls back by default
    def commit(self) -> None: ...

class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = SqlAlchemyRepository(self.session)
        return self

    def __exit__(self, *args):
        self.session.rollback()                   # safe-by-default; explicit commit required
        self.session.close()

    def commit(self):
        self.session.commit()
```

The UoW narrows the interface the service layer depends on to exactly what it needs — it never
sees the raw SQLAlchemy session — and gives you a single seam to fake in tests.

## Domain services vs. application (service-layer) services

- **Domain service** — stateless business logic that doesn't naturally belong to one entity.
  In Python this is usually just a **function**, not a class with one method and no fields.
- **Application/service-layer function** — orchestration: fetch from the repository via the
  UoW, check state, invoke the domain, commit. Contains **no business rules of its own** — if
  you see `if order.status == "DRAFT"` here, that rule escaped the aggregate.

## When to introduce this — and when not to

Guess where boundaries go and you will sometimes guess wrong; the fix is to keep the *option*
of adding a boundary cheap, not to build every layer up front.

**Stage 1 — baseline hygiene, everywhere, always:**
- Ruff (lint + format) + mypy in pre-commit/CI; start mypy lax, ratchet toward `strict` per
  package.
- `frozen` dataclasses (or attrs) for internal value objects; pydantic v2 only at boundaries.
- Extract business logic out of framework code — out of Airflow DAG files and FastAPI path
  operations especially — into plain, importable, unit-tested functions.

**Stage 2 — introduce architecture where complexity justifies it** (FastAPI/Kafka services
with real domain logic):
- Ports as `typing.Protocol`; Repository + Unit-of-Work over SQLAlchemy; in-memory fakes for
  tests.
- A thin service/handler layer plus a message bus for domain events, wired from a single
  `bootstrap.py` composition root (see the SOLID/Patterns section below for the pattern).
- Build the test pyramid — see the Testing Strategy section below.

**Stage 3 — only if you feel real pain:**
- A DI framework, only once dependency chains genuinely deepen — see the SOLID/Patterns section
  below for ranked options and their current maintenance status.
- A Result type (`returns` library) for core domain logic only where explicit, composable
  error flow clearly beats exceptions and the team is bought into the style.

**Concrete thresholds:**
- **Add a port/boundary** when a second adapter actually appears (second DB, second message
  transport) or a component genuinely needs to be swapped or faked — not speculatively.
- **Drop back toward the lightweight path** if a trivial change touches many pass-through
  files, a new engineer can't trace a flow, or the domain is thin (CRUD/ETL glue).
- **Escalate DI from manual to a framework** only when the composition root becomes unwieldy
  from nested dependencies with mixed singleton/scoped/transient lifetimes.

---

# SOLID in Python, the Pattern-Catalogue Collapse, and Dependency Injection

Read this section before recommending a design pattern, invoking a SOLID principle as a rule
rather than a question, or suggesting a DI framework.

## SOLID translates but deflates

All five principles remain useful **lenses**, but duck typing gives away part of the win for
free, and rigid application produces distinctly un-Pythonic code. Use them as pressure-test
questions ("which change forces this unit to change?", "can I test this without the real DB?"),
not as a mandate for class hierarchies.

| Principle | What it means in Python |
|---|---|
| **SRP** — one reason to change | The unit can be a function or a module, not necessarily a class. Split by responsibility at whatever granularity actually has one reason to change. |
| **OCP** — open for extension, closed for modification | Achieved with registries (a `dict` of handlers), callables, and plain duck typing — you often don't need to touch existing code to extend behavior, without a formal extension-point class. |
| **LSP** — substitutability | Governs subclasses *and* Protocol implementations *and* test fakes. A `FakeRepository` or `RecordingSender` must honor the same contract (same inputs accepted, same promises kept) as the real adapter, or green tests are lying to you. |
| **ISP** — clients shouldn't depend on methods they don't use | Duck typing gives you this mostly for free — a caller only relies on the methods it actually calls. `Protocol` lets you declare narrow role-interfaces (`Readable`, `Writable`) explicitly when you want the type checker to enforce it. |
| **DIP** — depend on abstractions, not concretions | The most valuable principle for architecture. The "abstraction" can be a `Protocol`, an `ABC`, or just a duck-typed contract — see the Dependency Inversion section above. |

**Practical limits worth saying out loud to a user:** don't scatter interfaces everywhere just
because Java does — Python's EAFP style and duck typing already deliver most of that
flexibility. ORMs make strict DIP genuinely painful because they intrinsically couple
persistence and domain; accept some imperfection there rather than fighting the ORM to
preserve a theoretically pure boundary.

## Most GoF creational/behavioral patterns are redundant in Python

Norvig (1996), Martelli (2007), and Brandon Rhodes' python-patterns.guide converge on the same
observation: Python's dynamism absorbs much of what these patterns exist to work around in
statically-typed, class-only languages. Recommend the plain version first; reach for the
classical pattern only when the plain version genuinely stops scaling.

| GoF pattern | Redundant in Python because... | Use instead |
|---|---|---|
| Strategy | Functions are first-class | Pass a function |
| Command | A callable *is* a command | A closure, callable object, or `functools.partial` |
| Abstract Factory / Factory Method | Classes are first-class runtime objects | Pass the class itself, or a plain factory function |
| Template Method | Composition replaces the fixed-skeleton-plus-hook-methods shape | Pass in the step functions; compose instead of subclassing |
| Singleton | Modules are singletons — cached once in `sys.modules` | A module-level instance. If you need shared *mutable* state across instances, use the Borg/Monostate pattern (Martelli), not a hand-rolled `__new__` guard |
| Prototype / Builder | Keyword arguments and stdlib helpers cover most cases | `dataclasses.replace()`, `copy.deepcopy()`, keyword-only constructors |
| Iterator | It's a language feature | `__iter__`, generators, generator expressions |

**Patterns that still earn their keep in Python:**

- **Adapter** — wrapping a third-party API to match your port's shape. This *is* ports and
  adapters; it doesn't go away just because the language is dynamic.
- **Facade** — simplifying a complex subsystem behind one entry point.
- **Proxy** — lazy loading, access control, or caching in front of a real object.
- **Decorator** — both the GoF pattern and Python's `@decorator` syntax are genuinely useful
  here; they're not redundant, they're native.
- **Observer / pub-sub** — this is literally your message bus.
- **State**, **Composite** — still earn their keep when the structure they describe is real.

The meta-point (Rhodes): Pythonistas see fewer patterns partly because the language absorbs
them, and partly because a lot of Python code is glue/framework code where the GoF catalogue
was never the right tool to begin with. Don't port a pattern from a Java codebase just because
it was there — ask what problem it's solving first.

## Dependency injection approaches, ranked

### 1. Manual DI via a composition root — the default

A single `bootstrap.py` wires real adapters (prod) or fakes (test) into handlers, using
closures or `functools.partial` to pre-inject dependencies. No framework, fully explicit,
trivially testable. **Start here for every project.**

```python
# bootstrap.py — the composition root
import functools
import inspect

def bootstrap(uow: AbstractUnitOfWork, publish) -> MessageBus:
    dependencies = {"uow": uow, "publish": publish}
    injected_handlers = {
        cmd_type: [inject(handler, dependencies) for handler in handlers]
        for cmd_type, handlers in COMMAND_HANDLERS.items()
    }
    return MessageBus(injected_handlers)

def inject(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {name: dep for name, dep in dependencies.items() if name in params}
    return functools.partial(handler, **deps)
```

FastAPI's own `Depends()` is a lightweight, built-in DI mechanism that works well for
request-scoped resources (DB sessions, current user, auth). It is not a full IoC container,
though — for deep dependency chains with mixed lifetimes (singleton/scoped/transient) it
becomes painful, which is the actual trigger for stage 2 below.

### 2. A DI framework — only once dependency chains get deep

"If you ever get into dependency chains... you may get some mileage out of a 'real' DI
framework" (cosmicpython). Don't reach for one before that point. Options, with maintenance
status as verified in mid-2026 — **re-check PyPI/GitHub before recommending a version or
maintenance claim to a user; this drifts fast**:

| Library | Notes |
|---|---|
| `dependency-injector` (ets-labs) | Most popular option: Cython-fast, mypy-friendly, declarative containers, FastAPI wiring. Had a multi-year maintenance gap (roughly Dec 2022–Aug 2024) but is active again as of 2026. Downside users cite: `Provide[Container...]` wiring leaks the container into call sites. |
| `punq` (by Bob Gregory, a co-author of *Architecture Patterns with Python*) | Small, unintrusive IoC container. Stable but slow-moving — verify the latest release isn't years old before treating it as actively maintained. Fine for small, stable dependency graphs. |
| `injector` (+ `fastapi-injector`) | Guice-inspired, requires `@inject` decorators; a reasonable combo specifically for FastAPI request scoping. |
| Newer entrants (Dishka, svcs, wireup, kink) | Exist and may be worth evaluating — verify current maintenance against PyPI/GitHub before adopting; none has broad, long-track-record adoption yet. |

The honest community observation: the Python DI-framework ecosystem is thin (few libraries
exceed 1k GitHub stars) because most Pythonistas do manual DI or lean on framework built-ins
instead. That's a signal to default to manual DI, not a gap to fill by picking a framework
preemptively.

### Result types as an alternative to exceptions for domain failures

Python is exception-first (EAFP) and that's correct for I/O and framework boundaries — let
FastAPI turn exceptions into HTTP responses. Domain exceptions can express real domain
concepts too (`OutOfStock` reads better than a generic `ValueError`).

For core business logic where you want failures visible in the type signature and composable,
a **Result type** is a legitimate alternative. The `returns` library (`Result`/`Success`/
`Failure`, railway-oriented programming, pattern-matchable on Python 3.10+) is the best-known
implementation — but treat it as genuinely contested, not settled: it trades verbosity and
interop friction with exception-based libraries for explicit, forced-handling error flow.
Recommend it only where the team is bought into the style and the failure is expected/routine
(validation, business-rule rejection) — use exceptions for the genuinely exceptional, and don't
introduce `returns` as a blanket default across a codebase.

---

# Testing Strategy, Applying This to FastAPI/Kafka/Airflow, and the Over-Engineering Counterarguments

Read this section before writing the test suite for a service-layer/domain design, before
deciding how much architecture an Airflow DAG needs, or before pushing back on a user who
thinks this whole file is over-engineering for their task (they may be right).

## Testing strategy

**Test pyramid, applied to this architecture:**

- **Unit tests (fat base)** — domain and service-layer logic against fakes
  (`FakeRepository`, `FakeUnitOfWork`), no real database or broker. These should be the large
  majority of the suite and run in milliseconds.
- **Integration tests (thinner)** — Repository/UoW against a real database; Kafka
  producer/consumer against a real broker or a testcontainer. These verify the fakes actually
  match reality.
- **End-to-end tests (a few)** — a handful of real HTTP/Kafka round-trips through the full
  stack, enough to catch wiring mistakes the composition root could hide.

Push tests to the highest level of abstraction that still catches the bug — a service-layer
test that exercises three domain rules through one call is worth more than three narrow domain
unit tests that each require the reader to reconstruct the scenario.

**Fakes over mocks for code you own.** A `FakeRepository`/`FakeUnitOfWork` (plain in-memory
implementation of the Protocol) is internally coherent and refactor-resilient. Over-mocking
creates green suites that pass while production breaks — the classic failure mode is a mock
configured to return a flat dict while the real dependency returns something nested. Keep
fakes honest by running the same contract/integration tests against both the fake and the real
adapter periodically.

**Mock only at the edge**: third-party APIs, payment/email providers, the clock (`freezegun`),
randomness (seed it), the network. This is Hynek Schlawack's "don't mock what you don't own" —
you own your Repository and UoW abstractions, so fake them; you don't own `stripe` or `boto3`,
so mock the call to them.

## Applying this to FastAPI microservices

FastAPI is the sweet spot for the full pattern set described earlier in this file.

- Path operations are **entrypoints/adapters** — keep them thin: parse and validate with
  Pydantic, call one service-layer function, translate domain exceptions to HTTP status codes.
  A router that branches on business state has a leaked domain rule; move it back into the
  aggregate.
- Inject the UoW/handlers via the `bootstrap.py` composition root for anything beyond
  request-scoped resources; use `Depends()` for request-scoped things (DB session, current
  user) where FastAPI's own DI already does the job.
- Keep the domain model Pydantic-free where you want it pure. DTOs at the boundary are
  Pydantic; the aggregate underneath is a dataclass or attrs class.

## Applying this to Kafka / event-driven services

The message-bus + command/event + handler model described earlier is, in effect, an
in-process version of what a Kafka-based architecture does across services:

```
Consumed Kafka message → deserialize (Pydantic) → command
    → handler runs inside a Unit of Work
    → domain emits events
    → publish new Kafka events
```

- Aggregates as consistency boundaries, paired with optimistic-concurrency version numbers,
  are the right tool for parallel consumers — prefer this over coarse table-wide locks.
- Idempotency and at-least-once delivery semantics belong in the **adapter layer**
  (deduplication by message ID, for example), not the domain. The domain shouldn't need to
  know a message might arrive twice.

## Applying this to Airflow / ETL — relax the architecture deliberately

This is where purist Clean Architecture causes the most friction and returns the least value.
DAGs are orchestration glue, not domain logic, and treating them like a bounded context with
entities/use-cases/presenters is usually pure overhead.

Concrete guidance:

- **DAG files are orchestration only.** Keep transformation logic in separate, importable,
  framework-free Python modules/functions that take data in and return data out — unit-test
  them with pytest, no Airflow runtime required.
- **Avoid top-level code in DAG files** — it runs on every scheduler parse, not once.
- **Validate structurally in CI**: `airflow dags list-import-errors` and DAG-validation tests
  catch broken imports and cycles before deploy.
- **Dry-run functionally**: `dag.test()` or
  `airflow tasks test <dag_id> <task_id> <execution_date>` exercises task logic without a full
  scheduler; mock external systems at the edge for these runs.
- **Data-quality checks are first-class tasks**, not an afterthought — SQL check operators or
  Great Expectations belong in the pipeline itself. "Clean in, clean out" is a false
  assumption; verify it.

The dependency-inversion instinct still helps here in one narrow way: a `Repository`/gateway
over your warehouse makes transformation logic testable without a live database connection.
But the full entities/use-cases/presenters ceremony described earlier is usually overkill
for a DAG — apply the Stage 1 baseline-hygiene guidance, not Stage 2.

## Criticisms and counterarguments — take these seriously

A user pushing back on this architecture is often right. Known, real failure modes:

- **Boilerplate explosion.** Rigid Clean Architecture can turn a one-field change into edits
  across seven or more files. For the majority of projects that don't need the boundary yet,
  this is a genuine maintainability cost, not a strawman.
- **Guessing where boundaries go is unavoidable, and guessing wrong is expensive to fix.**
  Even Robert C. Martin concedes in *Clean Architecture* that boundary placement is a guess.
  Over-engineering is usually worse than under-engineering — but retrofitting a boundary after
  the fact is real work. The resolution used throughout this file: keep the *option*
  cheap (a plain `logic.py` module, a thin service function) without building every ring
  up front.
- **Cognitive load is real.** More indirection means more files a reader has to jump between
  to trace one flow. This is a measurable tax on new or mixed-experience teams, not just an
  aesthetic complaint.
- **Don't port Java dogma wholesale.** Interfaces everywhere, `__new__`-based singletons, and
  factory-method hierarchies produce code that is *harder* to read and test in Python than the
  plain-function equivalent. If a recommendation in this skill starts to look like translated
  Java rather than idiomatic Python, that's a signal to reconsider it, not to defend it.
- **When simpler clearly wins**: MVPs and prototypes, short-lived scripts, single-adapter
  apps, small teams, and most Airflow DAGs. Use the smell test: if a pattern is creating more
  mess and effort than it returns, something is wrong — patterns exist to serve the code, not
  the other way around.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Domain package importing FastAPI, SQLAlchemy, or a Kafka client | Dependencies point only inward: infrastructure → application → domain |
| Domain model inheriting from a SQLAlchemy declarative base | Imperative/classical `mapper` — the ORM imports the domain, not the reverse |
| Class hierarchies for Strategy/Command/Factory/Template Method | A function, closure, or `functools.partial` |
| Hand-rolled `__new__`-based Singleton class | Modules are already singletons (cached in `sys.modules`) |
| Scattering Java-style interfaces everywhere | `typing.Protocol` (or plain duck typing) at the point of use |
| Business `if` on domain state in entrypoints (path operations, consumers) | Push the rule back into the aggregate |
| Business rules in the service layer (`if order.status == "DRAFT"`) | Service layer orchestrates only; rules live on the domain |
| Callers poking at aggregate attributes via setters | Behavior methods on the root (e.g. `allocate`) that enforce invariants with the data |
| Pydantic models for internal domain value objects | `frozen=True` dataclass/attrs; pydantic reserved for boundary DTOs |
| Referencing other aggregates by direct object reference | Reference by ID only — the aggregate is the consistency boundary |
| UoW committing implicitly or exposing the raw session | Context manager that rolls back by default; explicit `commit()` |
| Silently retrying/clobbering concurrent aggregate writes | Optimistic version check — fail loudly on `rowcount == 0` |
| One-method, no-field domain service classes | A plain module-level function |
| Speculative ports, boundaries, or DI frameworks up front | Add a boundary when a second adapter or swap/fake need actually appears; manual `bootstrap.py` composition root by default |
| Full onion architecture for Airflow DAGs and ETL glue | Extract pure, unit-testable functions and skip the layers |

## Pre-flight checklist — run before delivering any Python domain/architecture design

When designing or reviewing a Python domain model or service layer, verify:

- [ ] **Dependency rule**: Domain package imports nothing from infrastructure or frameworks
- [ ] **Ports**: Defined as `typing.Protocol` (or plain duck typing) at the point of use, not a grab-bag interfaces module
- [ ] **ORM direction**: The ORM maps to the domain model (classical `mapper`), not the reverse
- [ ] **Value objects**: `frozen=True` dataclass/attrs for internal VOs; pydantic reserved for boundary DTOs
- [ ] **Entities/aggregates**: Identity-based equality; invariants enforced on the aggregate root, not via setters
- [ ] **Concurrency**: Aggregate mutations protected by an explicit version/optimistic-lock check
- [ ] **Repository + UoW**: UoW is a context manager, rolls back by default, commits only on explicit `commit()`
- [ ] **Service layer**: Orchestrates only — no business rules; business rules live on the domain
- [ ] **Entrypoints**: FastAPI routers / Kafka consumers are thin — parse, delegate, translate errors
- [ ] **DI**: Manual composition root (`bootstrap.py` + `functools.partial`) is the default; a DI framework only for genuinely deep, mixed-lifetime dependency graphs
- [ ] **Justification**: Every aggregate/repository/extra layer added can name the concrete invariant or swap-need it solves
- [ ] **Airflow/ETL**: Business logic lives in plain functions outside the DAG file; DAG files stay orchestration-only
