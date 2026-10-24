# Domain-Driven Design (DDD) Reference

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Bounded Contexts](#bounded-contexts)
3. [Context Mapping](#context-mapping)
4. [Ubiquitous Language](#ubiquitous-language)
5. [Subdomain Classification](#subdomain-classification)
6. [Building Blocks](#building-blocks)
7. [Aggregates](#aggregates)
8. [Domain Events](#domain-events)
9. [Repositories](#repositories)
10. [Domain Services](#domain-services)
11. [Anti-Corruption Layer](#anti-corruption-layer)
12. [Common Mistakes](#common-mistakes)

---

## Core Concepts

DDD is about making the **software model reflect the business domain** as closely as possible. The structure and language of the code should match the mental model of domain experts.

**Strategic Design** (big picture): Bounded Contexts, Context Maps, Ubiquitous Language  
**Tactical Design** (code level): Entities, Value Objects, Aggregates, Domain Events, Repositories, Domain Services

---

## Bounded Contexts

A Bounded Context is a **clear boundary within which a domain model applies**. The same word can mean different things in different contexts.

```
Ordering Context     | Inventory Context   | Shipping Context
---------------------|---------------------|------------------
Product (price, desc)| Product (SKU, qty)  | Product (weight)
Customer (billing)   | Customer (----)     | Customer (address)
Order (items, total) | Order (------)      | Order (tracking)
```

**Rules:**
- Each Bounded Context has its own model, its own database schema, its own codebase
- Communication between contexts happens via **published Domain Events** or **ACL (Anti-Corruption Layer)**
- Never share domain models across bounded contexts — translate via DTOs or events

---

## Context Mapping

Once there are multiple Bounded Contexts, document how they relate. Six recurring patterns:

| Pattern | Meaning |
|---|---|
| **Shared Kernel** | Two contexts deliberately share a small subset of the model. High coordination cost — use sparingly. |
| **Customer/Supplier** | Downstream depends on upstream; upstream considers downstream's needs in its planning. |
| **Conformist** | Downstream just accepts the upstream model as-is, no translation. |
| **Anti-Corruption Layer** | Downstream translates the upstream model into its own terms rather than conforming. |
| **Open Host Service** | Upstream exposes a well-defined protocol/API for many consumers. |
| **Partnership** | Two teams evolve their contexts together, tightly coordinated. |

Drawing this map early prevents a "distributed monolith" — contexts technically separate but
hopelessly coupled in practice.

---

## Ubiquitous Language

A shared, precise vocabulary used **consistently** in code, tests, documentation, and conversations with domain experts.

**How to build it:**
1. Talk to domain experts and extract their terms
2. Create a glossary for each Bounded Context
3. Name every class, method, and variable using those exact terms
4. When experts change their language, refactor the code

**Example:**
```python
# ❌ Generic / technical naming
def process(data):
    result = calc(data.qty * data.p)

# ✅ Ubiquitous Language
def fulfill_order(order: Order) -> FulfillmentResult:
    total_value = order.calculate_total_value()
```

---

## Subdomain Classification

Not every part of the domain deserves the same investment. Classify each subdomain before
modeling it:

- **Core Domain** — what actually differentiates the business. Model this deeply; invest the most
  design/engineering effort here.
- **Supporting Subdomain** — necessary to run the business but not a differentiator. A simpler
  model is fine.
- **Generic Subdomain** — a solved problem elsewhere (authentication, payments, email delivery).
  Buy or integrate an existing solution rather than modeling it from scratch; wrap it with an
  Anti-Corruption Layer if needed.

A common failure mode: over-engineering a Generic Subdomain (a bespoke auth system) while
under-investing in the actual Core Domain.

---

## Building Blocks

### Entity
Has a **unique identity** that persists through state changes.
- Identity is what makes two entities "the same" — not their attributes
- Can be mutable (state changes over its lifecycle)
- Use a **strongly typed ID** (never raw strings/ints)

```python
@dataclass
class ProductId:
    value: UUID

class Product:  # Entity
    def __init__(self, product_id: ProductId, name: str, price: Money):
        self._id = product_id
        self._name = name
        self._price = price

    def __eq__(self, other):
        return isinstance(other, Product) and self._id == other._id

    def reprice(self, new_price: Money) -> None:
        if new_price.amount <= 0:
            raise DomainError("Price must be positive")
        self._price = new_price
```

### Value Object
Defined entirely by its **attributes**, no identity. Always **immutable**.
- Two Value Objects with the same attributes are equal
- Replace entire object instead of mutating
- Great for: Money, Address, DateRange, Email, Coordinates, Quantity

```python
@dataclass(frozen=True)
class Address:
    street: str
    city: str
    postal_code: str
    country: str

    def __post_init__(self):
        if not self.postal_code:
            raise ValueError("Postal code is required")

    def is_domestic(self, country_code: str) -> bool:
        return self.country == country_code
```

### Factory
Encapsulates **complex creation logic** for Entities or Aggregates.
- Enforces all invariants at creation time
- Named with domain language: `Order.create_from_cart()` not `OrderFactory.make()`
- Use class methods or dedicated Factory classes

```python
class Order:
    @classmethod
    def create(cls, customer: Customer, currency: Currency) -> "Order":
        if not customer.is_active():
            raise DomainError("Inactive customers cannot place orders")
        order_id = OrderId(uuid4())
        return cls(order_id, customer.id, currency)
```

---

## Aggregates

An Aggregate is a **cluster of domain objects treated as a single unit** with one **Aggregate Root** that controls all access and enforces invariants across the cluster.

### Rules
1. **Reference other aggregates by ID only** — never hold a direct object reference
2. **All mutations go through the Aggregate Root** — never modify child entities directly
3. **Aggregate boundaries == transaction boundaries** — one transaction per aggregate
4. **Keep aggregates small** — if an aggregate is large, it probably should be split
5. Save/load the entire aggregate at once

```python
class Cart:  # Aggregate Root
    def __init__(self, cart_id: CartId, customer_id: CustomerId):
        self._id = cart_id
        self._customer_id = customer_id  # Reference by ID, not Customer object
        self._lines: dict[ProductId, CartLine] = {}

    def add_product(self, product_id: ProductId, quantity: Quantity, price: Money) -> None:
        if product_id in self._lines:
            self._lines[product_id] = self._lines[product_id].increase_quantity(quantity)
        else:
            self._lines[product_id] = CartLine(product_id, quantity, price)

    def remove_product(self, product_id: ProductId) -> None:
        if product_id not in self._lines:
            raise DomainError("Product not in cart")
        del self._lines[product_id]

    def checkout(self) -> list[DomainEvent]:
        if not self._lines:
            raise DomainError("Cannot checkout an empty cart")
        return [CartCheckedOut(self._id, self._customer_id, list(self._lines.values()))]
```

---

## Domain Events

A Domain Event represents **something that happened in the domain** — immutable facts.

### Rules
- Named in the **past tense**: `OrderPlaced`, `PaymentFailed`, `InventoryDepleted`
- Contain only data relevant to the event (no behavior)
- Published **after** the aggregate operation succeeds
- Handled by Application Services or Event Handlers outside the aggregate

```python
@dataclass(frozen=True)
class OrderPlaced:
    event_id: UUID
    occurred_at: datetime
    order_id: OrderId
    customer_id: CustomerId
    total_amount: Money

    @classmethod
    def create(cls, order_id: OrderId, customer_id: CustomerId, total: Money) -> "OrderPlaced":
        return cls(
            event_id=uuid4(),
            occurred_at=datetime.utcnow(),
            order_id=order_id,
            customer_id=customer_id,
            total_amount=total,
        )
```

**Publishing pattern (collect then publish):**
```python
# In the aggregate
def _raise_event(self, event: DomainEvent) -> None:
    self._uncommitted_events.append(event)

# In the application service
order.place(...)
self._order_repo.save(order)
self._event_bus.publish(order.pull_uncommitted_events())
```

---

## Repositories

A Repository provides a **collection-like interface** for accessing aggregates. It abstracts the persistence mechanism.

### Rules
- Interface defined in the **domain layer**
- Implementation lives in the **infrastructure layer**
- One repository per Aggregate Root
- Methods speak domain language: `find_by_customer`, `find_pending_orders` — not SQL

```python
# Domain layer — interface only
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None: ...

    @abstractmethod
    def find_by_id(self, order_id: OrderId) -> Optional[Order]: ...

    @abstractmethod
    def find_pending_by_customer(self, customer_id: CustomerId) -> list[Order]: ...

# Infrastructure layer — implementation
class SqlOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self._session = session

    def save(self, order: Order) -> None:
        record = OrderMapper.to_record(order)
        self._session.merge(record)

    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        record = self._session.get(OrderRecord, order_id.value)
        return OrderMapper.to_domain(record) if record else None
```

---

## Domain Services

Use a Domain Service when **a domain operation doesn't naturally belong to any single Entity or Value Object** and involves multiple domain objects.

```python
class PricingService:
    """Calculates the final price applying customer tier discounts and promotions."""

    def calculate_final_price(
        self,
        product: Product,
        customer_tier: CustomerTier,
        active_promotions: list[Promotion],
    ) -> Money:
        base_price = product.price
        discounted = customer_tier.apply_discount(base_price)
        return self._apply_best_promotion(discounted, active_promotions)
```

**Not a Domain Service**: operations that only need one entity should be methods on that entity.

---

## Anti-Corruption Layer (ACL)

Protects your domain model from **external system concepts leaking in**.

```python
# External system returns a raw dict/legacy format
class LegacyInventoryAdapter:
    def __init__(self, legacy_client: LegacyInventoryClient):
        self._client = legacy_client

    def get_available_quantity(self, sku: SKU) -> Quantity:
        raw = self._client.check_stock(sku.value)  # Returns {"QTY_ON_HAND": 50, ...}
        return Quantity(raw["QTY_ON_HAND"] - raw.get("QTY_RESERVED", 0))
```

---

## Common DDD Mistakes

| Mistake | Correct Approach |
|---|---|
| Anemic domain model (entities are just data bags) | Put behavior and invariants IN the entities |
| Repositories with `find_all()` that return everything | Add specific, domain-meaningful query methods |
| Sharing entity objects across bounded contexts | Translate to DTOs or use domain events |
| Multiple aggregates in one transaction | Redesign aggregate boundaries |
| Business logic in application services | Move it to the domain model |
| Using ORM models as domain objects | Keep ORM models in infra; use mappers |
| Fat constructors with no validation | Enforce all invariants at construction time |
| Modeling a Generic Subdomain as deeply as the Core Domain | Reserve deep modeling effort for the Core Domain |
| Domain events published before the transaction commits | Collect events on the aggregate, publish after persistence succeeds |
