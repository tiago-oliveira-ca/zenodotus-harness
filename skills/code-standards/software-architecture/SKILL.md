---
name: software-architecture
description: >
  Guides software design and architecture decisions using DDD, SOLID, Clean Code, Clean
  Architecture, and Design Patterns. Use when the user asks to design a feature, model a domain,
  define layer boundaries, choose a design pattern, refactor toward clean architecture, or
  review architectural correctness. Trigger on: "design this properly", "make this
  production-ready", "how should I structure this", "is this good architecture", domain
  modeling, use case design, aggregate design, dependency inversion, or architecture review. Do
  NOT trigger for routine bug fixes or single-file edits with no architectural decision — defer
  to the framework-specific skill.
---

# Software Architecture Skill

Use the lightest architecture that solves the problem. Start with the task router below,
then read only the sections and reference files relevant to the task. Do not force DDD,
events, repositories, or extra layers onto simple work that does not need them.

> **Scope boundary.** This skill governs **code structure within a module** (layers,
> aggregates, use cases, repository pattern, SOLID). For **system topology** questions — how
> many deployables, when to split a monolith, where bounded contexts live, when to introduce
> events or microservices — use the top-level `software-architecture-progression` skill
> first (it decides the system shape), then return here to structure the code inside each
> module. The two are complementary.

> **Relationship to language-specific architecture guidance.** Three languages carry their
> own dedicated DDD/Clean Architecture reference that wins over this generic skill for that
> language — read the language-specific file first, and fall back here only for concerns it
> doesn't cover: `code-standards/python/references/ddd-clean-architecture.md` (Python),
> `code-standards/database-data-modeling/oracle-plsql/references/clean-architecture.md`
> (Oracle PL/SQL), and `code-standards/typescript-code-standards/references/angular-clean-architecture.md`
> (Angular/TypeScript).

---

## Quick Reference Map

| Concern | File | Read when |
| --- | --- | --- |
| Domain-Driven Design | [`references/ddd.md`](references/ddd.md) | Modeling aggregates, invariants, bounded contexts, context mapping, subdomain classification, domain events |
| SOLID Principles and Clean Code | [`references/solid-clean-code.md`](references/solid-clean-code.md) | Refactoring classes/functions, reviewing maintainability, tightening interfaces |
| Clean Architecture layers | [`references/clean-architecture.md`](references/clean-architecture.md) | Clarifying boundaries, dependency direction, ports/adapters, composition root |
| Design Patterns catalogue | [`references/design-patterns.md`](references/design-patterns.md) | Solving a specific creation, structural, or behavioral problem without inventing a pattern |

Load only the files you need. For simple refactors or reviews, start with
`solid-clean-code.md` and `clean-architecture.md`. For rich domain work, add `ddd.md`.

---

## Task Router

Choose one path before writing code or review comments.

- **Lightweight change**: Use for CRUD work, isolated behavior changes, thin orchestration,
  or framework-specific tasks that do not need new architectural boundaries. Preserve the
  existing structure unless the structure is the problem.
- **Rich domain feature**: Use when the task has real business invariants, aggregate
  consistency, transactional rules, or long-lived domain concepts. Read `ddd.md` and
  `clean-architecture.md` first.
- **Architectural refactor**: Use when the goal is to improve boundaries, dependency
  direction, testability, or separation of concerns without changing behavior. Start with
  `clean-architecture.md` and `solid-clean-code.md`.
- **Architecture review**: Use when reviewing code or a design for architectural quality.
  Focus on boundary leaks, misplaced business logic, hidden coupling, dependency direction,
  and testing gaps. Start with `clean-architecture.md` and `solid-clean-code.md`.

Escalate to the rich domain path only when the problem justifies it. If the request is
simple and the current code is serviceable, do not introduce aggregates, domain events,
repository abstractions, or extra layers just because they exist in this skill.

---

## Core Mental Model

Always ask these questions before changing structure or behavior:

1. **What domain concept does this represent?** → Name it precisely (DDD Ubiquitous Language)
2. **Which layer does it live in?** → Domain / Application / Infrastructure / Presentation
3. **Who depends on whom?** → Dependencies point inward; domain has zero external deps
4. **What is the single responsibility?** → One reason to change
5. **What is the simplest design that preserves clarity?** → Add complexity only with evidence
6. **What pattern fits, if any?** → Do not invent; apply one only when a concrete force exists

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│         (Controllers, CLI, REST handlers, gRPC)             │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│      (Use Cases / Application Services / Commands/Queries)  │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│  (Entities, Value Objects, Aggregates, Domain Services,     │
│   Domain Events, Repository Interfaces, Policies)           │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│  (DB Adapters, Kafka, HTTP clients, Repository Impls,       │
│   ORM Mappers, External Service Adapters)                   │
└─────────────────────────────────────────────────────────────┘
         Dependency Rule: outer layers depend on inner layers.
         Inner layers NEVER import from outer layers.
```

---

## Lightweight Change Path

Use this path unless the task clearly needs richer modeling.

- Preserve existing module and package boundaries unless they are causing the problem.
- Prefer a small, explicit service/module/function over introducing new architectural layers.
- Add abstractions at external or volatile boundaries, not around stable local code.
- Keep framework concerns out of the core logic, but do not build a full domain model for
  simple data movement or validation.
- If you are tempted to add an aggregate, repository, or domain event, state the invariant
  or coupling problem it solves first. If you cannot, do not add it.

---

## Rich-Domain Workflow

Use this workflow only when domain complexity justifies it.

### Step 1 — Understand the Domain

- Identify the **Bounded Context** and **Aggregate Root**
- Define the **Ubiquitous Language**: write a mini-glossary for the domain concepts involved
- Decide which **Entities** carry identity and which concepts are **Value Objects**
- Read `references/ddd.md` for full rules

### Step 2 — Model the Domain Layer

- Create Entities and Value Objects with **no framework dependencies**
- Enforce invariants in constructors/factory methods (never allow invalid state)
- Define **Repository interfaces** (not implementations) in the domain layer
- Raise **Domain Events** for side effects rather than calling them directly
- Example skeleton:

```python
# Imports and supporting types omitted for brevity.

class DomainError(Exception):
    """Base type for domain-level failures."""


class InvalidMoneyAmount(DomainError):
    """Raised when Money would enter an invalid state."""


# Domain layer — zero external dependencies
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise InvalidMoneyAmount("Amount cannot be negative")

class Order:  # Aggregate Root
    def __init__(self, order_id: OrderId, customer_id: CustomerId):
        self._id = order_id
        self._customer_id = customer_id
        self._items: list[OrderItem] = []
        self._events: list[DomainEvent] = []

    @classmethod
    def create(cls, order_id: OrderId, customer_id: CustomerId) -> "Order":
        order = cls(order_id, customer_id)
        order._events.append(OrderCreated(order_id, customer_id))
        return order

    @property
    def id(self) -> OrderId:
        return self._id

    def add_item(self, product_id: ProductId, quantity: int, price: Money) -> None:
        if quantity <= 0:
            raise DomainError("Quantity must be positive")
        self._items.append(OrderItem(product_id, quantity, price))
        self._events.append(OrderItemAdded(self._id, product_id, quantity))

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
```

### Step 3 — Define the Use Case (Application Layer)

- One class per use case; name it as a verb phrase: `PlaceOrder`, `CancelOrder`
- Orchestrates domain objects and infrastructure through **interfaces only**
- Handles transactions and orchestration; never contains business logic
- Dependencies (like repositories) are injected at the **Composition Root / Main**
- Read `references/clean-architecture.md` for full rules

```python
class PlaceOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        event_bus: EventBus,
        order_ids: OrderIdGenerator,
    ):
        self._order_repo = order_repo
        self._event_bus = event_bus
        self._order_ids = order_ids

    def execute(self, cmd: PlaceOrderCommand) -> OrderId:
        order = Order.create(
            order_id=self._order_ids.next(),
            customer_id=cmd.customer_id,
        )
        for item in cmd.items:
            order.add_item(item.product_id, item.quantity, item.price)
        self._order_repo.save(order)
        self._event_bus.publish(order.pull_events())
        return order.id
```

### Step 4 — Implement Infrastructure

- Implement repository interfaces defined in the domain
- Use mappers to convert between domain objects and persistence models
- Never let ORM models bleed into the domain layer
- Read `references/clean-architecture.md#infrastructure-layer`

### Step 5 — Apply SOLID & Clean Code

- Review each class against SOLID before committing
- Apply the **Boy Scout Rule**: leave code cleaner than you found it
- Read `references/solid-clean-code.md` for full checklist

### Step 6 — Select Design Patterns

- Identify structural and behavioral needs
- Apply patterns from the catalogue only when a concrete force exists
- Read `references/design-patterns.md` for pattern selection guide

---

## Architecture Review Path

Use this path when the task is a review instead of an implementation.

1. Identify the intended domain concepts and current boundaries.
2. Check dependency direction and layer leaks.
3. Check whether business logic lives in the right place.
4. Check whether abstractions are justified or accidental.
5. Check whether tests protect invariants, orchestration, and adapter behavior.
6. Report findings ordered by severity, with file references and the concrete consequence.

Prioritize these failure modes:

- Domain code importing framework or infrastructure concerns
- Controllers, handlers, repositories, or adapters containing business rules
- Application services growing into god objects or workflow scripts with hidden policy
- Interfaces that exist only to satisfy a pattern, not a real boundary
- Missing tests around invariants, transactions, or adapter contracts

---

## Non-Negotiable Rules (apply always)

### Naming

- Names must be **intention-revealing** and follow the language or repo convention:
  `calculate_total_order_value()` in Python, `calculateTotalOrderValue()` in TypeScript,
  never just `calc()`
- Avoid noise words: `OrderData`, `OrderInfo`, `OrderObject` → just `Order`
- Use domain language everywhere; align with the Ubiquitous Language

### Functions

- Do one thing; if you need "and" to describe it, split it
- Max ~20 lines; if longer, extract
- No side effects in query methods (Command-Query Separation)
- No boolean parameters — use enums or separate methods

### Classes

- Small and focused; if the class description needs "and", split it
- Prefer **composition over inheritance**
- Depend on **abstractions, not concretions** (DIP)

### Error Handling

- Use **domain-specific exceptions** (`InsufficientInventoryError` not `ValueError`)
- Never use exceptions for flow control
- Fail fast: validate at system/aggregate boundaries

### Tests

- Every use case must have a unit test (no infrastructure)
- Every aggregate must have tests that verify invariants
- Repository implementations (Infrastructure) must be verified with **Integration Tests** against a real or containerized database
- When taking the lightweight path, test the behavior at the seam you changed; do not create
  extra test layers without a matching architectural seam
- Name tests: `test_given_<context>_when_<action>_then_<expected>()`

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Forcing aggregates, domain events, or repositories onto simple work | Use the lightest architecture that solves the problem; state the invariant or coupling problem an abstraction solves before adding it |
| Domain code importing framework or infrastructure concerns | Domain layer has zero external deps; dependencies point inward |
| Business rules in controllers, handlers, repositories, or adapters | Keep business logic in the domain layer |
| Application services growing into god objects or workflow scripts with hidden policy | One class per use case; use cases orchestrate only, never contain business logic |
| Interfaces that exist only to satisfy a pattern | Add abstractions at external or volatile boundaries, not around stable local code |
| Noise-word names (`OrderData`, `OrderInfo`, `OrderObject`) or vague names (`calc()`) | Intention-revealing names from the Ubiquitous Language (`Order`, `calculate_total_order_value()`) |
| Functions that need "and" to describe them, or exceed ~20 lines | Do one thing; split and extract |
| Boolean parameters | Enums or separate methods |
| Side effects in query methods | Command-Query Separation |
| Inheritance-first class design | Prefer composition over inheritance |
| Generic exceptions (`ValueError`) for domain failures | Domain-specific exceptions (`InsufficientInventoryError`) |
| Exceptions used for flow control | Fail fast; validate at system/aggregate boundaries |
| `new ConcreteClass()` inside business logic | Depend on abstractions; inject at the Composition Root |
| ORM models bleeding into the domain layer | Mappers between domain objects and persistence models |
| Calling side effects directly from the domain | Raise domain events instead |

---

## Pre-flight checklist — run before delivering any architecture design

Before finalizing any code, verify:

- [ ] All domain concepts have precise names from the Ubiquitous Language
- [ ] Domain layer has zero imports from infrastructure or application layers
- [ ] Each class has a single responsibility
- [ ] All interfaces follow Interface Segregation (no fat interfaces)
- [ ] Dependencies flow inward (Dependency Rule respected)
- [ ] Repository implementations are in infrastructure, interfaces in domain
- [ ] No `new ConcreteClass()` inside business logic (use DI)
- [ ] All invariants enforced in the domain model
- [ ] No business logic in controllers or repositories
- [ ] Domain events raised instead of direct side-effect calls
- [ ] Each function does one thing and is named accordingly
- [ ] No magic numbers or strings; use constants/value objects
- [ ] Error types are domain-specific and meaningful
- [ ] All public methods have clear intent from their name alone
- [ ] The chosen design is no more complex than the problem requires
