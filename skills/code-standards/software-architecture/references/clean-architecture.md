# Clean Architecture Reference

## Table of Contents
1. [The Dependency Rule](#the-dependency-rule)
2. [Layers Overview](#layers-overview)
3. [Domain Layer](#domain-layer)
4. [Application Layer](#application-layer)
5. [Infrastructure Layer](#infrastructure-layer)
6. [Presentation Layer](#presentation-layer)
7. [Crossing Layer Boundaries](#crossing-layer-boundaries)
8. [CQRS Pattern](#cqrs-pattern)
9. [Project Structure](#project-structure)
10. [Dependency Injection & Composition Root](#dependency-injection--composition-root)

---

## The Dependency Rule

> "Source code dependencies must point only inward, toward higher-level policies."

The domain (innermost) layer knows nothing about the application layer, which knows nothing about infrastructure, which knows nothing about the presentation layer.

```
Presentation  →  Application  →  Domain  ←  (no outward arrows)
     ↓                ↓
Infrastructure  →  Application  →  Domain
```

**Practical enforcement:**
- The `domain` package imports nothing from `application`, `infrastructure`, or `presentation`
- The `application` package imports from `domain` only
- The `infrastructure` package imports from `domain` and `application` (to implement interfaces)
- The `presentation` package imports from `application` only

---

## Layers Overview

```
┌──────────────────────────────────────────┐
│          Presentation Layer              │
│  REST API, CLI, gRPC, GraphQL, Events    │
│  - Maps HTTP/CLI input → Commands/Queries│
│  - Maps Results → HTTP responses/output  │
└──────────────┬───────────────────────────┘
               │ Command/Query DTOs
┌──────────────▼───────────────────────────┐
│          Application Layer               │
│  Use Cases (Commands + Queries)          │
│  - Orchestrates domain objects           │
│  - Manages transactions                  │
│  - Publishes domain events               │
└──────────────┬───────────────────────────┘
               │ Domain interfaces
┌──────────────▼───────────────────────────┐
│            Domain Layer                  │
│  Entities, Aggregates, Value Objects     │
│  Domain Events, Domain Services          │
│  Repository Interfaces                   │
│  NO external dependencies                │
└──────────────┬───────────────────────────┘
               │ Implemented by
┌──────────────▼───────────────────────────┐
│         Infrastructure Layer             │
│  DB Adapters, ORM, Kafka, HTTP clients   │
│  Repository Implementations              │
│  External Service Adapters, ACL          │
└──────────────────────────────────────────┘
```

---

## Domain Layer

**Contains:** Entities, Value Objects, Aggregates, Domain Events, Domain Services, Repository interfaces, Specification objects, Domain Exceptions

**Rules:**
- **Zero** external dependencies (no ORM, no frameworks, no HTTP)
- All business rules enforced here
- Rich model: behavior lives on the objects, not in services

**What does NOT belong here:**
- Persistence logic (`session.save()`)
- Email or messaging
- HTTP calls
- Logging frameworks
- Any `import sqlalchemy`, `import django`, etc.

```
domain/
├── model/
│   ├── order/
│   │   ├── order.py           # Aggregate root
│   │   ├── order_item.py      # Entity within aggregate
│   │   ├── order_id.py        # Value object
│   │   └── events.py          # Domain events for this aggregate
│   └── product/
│       ├── product.py
│       └── money.py
├── repository/
│   ├── order_repository.py    # Interface (ABC)
│   └── product_repository.py
├── service/
│   └── pricing_service.py     # Domain service
└── exceptions.py
```

---

## Application Layer

**Contains:** Use Cases (Application Services), Command/Query objects, DTOs, Application Events, Transaction management

**Rules:**
- Orchestrates domain objects — no business logic itself
- Calls repository interfaces (never implementations)
- Manages the transaction boundary
- Publishes domain events after state changes persist
- Returns DTOs (not domain objects) to callers

```python
# application/use_cases/place_order.py

@dataclass
class PlaceOrderCommand:
    customer_id: UUID
    items: list[OrderItemDTO]

@dataclass
class PlaceOrderResult:
    order_id: UUID
    total_amount: Decimal
    currency: str

class PlaceOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        event_bus: EventBus,
    ):
        self._order_repo = order_repo
        self._product_repo = product_repo
        self._event_bus = event_bus

    def execute(self, cmd: PlaceOrderCommand) -> PlaceOrderResult:
        # 1. Load required domain objects
        products = {
            item.product_id: self._product_repo.find_by_id(ProductId(item.product_id))
            for item in cmd.items
        }

        # 2. Execute domain logic
        order = Order.create(CustomerId(cmd.customer_id))
        for item_dto in cmd.items:
            product = products[item_dto.product_id]
            order.add_item(product.id, Quantity(item_dto.quantity), product.price)

        # 3. Persist (transaction commits here)
        self._order_repo.save(order)

        # 4. Publish events
        self._event_bus.publish(order.pull_uncommitted_events())

        # 5. Return DTO (not domain object)
        return PlaceOrderResult(
            order_id=order.id.value,
            total_amount=order.total.amount,
            currency=order.total.currency,
        )
```

---

## Infrastructure Layer

**Contains:** Repository implementations, ORM models & mappers, Kafka/messaging adapters, HTTP client adapters, Email/SMS senders, Cache adapters, Database migrations

**Rules:**
- Implements interfaces defined in the domain layer
- Translates between domain objects and external models via **Mappers**
- ORM models NEVER used outside this layer
- Never contains business logic

```python
# infrastructure/persistence/sql_order_repository.py

class SqlOrderRepository(OrderRepository):  # Implements domain interface
    def __init__(self, session: Session):
        self._session = session

    def save(self, order: Order) -> None:
        record = OrderRecord(
            id=str(order.id.value),
            customer_id=str(order.customer_id.value),
            status=order.status.value,
            total_amount=order.total.amount,
            currency=order.total.currency,
        )
        lines = [
            OrderLineRecord(
                order_id=record.id,
                product_id=str(line.product_id.value),
                quantity=line.quantity.value,
                unit_price=line.unit_price.amount,
            )
            for line in order.lines
        ]
        self._session.merge(record)
        for line_record in lines:
            self._session.merge(line_record)

    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        record = (
            self._session.query(OrderRecord)
            .options(joinedload(OrderRecord.lines))
            .filter_by(id=str(order_id.value))
            .first()
        )
        return OrderMapper.to_domain(record) if record else None
```

---

## Presentation Layer

**Contains:** REST controllers, CLI commands, gRPC handlers, GraphQL resolvers, Event consumers (as entry points), Request/Response schemas

**Rules:**
- Translates incoming requests into Commands/Queries
- Calls Application Layer use cases
- Translates results into responses
- NO business logic
- NO domain knowledge

The shape below is framework-agnostic: it applies equally to a REST controller, a CLI
command, a gRPC handler, or a GraphQL resolver — only the request/response transport
differs. An entrypoint parses input into a Command/Query, calls exactly one use case, and
translates the outcome (success or domain/application error) into a transport-level
response. Nothing about the domain leaks past this boundary.

```text
# presentation/api/order_endpoint.pseudo

entrypoint POST /orders(request: PlaceOrderRequest) -> OrderResponse:
    use_case = resolve(PlaceOrderUseCase)          # wired at the Composition Root

    try:
        command = PlaceOrderCommand(
            customer_id: request.customer_id,
            items: [ItemDTO(i.product_id, i.quantity) for i in request.items],
        )
        result = use_case.execute(command)
        return respond(status: CREATED, body: OrderResponse.from(result))

    except InsufficientInventoryError as e:
        return respond(status: CONFLICT, body: ErrorResponse(str(e)))
    except DomainError as e:
        return respond(status: UNPROCESSABLE, body: ErrorResponse(str(e)))
```

For a concrete FastAPI realization of this layer — `APIRouter`, `Depends`, `HTTPException`,
and Pydantic request/response schemas — see `code-standards/python/frameworks/fastapi.md`
(§5 Dependency Injection, §6 Routing & API Design, §9 Error Handling).

---

## Crossing Layer Boundaries

Data crosses boundaries via **DTOs** (Data Transfer Objects) — plain data structures with no behavior.

```
HTTP Request JSON
      ↓ (parsed by Pydantic model in Presentation)
PlaceOrderRequest (Pydantic schema — Presentation layer)
      ↓ (mapped by controller)
PlaceOrderCommand (dataclass — Application layer)
      ↓ (use case creates domain objects)
Order, OrderItem (domain objects — Domain layer)
      ↓ (repo mapper translates)
OrderRecord, OrderLineRecord (ORM model — Infrastructure layer)
      ↓ (SQL → database)
```

Each arrow = a mapping step. Never shortcut — keep layers clean.

---

## CQRS Pattern

Separate the **write model** (Commands) from the **read model** (Queries).

**Commands** (write side):
- Go through the full DDD/Clean Architecture stack
- Return void or a minimal result (ID, status)
- Enforce all business rules

**Queries** (read side):
- Can bypass the domain model entirely
- Query the read store directly (SQL, Elasticsearch, etc.)
- Return **View Models** (optimized for the UI/API consumer)
- No validation, no invariants — just data retrieval

```python
# Write side: full stack
class CancelOrderUseCase:
    def execute(self, cmd: CancelOrderCommand) -> None:
        order = self._order_repo.find_by_id(OrderId(cmd.order_id))
        order.cancel(reason=CancellationReason(cmd.reason))
        self._order_repo.save(order)
        self._event_bus.publish(order.pull_uncommitted_events())

# Read side: direct query, no domain objects
class OrderSummaryQuery:
    def __init__(self, db: Database):
        self._db = db

    def find_for_customer(self, customer_id: UUID) -> list[OrderSummaryView]:
        rows = self._db.execute(
            "SELECT id, status, total_amount, created_at "
            "FROM orders WHERE customer_id = :cid ORDER BY created_at DESC",
            {"cid": str(customer_id)},
        )
        return [OrderSummaryView(**row) for row in rows]
```

---

## Project Structure

```
src/
├── domain/                    # Zero external deps
│   ├── model/
│   │   └── <aggregate>/
│   │       ├── <aggregate>.py
│   │       ├── <aggregate>_id.py
│   │       └── events.py
│   ├── repository/            # Interfaces only
│   ├── service/               # Domain services
│   └── exceptions.py
│
├── application/               # Depends on domain only
│   ├── use_cases/
│   │   ├── commands/          # Write use cases
│   │   └── queries/           # Read queries
│   ├── dtos/
│   └── ports/                 # Event bus, email interfaces
│
├── infrastructure/            # Depends on domain + application
│   ├── persistence/
│   │   ├── models/            # ORM models
│   │   ├── mappers/           # Domain ↔ ORM mappers
│   │   └── repositories/      # Repository implementations
│   ├── messaging/             # Kafka, SQS adapters
│   └── external/              # HTTP client adapters, ACL
│
├── presentation/              # Depends on application only
│   ├── api/                   # REST endpoints
│   ├── cli/
│   └── events/                # Event consumer entry points
│
└── main.py                    # Composition root — wires everything
```

---

## Dependency Injection & Composition Root

The **Composition Root** is the single place where all dependencies are wired together. This should be as close to the program entry point as possible.

The pattern is the same regardless of language or framework: construct concrete
infrastructure first, wrap it in the adapters that implement the domain's interfaces, inject
those adapters into use cases via their constructors, then hand the wired use cases to the
presentation layer's entrypoints. Nothing in this wiring order is framework-specific — only
*how* a given framework triggers it (a DI container, a chain of `Depends()` calls, a manual
`main()` function) varies.

```text
# composition_root.pseudo

function build_application():
    # 1. Construct infrastructure — the volatile, replaceable parts
    db_connection  = open_database(config.DATABASE_URL)
    message_broker = connect_broker(config.BROKER_URL)

    # 2. Construct adapters that implement domain/application interfaces
    order_repo = SqlOrderRepository(db_connection)   # implements OrderRepository
    event_bus  = BrokerEventBus(message_broker)      # implements EventBus

    # 3. Inject adapters into use cases via constructor injection only
    place_order_use_case = PlaceOrderUseCase(order_repo, event_bus)

    # 4. Register the wired use cases with the presentation layer's entrypoints
    register_entrypoint("POST /orders", place_order_use_case)

    return application
```

For a concrete FastAPI realization — a `create_app()` factory using chained `Depends()`
providers and `app.include_router()` — see `code-standards/python/frameworks/fastapi.md`
(§5 Dependency Injection, §6 Routing & API Design).
