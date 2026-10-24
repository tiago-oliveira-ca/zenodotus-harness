# Design Patterns Reference

## Table of Contents
1. [Pattern Selection Guide](#pattern-selection-guide)
2. [Creational Patterns](#creational-patterns)
3. [Structural Patterns](#structural-patterns)
4. [Behavioral Patterns](#behavioral-patterns)
5. [Architectural Patterns](#architectural-patterns)
6. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Pattern Selection Guide

Use this quick guide to find the right pattern:

| I need to... | Pattern |
|---|---|
| Create objects without specifying exact class | Factory Method / Abstract Factory |
| Ensure only one instance of a class | Singleton (use with caution) |
| Build complex objects step by step | Builder |
| Copy existing objects | Prototype |
| Add responsibilities to objects dynamically | Decorator |
| Make incompatible interfaces work together | Adapter |
| Simplify a complex subsystem | Facade |
| Share objects to save memory | Flyweight |
| Compose objects into tree structures | Composite |
| Separate abstraction from implementation | Bridge |
| Define a family of algorithms, make them interchangeable | Strategy |
| Define a skeleton algorithm, let subclasses fill steps | Template Method |
| React to state changes in one-to-many relationships | Observer |
| Encapsulate a request as an object | Command |
| Pass requests along a chain of handlers | Chain of Responsibility |
| Access elements of a collection sequentially | Iterator |
| Allow objects to communicate without knowing each other | Mediator |
| Restore an object to a previous state | Memento |
| Change behavior when internal state changes | State |
| Add operations without changing classes | Visitor |
| Defer object creation or access | Proxy |

---

## Creational Patterns

### Factory Method
Define an interface for creating objects; let subclasses decide which class to instantiate.

**When to use:** When you don't know ahead of time what class you need to instantiate, or when subclasses should control object creation.

```python
class NotificationFactory(ABC):
    @abstractmethod
    def create_notifier(self) -> Notifier: ...

    def notify(self, message: str) -> None:  # Template method using factory method
        notifier = self.create_notifier()
        notifier.send(message)

class EmailNotificationFactory(NotificationFactory):
    def create_notifier(self) -> Notifier:
        return EmailNotifier(smtp_config=settings.SMTP)

class SmsNotificationFactory(NotificationFactory):
    def create_notifier(self) -> Notifier:
        return SmsNotifier(twilio_config=settings.TWILIO)
```

---

### Abstract Factory
Produce families of related objects without specifying their concrete classes.

**When to use:** When the system needs to be independent of how products are created, and when you need families of related products.

```python
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...

    @abstractmethod
    def create_dialog(self) -> Dialog: ...

class WindowsUIFactory(UIFactory):
    def create_button(self) -> Button:
        return WindowsButton()

    def create_dialog(self) -> Dialog:
        return WindowsDialog()

class MacOSUIFactory(UIFactory):
    def create_button(self) -> Button:
        return MacButton()

    def create_dialog(self) -> Dialog:
        return MacDialog()
```

---

### Builder
Construct complex objects step by step.

**When to use:** When you need to create an object with many optional components or configurations. Avoids telescoping constructors.

```python
@dataclass
class QueryBuilder:
    _table: str = ""
    _conditions: list[str] = field(default_factory=list)
    _columns: list[str] = field(default_factory=list)
    _limit: Optional[int] = None

    def from_table(self, table: str) -> "QueryBuilder":
        return replace(self, _table=table)

    def select(self, *columns: str) -> "QueryBuilder":
        return replace(self, _columns=list(columns))

    def where(self, condition: str) -> "QueryBuilder":
        return replace(self, _conditions=[*self._conditions, condition])

    def limit(self, n: int) -> "QueryBuilder":
        return replace(self, _limit=n)

    def build(self) -> str:
        cols = ", ".join(self._columns) or "*"
        query = f"SELECT {cols} FROM {self._table}"
        if self._conditions:
            query += " WHERE " + " AND ".join(self._conditions)
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query

# Usage
query = (
    QueryBuilder()
    .from_table("orders")
    .select("id", "status", "total")
    .where("status = 'pending'")
    .where("created_at > '2024-01-01'")
    .limit(100)
    .build()
)
```

---

## Structural Patterns

### Adapter
Convert the interface of a class into another interface that clients expect.

**When to use:** When you need to integrate a third-party library or legacy system with your existing code.

```python
# Target interface (what our domain expects)
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: Money, card_token: str) -> PaymentResult: ...

# Adaptee (third-party library with incompatible interface)
class StripeClient:
    def create_charge(self, amount_cents: int, currency: str, source: str) -> dict: ...

# Adapter
class StripePaymentAdapter(PaymentGateway):
    def __init__(self, stripe_client: StripeClient):
        self._stripe = stripe_client

    def charge(self, amount: Money, card_token: str) -> PaymentResult:
        raw = self._stripe.create_charge(
            amount_cents=int(amount.amount * 100),
            currency=amount.currency.lower(),
            source=card_token,
        )
        return PaymentResult(
            success=raw["status"] == "succeeded",
            transaction_id=raw["id"],
        )
```

---

### Decorator
Attach additional responsibilities to an object dynamically.

**When to use:** When you need to add behavior to individual objects without affecting others, and when inheritance would lead to an explosion of subclasses.

```python
class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: OrderId) -> Optional[Order]: ...
    @abstractmethod
    def save(self, order: Order) -> None: ...

class CachedOrderRepository(OrderRepository):
    def __init__(self, inner: OrderRepository, cache: Cache):
        self._inner = inner
        self._cache = cache

    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        key = f"order:{order_id.value}"
        cached = self._cache.get(key)
        if cached:
            return cached
        order = self._inner.find_by_id(order_id)
        if order:
            self._cache.set(key, order, ttl=300)
        return order

    def save(self, order: Order) -> None:
        self._inner.save(order)
        self._cache.delete(f"order:{order.id.value}")  # Invalidate

class LoggingOrderRepository(OrderRepository):
    def __init__(self, inner: OrderRepository, logger: Logger):
        self._inner = inner
        self._logger = logger

    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        self._logger.debug(f"Finding order {order_id.value}")
        result = self._inner.find_by_id(order_id)
        self._logger.debug(f"Found: {result is not None}")
        return result

    def save(self, order: Order) -> None:
        self._inner.save(order)
        self._logger.info(f"Saved order {order.id.value}")
```

---

### Facade
Provide a simplified interface to a complex subsystem.

**When to use:** When a complex subsystem has many components and you want to expose a simple API to clients.

```python
class CheckoutFacade:
    """Simplified interface to the complex checkout subsystem."""

    def __init__(
        self,
        cart_service: CartService,
        payment_service: PaymentService,
        inventory_service: InventoryService,
        notification_service: NotificationService,
    ):
        self._cart = cart_service
        self._payment = payment_service
        self._inventory = inventory_service
        self._notify = notification_service

    def checkout(self, cart_id: CartId, payment_token: str) -> Order:
        cart = self._cart.get(cart_id)
        self._inventory.reserve(cart.items)
        try:
            payment = self._payment.charge(cart.total, payment_token)
            order = self._cart.convert_to_order(cart, payment)
            self._notify.send_confirmation(order)
            return order
        except PaymentError:
            self._inventory.release(cart.items)
            raise
```

---

## Behavioral Patterns

### Strategy
Define a family of algorithms, encapsulate each one, and make them interchangeable.

**When to use:** When you need to switch algorithms at runtime, or when multiple variants of an algorithm exist.

```python
class ShippingStrategy(ABC):
    @abstractmethod
    def calculate_cost(self, order: Order) -> Money: ...

class StandardShipping(ShippingStrategy):
    def calculate_cost(self, order: Order) -> Money:
        return Money(Decimal("5.99"), order.currency)

class ExpressShipping(ShippingStrategy):
    def calculate_cost(self, order: Order) -> Money:
        return Money(Decimal("14.99"), order.currency)

class FreeShipping(ShippingStrategy):
    MINIMUM_ORDER = Decimal("50.00")

    def calculate_cost(self, order: Order) -> Money:
        if order.total.amount >= self.MINIMUM_ORDER:
            return Money(Decimal("0.00"), order.currency)
        raise ShippingEligibilityError("Order does not qualify for free shipping")

class ShippingCalculator:
    def __init__(self, strategy: ShippingStrategy):
        self._strategy = strategy

    def calculate(self, order: Order) -> Money:
        return self._strategy.calculate_cost(order)
```

---

### Observer
Define a one-to-many dependency so that when one object changes state, all dependents are notified.

**When to use:** For event-driven systems, domain events, notification systems.

```python
class DomainEventBus:
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            for handler in self._handlers.get(type(event), []):
                handler(event)

# Registering handlers
event_bus = DomainEventBus()
event_bus.subscribe(OrderPlaced, send_confirmation_email)
event_bus.subscribe(OrderPlaced, reserve_inventory)
event_bus.subscribe(OrderPlaced, notify_warehouse)
event_bus.subscribe(OrderCancelled, release_inventory)
event_bus.subscribe(OrderCancelled, issue_refund)
```

---

### Command
Encapsulate a request as an object, allowing parameterization, queuing, and undo.

**When to use:** To implement reversible operations, task queues, transactional behavior, or audit logs.

```python
class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...

class ApplyDiscountCommand(Command):
    def __init__(self, order: Order, discount: Discount):
        self._order = order
        self._discount = discount
        self._previous_total: Optional[Money] = None

    def execute(self) -> None:
        self._previous_total = self._order.total
        self._order.apply_discount(self._discount)

    def undo(self) -> None:
        if self._previous_total:
            self._order.reset_total(self._previous_total)

class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo_last(self) -> None:
        if self._history:
            self._history.pop().undo()
```

---

### Chain of Responsibility
Pass requests along a chain of handlers; each handler decides to handle or pass along.

**When to use:** For validation pipelines, middleware chains, approval workflows.

```python
class OrderValidator(ABC):
    def __init__(self):
        self._next: Optional["OrderValidator"] = None

    def set_next(self, validator: "OrderValidator") -> "OrderValidator":
        self._next = validator
        return validator

    def validate(self, order: Order) -> ValidationResult:
        result = self._check(order)
        if not result.is_valid or self._next is None:
            return result
        return self._next.validate(order)

    @abstractmethod
    def _check(self, order: Order) -> ValidationResult: ...

class CustomerActiveValidator(OrderValidator):
    def _check(self, order: Order) -> ValidationResult:
        if not order.customer.is_active:
            return ValidationResult.failure("Customer account is inactive")
        return ValidationResult.success()

class InventoryAvailableValidator(OrderValidator):
    def __init__(self, inventory: InventoryService):
        super().__init__()
        self._inventory = inventory

    def _check(self, order: Order) -> ValidationResult:
        for item in order.items:
            if not self._inventory.is_available(item.product_id, item.quantity):
                return ValidationResult.failure(f"Product {item.product_id} unavailable")
        return ValidationResult.success()

# Building the chain
validator = CustomerActiveValidator()
validator.set_next(InventoryAvailableValidator(inventory_service))
result = validator.validate(order)
```

---

## Architectural Patterns

### Repository Pattern
See `ddd.md` and `clean-architecture.md` for full treatment.

### Specification Pattern
Encapsulate business rules as composable specification objects.

```python
class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool: ...

    def and_(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification":
        return NotSpecification(self)

class PremiumCustomerSpecification(Specification):
    def is_satisfied_by(self, customer: Customer) -> bool:
        return customer.lifetime_value > Money(Decimal("1000"), "USD")

class ActiveCustomerSpecification(Specification):
    def is_satisfied_by(self, customer: Customer) -> bool:
        return customer.is_active

# Usage
eligible_for_discount = (
    PremiumCustomerSpecification()
    .and_(ActiveCustomerSpecification())
)
if eligible_for_discount.is_satisfied_by(customer):
    order.apply_discount(loyalty_discount)
```

### Outbox Pattern
Ensures **reliable event publishing** by writing events to the same database transaction as the state change.

> For the RabbitMQ-specific relay/shovel variant of this pattern, see
> `code-standards/rabbitmq/SKILL.md` §10 (Architectural Patterns).

```python
class OrderRepository:
    def save(self, order: Order) -> None:
        # Save order record
        self._session.merge(OrderMapper.to_record(order))

        # Save events to outbox in the same transaction
        for event in order.pull_uncommitted_events():
            self._session.add(OutboxRecord(
                event_type=type(event).__name__,
                payload=json.dumps(event, cls=DomainEventEncoder),
                created_at=datetime.utcnow(),
                published=False,
            ))
        # Transaction commits atomically — order + events together
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|---|---|---|
| **God Object** | One class that knows/does too much | Split by SRP, extract domain services |
| **Anemic Domain Model** | Entities are dumb data bags; logic in services | Move business rules into entities |
| **Service Locator** | Global registry to fetch dependencies | Constructor injection (DIP) |
| **Spaghetti Code** | Random dependencies, no structure | Apply Clean Architecture layers |
| **Golden Hammer** | Applying the same pattern everywhere | Match pattern to actual problem |
| **Premature Optimization** | Complex patterns before simple code works | Start simple, refactor when needed |
| **Lasagna Code** | Too many thin layers that add no value | Each layer must have a clear responsibility |
| **Singleton Abuse** | Shared mutable state, hidden coupling | Inject dependencies explicitly |
| **Data Transfer Object bloat** | DTOs with behavior (business logic) | Keep DTOs as plain data; behavior in domain |
| **Leaky Abstractions** | Domain model exposed outside application | Use output DTOs; never return domain objects from use cases |
