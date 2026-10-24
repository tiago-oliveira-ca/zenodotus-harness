# Swift Domain-Driven Design Reference

Read this before designing or reviewing any Swift domain model with real invariants —
value objects, entities, aggregates, repositories, or bounded contexts. For the
one-paragraph version and the "when this is overkill" calibration, `SKILL.md` §2 is
enough; this file is the full tactical treatment.

**Calibration first:** in app-side Swift, one-repository-per-aggregate-root is the right
default *when the domain has real rules*, but resist importing the full DDD tactical
apparatus (unit-of-work, domain-service ceremony, an aggregate for every screen) into a
15-screen CRUD app. Value-type + enum modeling alone gives ~80% of DDD's correctness
benefit for ~20% of the structure. Reserve full aggregates/repositories for genuinely
complex domains (finance, health, sync engines) or server-side Swift services.

## Entities vs. value objects

DDD **value objects** (equality by attributes, immutable) map directly onto Swift
`struct` with value semantics and synthesized `Equatable`/`Hashable`:

```swift
struct Money: Equatable, Hashable, Sendable {
    let amount: Decimal
    let currency: CurrencyCode   // itself a value object
}
```

DDD **entities** (equality by identity, mutable over a lifecycle) are the friction
point, because idiomatic Swift prefers structs over classes. Three viable strategies,
in order of preference:

1. **Struct + typed identity + `Identifiable`** (default for most app domains).
   Mutation is expressed as producing new values, or via the aggregate root's methods.
   Plays well with SwiftUI diffing.
2. **`final class`** when reference identity or a shared mutable lifecycle is inherent
   to the domain (e.g. a long-lived session object).
3. **`actor`** when the entity is *also* a genuine concurrency boundary — not merely
   because it's mutable. See `SKILL.md` §8 and `architecture-and-concurrency.md` for
   when that's actually warranted.

```swift
struct Order: Identifiable, Equatable, Sendable {
    let id: Order.ID
    private(set) var lines: [OrderLine]
    private(set) var status: Status

    enum Status: Equatable, Sendable {
        case draft
        case submitted(at: Date)
        case shipped(tracking: TrackingNumber)
        case cancelled(reason: String)
    }
}
```

## Typed identifiers / phantom types

A `String`-based `User.id` and a `String`-based `Subscription.id` are interchangeable to
the compiler by default — a classic source of bugs. Phantom types fix this, popularized
in the community by Point-Free's `swift-tagged` and widely covered elsewhere:

```swift
// Hand-rolled phantom-typed identifier
struct Identifier<Owner>: Hashable, Sendable {
    let raw: String
}
struct User: Identifiable { let id: Identifier<User> }
struct Subscription: Identifiable { let id: Identifier<Subscription> }
// user.id == subscription.id  // ❌ compile error — different types
```

Or with Point-Free's Tagged library: `typealias ID = Tagged<Order, UUID>`. Tagged uses
generics, generic type aliases, phantom types, and conditional conformance so the
wrapper transparently gets `Decodable`, `Equatable`, etc. for free. Trade-off: a little
ceremony at construction sites and occasional `.rawValue` unwrapping — almost always
worth it for domain IDs and units (the canonical example is distinguishing
`Seconds<Int>` from `Milliseconds<Int>`, or `Dollars<Int>` from `Cents<Int>`).

## Enforcing invariants

Use failable/throwing initializers, or a `private init` + static factory, to make the
DDD "always-valid entity" principle a compiler-checked fact rather than caller
discipline:

```swift
struct EmailAddress: Equatable, Sendable {
    let value: String
    init(_ raw: String) throws(ValidationError) {
        guard raw.contains("@") else { throw .invalidEmail }
        self.value = raw
    }
}

struct Quantity {
    let value: Int
    private init(unchecked value: Int) { self.value = value }
    static func make(_ value: Int) -> Result<Quantity, ValidationError> {
        value > 0 ? .success(.init(unchecked: value)) : .failure(.mustBePositive)
    }
}
```

`private init` + static factory is the Swift expression of "parse, don't validate" —
once you hold a `Quantity`, it's provably valid; there is no code path that constructs
an invalid one.

## Aggregates and aggregate roots

The DDD rule — outside code references only the root, the root enforces invariants, one
repository per aggregate root, persistence at root level — maps naturally onto Swift.
Enforce it with **access control**: the root exposes intent-revealing mutating methods;
children are `private(set)` or hidden behind `internal`/`package` visibility so external
code cannot mutate them directly.

```swift
extension Order {
    mutating func addLine(_ product: Product, quantity: Quantity) throws(OrderError) {
        guard case .draft = status else { throw .cannotModifyAfterSubmit }
        lines.append(OrderLine(product: product, quantity: quantity))
    }
}
```

## Repositories as protocols; domain events

```swift
protocol OrderRepository: Sendable {
    func find(_ id: Order.ID) async throws -> Order?
    func save(_ order: Order) async throws
}

enum DomainEvent: Sendable {
    case orderSubmitted(Order.ID, at: Date)
    case orderShipped(Order.ID, TrackingNumber)
}
```

The domain module declares the *protocol*; the infrastructure module provides the
concrete implementation (Core Data, SQLite, a Vapor Fluent model, a REST client). This
is the dependency-inversion seam — see `SKILL.md` §4 for how SPM makes it a compile-time
fact, not just a convention.

## Bounded contexts and ubiquitous language

Bounded contexts map cleanly onto **SPM packages/targets** (`SKILL.md` §4). Each context
gets its own module and its own namespaced types, so a `Customer` in Billing and a
`Customer` in Support are literally different types unless deliberately shared. Swift's
implicit per-module namespacing makes the ubiquitous-language-per-context discipline
nearly free — you don't need a naming convention to keep them apart, the compiler
already does.
