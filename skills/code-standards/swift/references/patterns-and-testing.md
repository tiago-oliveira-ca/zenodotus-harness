# Swift Patterns & Testing Reference

Full SOLID-to-protocol mapping, the GoF-pattern replacement table, the protocol-witness
technique in depth, the Coordinator pattern, and the full testing section. `SKILL.md`
§3 and §9 carry the summary; read this file when picking a specific pattern or
designing a test strategy.

## SOLID → protocol-oriented programming, in full

- **SRP** — small structs/enums and free functions; watch for the SwiftUI-era "Massive
  ViewModel" as the new "Massive View Controller."
- **OCP** — protocol + protocol extension for default behavior; enums are *closed*
  (good for exhaustive domain modeling, bad for open extension — a deliberate tension).
  Choose enum when the set of cases is fixed and you want exhaustiveness; protocol when
  you want open extension.
- **LSP** — value types and protocol conformances sidestep inheritance-substitution
  hazards; class inheritance is rare in idiomatic Swift.
- **ISP** — Swift protocols are naturally small; compose with protocol inheritance or
  multiple conformances. Beware `associatedtype`/`Self` requirements that make a
  protocol unusable as an existential.
- **DIP** — the big one. High-level modules depend on protocols owned by the domain;
  low-level modules implement them.

## GoF patterns Swift makes redundant

| GoF / classic pattern | Idiomatic Swift replacement |
|---|---|
| Strategy | A stored **closure**, or a small protocol; often just `(Input) -> Output` |
| Singleton | Usually an anti-pattern; prefer injected dependencies. If truly needed, `static let shared` — made controllable via swift-dependencies |
| Factory | Static factory methods; enums; `make…` functions |
| Adapter | Protocol conformance / extension on the adaptee |
| Decorator | **Protocol composition**, wrapping structs, or closures that wrap closures |
| Observer | **`@Observable`** (Observation framework), `AsyncSequence`, or Combine |
| Command | An enum of actions (this is literally TCA's `Action`) |
| Template method | Protocol extension with default implementations + customization points |
| Iterator | Built-in: `Sequence` / `IteratorProtocol` / `AsyncSequence` |

## Protocol witnesses, in depth

Replace a protocol with a generic struct of closures instead of a deep protocol
hierarchy. Advantages over a real protocol:

- A type can have **many** "conformances" this way — impossible with a real protocol,
  which a type can satisfy only one way.
- No `associatedtype`/`Self`-requirement friction blocking existential (`any`) use.
- Trivial composition — wrap or transform the closures directly.
- It's literally what the compiler does under the hood for protocol conformance
  (explicit witness tables), so it isn't a hack — it's making the mechanism explicit.

Cost: less familiar to newcomers, and it loses some protocol ergonomics (no `.self`
existential niceties, no protocol-extension default methods). Point-Free developed the
technique while building their snapshot-testing library, and it's now the backbone of
swift-dependencies' `@DependencyClient` and most modern test doubles.

```swift
struct OrderRepositoryClient: Sendable {
    var find: @Sendable (Order.ID) async throws -> Order?
    var save: @Sendable (Order) async throws -> Void
}
// Test double = just construct one with closures. No mock class needed.
let testClient = OrderRepositoryClient(
    find: { _ in .draftFixture },
    save: { _ in }
)
```

Reach for a witness struct as soon as a protocol seam causes `any`/existential churn or
an `associatedtype`/`Self` requirement blocks the use you need — don't wait until it's
painful across the whole codebase.

## Coordinator pattern for navigation

Adapts Martin Fowler's "Application Controller" pattern (*Patterns of Enterprise
Application Architecture*) to fight Massive View Controllers in UIKit. In SwiftUI it
becomes `NavigationStack(path:)` + an `@Observable` router holding a `NavigationPath`
and a `Route` enum.

**Caveat:** SwiftUI's `NavigationStack` only handles push/pop; modal presentation is
separate, and the SwiftUI Coordinator ends up **more view-coupled** than its UIKit
ancestor — it needs `rootView`/`destination` wiring because everything in SwiftUI wraps
a view. Worthwhile for large multi-flow apps and deep linking; overkill for small apps —
apply the same "don't pre-adopt structure" discipline as `SKILL.md` §1's thresholds.

## Testing, in full

**Swift Testing** (GA with the Swift 6 toolchain) is the default for new
unit/integration tests:

- `@Test` functions, `#expect`/`#require` macros, `@Suite` types (structs preferred —
  `init`/`deinit` replace `setUp`/`tearDown`).
- **Parameterized tests** — a single `@Test(arguments:)` covers a table of cases instead
  of hand-duplicated test functions.
- **Tags and traits** for grouping/filtering (`.tags(.critical)`, `.disabled(...)`).
- **Parallel-by-default execution**, with a fresh suite instance per test — this
  enforces isolation and surfaces tests that quietly assumed shared serial state faster
  than XCTest did.

**XCTest remains required** for UI automation (`XCUIApplication`) and performance
(`XCTMetric`) tests — Swift Testing does not cover either. The two frameworks coexist in
one target, but **their assertions are not interoperable**: `XCTFail` will not register
inside a `@Test`, and `#expect` will not fail an `XCTestCase`. Never mix them in the
same file.

**Test doubles: closures/witnesses vs. protocol fakes.**

- Closure/witness-struct doubles (construct an `OrderRepositoryClient` inline) are
  lighter than a `MockXProtocol` class per protocol, and compose better — this is the
  swift-dependencies philosophy. Default to these.
- Use a protocol-conforming fake (e.g. `InMemoryOrderRepository`) when you want a
  reusable, stateful in-memory implementation shared across many tests.

**Unit-testing use cases without infrastructure:** inject the repository
protocol/client with an in-memory or closure double. Because use cases are structs with
injected dependencies and the domain has no framework imports, these tests are fast and
deterministic. Control `Date`/`UUID`/`Clock` via swift-dependencies (which ships
controllable versions of exactly these) rather than hardcoding them.

**Snapshot testing:** Point-Free's `swift-snapshot-testing` is the de-facto community
library — fittingly, it's also the origin of the protocol-witness technique above.

```swift
import Testing

@Suite struct SubmitOrderTests {
    @Test(arguments: [Quantity.make(1), Quantity.make(5)])
    func submittingWithValidQuantitySucceeds(quantity: Result<Quantity, ValidationError>) async throws {
        let repo = InMemoryOrderRepository(seed: [.draftFixture])
        let submit = SubmitOrder(repository: repo, clock: TestClock())
        try await submit(.draftFixture.id)
        let saved = try await repo.find(.draftFixture.id)
        #expect(saved?.status.isSubmitted == true)
    }
}
```
