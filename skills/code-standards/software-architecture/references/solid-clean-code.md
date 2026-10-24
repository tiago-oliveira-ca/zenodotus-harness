# SOLID Principles & Clean Code Reference

## Table of Contents
1. [S — Single Responsibility Principle](#s--single-responsibility-principle)
2. [O — Open/Closed Principle](#o--openclosed-principle)
3. [L — Liskov Substitution Principle](#l--liskov-substitution-principle)
4. [I — Interface Segregation Principle](#i--interface-segregation-principle)
5. [D — Dependency Inversion Principle](#d--dependency-inversion-principle)
6. [Clean Code: Naming](#clean-code-naming)
7. [Clean Code: Functions](#clean-code-functions)
8. [Clean Code: Classes](#clean-code-classes)
9. [Clean Code: Comments](#clean-code-comments)
10. [Clean Code: Error Handling](#clean-code-error-handling)
11. [Clean Code: Tests](#clean-code-tests)

---

## S — Single Responsibility Principle

> "A class should have one, and only one, reason to change."

A **reason to change** means a stakeholder or actor whose requirements can cause the class to change. If two different actors could ask for changes to the same class, it violates SRP.

**Signals of SRP violation:**
- The class name contains "and", "manager", "handler", "helper", or "util"
- The class has more than one group of methods that don't interact
- Changes for one feature require testing unrelated features

```python
# ❌ Multiple responsibilities
class OrderService:
    def place_order(self, cart): ...       # business logic
    def save_order(self, order): ...       # persistence
    def send_confirmation_email(self): ... # notification
    def generate_invoice_pdf(self): ...    # reporting

# ✅ Each class has one responsibility
class OrderPlacementService:
    def place(self, cart: Cart) -> Order: ...

class OrderRepository:
    def save(self, order: Order) -> None: ...

class OrderNotificationService:
    def send_confirmation(self, order: Order) -> None: ...

class InvoiceGenerator:
    def generate(self, order: Order) -> Invoice: ...
```

---

## O — Open/Closed Principle

> "Software entities should be open for extension, but closed for modification."

Extend behavior by **adding new code**, not modifying existing code. Use abstractions (interfaces/abstract classes) to define extension points.

```python
# ❌ Adding new discount type requires modifying this class
class DiscountCalculator:
    def calculate(self, order: Order, discount_type: str) -> Decimal:
        if discount_type == "seasonal":
            return order.total * Decimal("0.10")
        elif discount_type == "loyalty":
            return order.total * Decimal("0.15")
        # Every new type requires modifying this method

# ✅ Add new types by adding new classes
class DiscountPolicy(ABC):
    @abstractmethod
    def calculate(self, order: Order) -> Decimal: ...

class SeasonalDiscount(DiscountPolicy):
    def calculate(self, order: Order) -> Decimal:
        return order.total * Decimal("0.10")

class LoyaltyDiscount(DiscountPolicy):
    def calculate(self, order: Order) -> Decimal:
        return order.total * Decimal("0.15")

class DiscountCalculator:
    def __init__(self, policies: list[DiscountPolicy]):
        self._policies = policies

    def calculate_best(self, order: Order) -> Decimal:
        return max((p.calculate(order) for p in self._policies), default=Decimal("0"))
```

---

## L — Liskov Substitution Principle

> "Objects of a superclass should be replaceable with objects of its subclasses without breaking the program."

If you use a subtype, it must be usable wherever the parent type is expected — with no surprises.

**LSP is violated when a subclass:**
- Throws exceptions the parent doesn't throw
- Returns types or ranges narrower than the parent's contract
- Overrides a method to do nothing (a.k.a. "refuse bequest")
- Requires the caller to know about the concrete type

```python
# ❌ LSP violation: ReadOnlyFile refuses write
class File:
    def write(self, content: str) -> None: ...

class ReadOnlyFile(File):
    def write(self, content: str) -> None:
        raise NotImplementedError("Read-only!")  # Breaks callers that use File

# ✅ Correct hierarchy
class ReadableFile(ABC):
    @abstractmethod
    def read(self) -> str: ...

class WritableFile(ReadableFile, ABC):
    @abstractmethod
    def write(self, content: str) -> None: ...

class ReadOnlyFile(ReadableFile):
    def read(self) -> str: ...  # Fine — doesn't pretend to be writable

class MutableFile(WritableFile):
    def read(self) -> str: ...
    def write(self, content: str) -> None: ...
```

---

## I — Interface Segregation Principle

> "Clients should not be forced to depend upon interfaces they do not use."

Prefer **many small, focused interfaces** over one large general-purpose interface. A class implementing an interface should use all methods it declares.

```python
# ❌ Fat interface — implementors must stub methods they don't need
class Worker(ABC):
    @abstractmethod
    def work(self): ...
    @abstractmethod
    def eat(self): ...
    @abstractmethod
    def sleep(self): ...

class Robot(Worker):
    def work(self): ...
    def eat(self): raise NotImplementedError  # Robots don't eat
    def sleep(self): raise NotImplementedError

# ✅ Segregated interfaces
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Breakable(ABC):
    @abstractmethod
    def eat(self): ...
    @abstractmethod
    def sleep(self): ...

class Human(Workable, Breakable):
    def work(self): ...
    def eat(self): ...
    def sleep(self): ...

class Robot(Workable):
    def work(self): ...  # Only implements what it actually does
```

---

## D — Dependency Inversion Principle

> "High-level modules should not depend on low-level modules. Both should depend on abstractions."

**High-level** = business logic. **Low-level** = I/O, databases, frameworks.  
Define abstractions (interfaces) in the domain/application layer. Wire up concrete implementations externally (Dependency Injection).

```python
# ❌ High-level use case depends directly on low-level PostgreSQL adapter
class PlaceOrderUseCase:
    def __init__(self):
        self._repo = PostgresOrderRepository()  # Concrete dep — hard to test/swap

# ✅ Depend on abstraction; inject the implementation
class PlaceOrderUseCase:
    def __init__(self, order_repo: OrderRepository, event_bus: EventBus):
        self._order_repo = order_repo  # Interface defined in domain
        self._event_bus = event_bus

# Wiring happens in composition root (main / DI container)
use_case = PlaceOrderUseCase(
    order_repo=PostgresOrderRepository(session),
    event_bus=KafkaEventBus(producer),
)
```

**Practical DI patterns:**
- **Constructor injection** (preferred): dependencies declared in `__init__`
- **Factory injection**: pass a factory callable when object creation is lazy
- **Avoid service locators**: they hide dependencies

---

## Clean Code: Naming

Names are the most powerful documentation tool.

| Rule | Bad | Good |
|---|---|---|
| Reveal intent | `d` (days) | `days_since_creation` |
| No disinformation | `accountList` (it's a dict) | `accounts` |
| Meaningful distinction | `ProductData` vs `ProductInfo` | `Product` vs `ProductSummary` |
| Pronounceable | `genymdhms` | `generation_timestamp` |
| Searchable | `7` (days in week) | `DAYS_IN_WEEK = 7` |
| No encodings | `m_description` | `description` |
| Domain language | `process()` | `fulfill_order()` |

**Length rule:** variable scope ∝ name length. Loop counters can be `i`; class-level fields need full names.

---

## Clean Code: Functions

- **Do one thing.** If you can extract a meaningful sub-function, the original does more than one thing.
- **One level of abstraction per function.** Don't mix high-level orchestration with low-level bit manipulation.
- **Stepdown rule.** Functions should read top-to-bottom like a newspaper: high-level to detail.
- **No flag (boolean) parameters.** `render(true)` → `render_html()` and `render_plain()`.
- **No output arguments.** Don't mutate arguments; return values or raise events.
- **Limit arguments.** 0 ideal, 1–2 acceptable, 3 only when essential, 4+ refactor.
- **Command-Query Separation.** A function either changes state OR returns information — never both.

```python
# ❌ Does multiple things, flag param, side effects mixed with query
def process_order(order, send_email=False):
    total = 0
    for item in order.items:
        total += item.price * item.qty
    order.total = total
    if order.total > 0:
        order.status = "confirmed"
    if send_email:
        smtp.send(order.customer_email, f"Your order total: {total}")
    return order.status == "confirmed"

# ✅ Each function does one thing
def calculate_order_total(order: Order) -> Money:
    return sum(item.subtotal for item in order.items)

def confirm_order(order: Order) -> None:
    order.confirm(calculate_order_total(order))

def notify_customer_of_confirmation(order: Order) -> None:
    self._email_service.send_order_confirmation(order)
```

---

## Clean Code: Classes

- **Small.** Measured by responsibilities, not lines.
- **Single Responsibility.** One cohesive purpose.
- **High cohesion.** Class fields used by all (or most) methods.
- **Low coupling.** Few dependencies on other classes.
- **Organize for readability.** Public API at the top, private helpers below.
- **Encapsulate data.** Don't expose internals through getters for every field.

```python
# ❌ Low cohesion — fields used by only some methods
class Stats:
    def __init__(self):
        self.sales_data = []  # used by calc_revenue
        self.user_data = []   # used by count_users
        self.log_data = []    # used by print_logs

# ✅ High cohesion — every field used by every method
class SalesMetrics:
    def __init__(self, sales_data: list[Sale]):
        self._sales = sales_data

    def total_revenue(self) -> Money: ...
    def average_order_value(self) -> Money: ...
    def top_products(self, n: int) -> list[Product]: ...
```

---

## Clean Code: Comments

> "Comments are always failures. We must have them because we cannot always figure out how to express ourselves without them." — Robert C. Martin

**Good comments:**
- Legal headers
- Explanation of intent when the _why_ is not obvious from the code
- Warnings of consequences
- TODO notes (but address them)
- Public API documentation (docstrings)

**Bad comments (remove them):**
- Redundant: `# increment i by 1` before `i += 1`
- Noise: `# constructor`, `# getter`
- Commented-out code: delete it; use version control
- Misleading: outdated comments that no longer reflect the code
- Journal: `# 2024-01-15 John: added null check` → use git blame

```python
# ❌ Redundant comment
# Add item to cart
cart.add_item(item)

# ✅ Explaining a non-obvious domain rule
# Reservations expire after 15 min per the business SLA for high-demand products
RESERVATION_TTL_SECONDS = 900
```

---

## Clean Code: Error Handling

- **Use exceptions, not error codes.** Codes require callers to check them; exceptions propagate naturally.
- **Write the try-catch-finally first.** It defines the scope of what can fail.
- **Use unchecked exceptions** (runtime exceptions) for domain errors; checked exceptions for recoverable I/O.
- **Provide context.** Exception messages should say what failed and why.
- **Don't return None.** Return an empty collection, Optional, or raise an exception.
- **Don't pass None.** Validate at the boundary.
- **Create domain-specific exceptions** for meaningful error handling by callers.

```python
# ❌ Returns None — caller must guess what happened
def find_order(order_id: str) -> Optional[Order]:
    ...
    return None  # Why? Not found? DB error? Deleted?

# ✅ Specific, meaningful exceptions
class OrderNotFoundError(DomainError):
    def __init__(self, order_id: OrderId):
        super().__init__(f"Order {order_id.value} not found")
        self.order_id = order_id

def find_order(order_id: OrderId) -> Order:
    order = self._repo.find_by_id(order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    return order
```

---

## Clean Code: Tests

**F.I.R.S.T. principles:**
- **Fast**: Tests must run quickly or they won't be run often
- **Independent**: Tests must not depend on each other
- **Repeatable**: Same result in any environment
- **Self-Validating**: Pass or fail — no manual inspection
- **Timely**: Written alongside or before the production code (TDD)

**Test naming:** `test_given_<context>_when_<action>_then_<expected>`

```python
class TestOrder:
    def test_given_empty_cart_when_placing_order_then_raises_domain_error(self):
        order = Order.create(customer_id=CustomerId(uuid4()))
        with pytest.raises(DomainError, match="empty"):
            order.place()

    def test_given_active_order_when_adding_item_then_total_updates(self):
        order = Order.create(customer_id=CustomerId(uuid4()))
        order.add_item(ProductId(uuid4()), Quantity(2), Money(Decimal("10.00"), "USD"))
        assert order.total == Money(Decimal("20.00"), "USD")
```

**AAA pattern (Arrange, Act, Assert):**
```python
def test_apply_seasonal_discount():
    # Arrange
    order = build_order(total=Money(Decimal("100.00"), "USD"))
    policy = SeasonalDiscount(rate=Decimal("0.10"))

    # Act
    discount = policy.calculate(order)

    # Assert
    assert discount == Money(Decimal("10.00"), "USD")
```

**One concept per test.** If a test method has multiple `assert` groups for unrelated things, split it.
