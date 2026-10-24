---
name: swift
description: >
  Idiomatic Swift standards for 2026: architecture selection (MVVM + Clean core vs. TCA vs.
  VIPER), value-type domain modeling (DDD entities/value objects, typed IDs), SOLID via
  protocol-oriented programming, Clean Architecture with SPM, error handling (typed
  throws/Result), Swift 6 concurrency (actors, Sendable, MainActor), Swift Testing vs. XCTest.
  Use for any Swift/SwiftUI writing, review, refactor, or architecture choice. Trigger on:
  "typed throws", "TCA", "VIPER", "Vapor", "Swift Testing", "XCTest", "actor", "Sendable",
  "@Observable", "Swift concurrency", "SwiftUI", "MVVM Swift", "Swift DDD", "is this idiomatic
  Swift", or any Swift task — even without "DDD" when modeling a domain with invariants in
  Swift.
---

# Swift Code Standards & Best Practices

As an AI assistant, you must adhere to these standards when generating, reviewing, or
refactoring Swift code. Swift rewards the *goals* of DDD/SOLID/Clean Architecture but
punishes their *classic OOP mechanics* — model the domain with value types and
enums-with-associated-values, keep the dependency rule, but reach for closures and
protocol-witness structs instead of deep protocol hierarchies. Authoritative source for
naming: the Swift API Design Guidelines (swift.org, SE-0023).

**Verify every version number in this skill and its reference files against
swift.org / GitHub / the Swift Package Index before quoting one in generated code** —
see "Version verification" at the end of this file. The architectural guidance is far
more durable than the version numbers.

Concept-level DDD / SOLID / Clean Architecture canon lives in
`code-standards/software-architecture` and its references — the sections below only map
those concepts onto Swift; load that skill for the language-neutral theory.

## 1. Which architecture? Decide before writing code

Default to **MVVM + a thin Clean-Architecture core**: `@Observable` models, use-cases as
structs, repository protocols, wired with initializer injection (add
**swift-dependencies** once you need controllable process-wide state). This is the right
starting point for the large majority of apps.

| Signal | Action |
|---|---|
| New app, unsure of scale | Vanilla SwiftUI + `@Observable`, no extra layers |
| >1 feature team, cross-platform code sharing, real domain rules | Split into SPM targets (§5), extract use-case structs, add swift-dependencies |
| Deep navigation, heavy state composition, team wants maximal testability and is already fluent in SwiftUI | Evaluate **TCA** feature-by-feature — it composes with plain SwiftUI, you don't have to convert the whole app |
| UIKit-era codebase, or someone suggests VIPER for new SwiftUI work | Don't. VIPER's Presenter/passive-View split fights SwiftUI's data-driven model and is legacy-UIKit territory in 2026 — see `references/architecture-and-concurrency.md` for the full comparison |

Escalate past the default only when one of these concrete thresholds is hit — don't
pre-adopt structure the app doesn't need yet:

- **Compile times climbing, or a "Massive ViewModel"/"Massive Reducer" forming** →
  split SPM modules, extract use cases, or (for TCA) split reducers before it calcifies.
- **Protocol indirection causing `any`/existential churn, or `associatedtype`/`Self`
  requirements blocking an existential** → replace that seam with a protocol-witness
  struct of closures (§4).
- **Writing a third `MockXProtocol` class** → switch to closure/witness test doubles +
  swift-dependencies.
- **Bus-factor anxiety about a third-party framework (TCA is a two-maintainer,
  ~14.7k-star project)** → keep domain/use-case logic in plain Swift modules that don't
  import the framework, so it stays confined to the presentation edge and replaceable.

Full comparison table (MVVM / TCA / VIPER / MVC / MVP / Redux-like), narrative verdicts,
and the staged-adoption path are in `references/architecture-and-concurrency.md`.

**On the server** (Vapor/Hummingbird), this table doesn't apply — there's no SwiftUI
data-flow to fight, so classic Clean Architecture/DDD layering pays off more directly.
See the server-side caveat in `references/architecture-and-concurrency.md`.

---

## 2. Domain modeling with value types

**"Make illegal states unrepresentable" is the single highest-leverage technique
available in Swift** — enums with associated values are true sum types the compiler
checks exhaustively. Reach for this before reaching for runtime validation.

```swift
// ✅ Domain choice modeled as a sum type — illegal states unrepresentable
enum OrderStatus: Equatable, Sendable {
    case draft
    case submitted(at: Date)
    case shipped(tracking: TrackingNumber)
    case cancelled(reason: String)
}
```

**Value objects → `struct`.** DDD value objects (equality by attributes, immutable) map
directly onto Swift structs with synthesized `Equatable`/`Hashable`.

**Entities are the friction point** because idiomatic Swift prefers structs over
classes. Default to a **struct + typed identity + `Identifiable`**, with mutation
expressed through the aggregate root's methods; reach for `final class` only when
reference identity/shared mutable lifecycle is inherent (e.g. a long-lived session
object), and `actor` only when the entity is also a genuine concurrency boundary (§7).

**Typed identifiers.** A `String`-based `User.id` and a `String`-based `Order.id` are
interchangeable to the compiler by default — that's a real bug source. Use phantom
types (hand-rolled, or Point-Free's `swift-tagged`) so `user.id == order.id` is a
compile error, not a runtime surprise:

```swift
struct Identifier<Owner>: Hashable, Sendable { let raw: String }
struct User: Identifiable { let id: Identifier<User> }
struct Order: Identifiable { let id: Identifier<Order> }
```

**Enforce invariants with `private init` + a static factory** — this is Swift's
expression of "parse, don't validate": once you hold the value, it's provably valid.

```swift
struct Quantity {
    let value: Int
    private init(unchecked value: Int) { self.value = value }
    static func make(_ value: Int) -> Result<Quantity, ValidationError> {
        value > 0 ? .success(.init(unchecked: value)) : .failure(.mustBePositive)
    }
}
```

Full aggregate/repository/bounded-context treatment — including the "don't import the
full DDD tactical apparatus into a 15-screen app" calibration rule — is in
`references/domain-driven-design.md`. Read it before designing or reviewing any Swift
domain model with real invariants.

---

## 3. SOLID via protocol-oriented programming, and dependency injection

- **SRP** — small structs/enums, free functions; watch for "Massive ViewModel" as the
  SwiftUI-era successor to "Massive View Controller."
- **OCP** — protocol + protocol extension for default behavior. Enums are *closed* by
  design (good for exhaustive domain modeling, bad for open extension) — choose enum
  when the case set is fixed and you want exhaustiveness, protocol when you want open
  extension.
- **LSP** — value types and protocol conformances mostly sidestep inheritance-
  substitution hazards; class inheritance is rare in idiomatic Swift.
- **ISP** — Swift protocols are naturally small. Beware `associatedtype`/`Self`
  requirements that make a protocol unusable as an existential — that's a signal to
  switch to a protocol witness (below).
- **DIP** — the big one: high-level modules depend on protocols the domain owns;
  low-level modules implement them.

**Protocol-heavy indirection has real costs** — slower compile times, `any`/existential
overhead, `Self`/`associatedtype` friction. The idiomatic escape hatch is a **protocol
witness**: a generic struct of closures instead of a protocol. A type can satisfy many
"conformances" this way (impossible with a real protocol, which a type can conform to
only once), and it composes trivially:

```swift
struct OrderRepositoryClient: Sendable {
    var find: @Sendable (Order.ID) async throws -> Order?
    var save: @Sendable (Order) async throws -> Void
}
// Test double = construct one inline with closures. No mock class needed.
```

Full GoF-pattern → Swift-idiom table and the witness technique in depth are in
`references/patterns-and-testing.md`.

**Dependency injection — pick from this table:**

| Approach | Best for | Cost |
|---|---|---|
| **Initializer injection** (default — start here) | Almost everything | Manual wiring; call-tree "dependency carrying" on large apps |
| **swift-dependencies (Point-Free)** | Testability/previews, process-wide dependencies (clock, UUID, API client) you must control in tests | Global-ish registry; best when the architecture funnels through one entry point (SwiftUI/TCA) |
| **SwiftUI `@Environment`** | View-tree-scoped values | View-only — ViewModels can't read it directly |
| **Factory** (Michael Long) | Small–mid SwiftUI apps wanting low intrusion | Still a service-locator flavor |
| **Swinject** | Large/legacy UIKit, gradual migration | Runtime resolution → runtime crashes, not compile-time safety |
| **Needle** (Uber) | Very large teams needing a compile-time-safe graph | Codegen build step |

Start with initializer injection; add swift-dependencies once you have process-wide
dependencies to control in tests and previews. Avoid runtime containers (Swinject) for
new SwiftUI code unless migrating a large UIKit graph. (A widely cited "Factory is
faster than Swinject" number traces to a single informal blog microbenchmark — treat it
as indicative only, not a rigorous result.)

---

## 4. Clean Architecture layering with Swift Package Manager

Model layers as **separate SPM targets or packages** — the dependency rule becomes a
compile-time fact: if `Domain` doesn't link `Presentation`/`Infrastructure`, no one can
accidentally import inward-violating code.

```
MyApp/                      (Xcode app target — composition root only)
└── Packages/
    └── MyFeature/
        ├── Domain          (entities, value objects, repository PROTOCOLS, use cases)
        ├── Infrastructure  (repository IMPLEMENTATIONS; depends on Domain)
        └── Presentation    (SwiftUI views + @Observable models; depends on Domain)
```

```swift
// Package.swift — the dependency rule, enforced by the compiler
.target(name: "Domain"),                                   // depends on nothing
.target(name: "Infrastructure", dependencies: ["Domain"]),
.target(name: "Presentation",   dependencies: ["Domain"]),
.target(name: "AppFeature",     dependencies: ["Domain","Infrastructure","Presentation"]),
```

Use cases are small structs (or functions), not ceremony-heavy classes:

```swift
struct SubmitOrder: Sendable {
    let repository: any OrderRepository
    let clock: any Clock<Duration>
    func callAsFunction(_ id: Order.ID) async throws {
        guard var order = try await repository.find(id) else { throw OrderError.notFound }
        try order.submit(at: Date())
        try await repository.save(order)
    }
}
```

For a mid-large package, split **interface** modules (change rarely) from
**implementation** modules (carry the heavy dependencies) to cut build times —
composition happens only in the app target.

**When this pays off:** multi-module apps, multiple teams, code shared across
iOS/macOS/watchOS/server, long-lived products with real domain rules. **When it's
over-engineering:** a data-in/JSON-out reader app, a prototype, a solo 10-screen app —
collapse to two layers (an `@Observable` model talking to a repository protocol)
instead.

---

## 5. Naming & Clean Code (Swift API Design Guidelines)

- **Clarity at the point of use is the prime directive** — "clarity is more important
  than brevity"; it is explicitly a non-goal to minimize character count. Make call
  sites read as grammatical English: `x.insert(y, at: z)`.
- **Factory methods begin with `make`.**
- **Boolean properties/methods read as assertions:** `isEmpty`, `isActive`, not
  `empty`/`active`.
- **Protocols describing a capability end in `-able`/`-ing`** (`Equatable`,
  `ProgressReporting`); protocols describing what something *is* read as nouns.
- **Compensate for weak type information** (`Any`, `NSObject`, `Int`) with a role noun
  before the parameter: `addObserver(_:forKeyPath:)`.
- Avoid force-unwrapping (`!`); use `guard let ... else { return }` for early exits.
- Command-Query Separation: mutating methods return `Void`; reads are pure. Use
  `@discardableResult` sparingly.

---

## 6. Error handling

Three tiers — pick deliberately, don't default to the newest feature:

- **Untyped `throws`** — the recommended default even by the typed-throws proposal
  authors, for evolving APIs and library boundaries.
- **Typed `throws(SomeError)`** (SE-0413) — only inside a *bounded domain* with a fixed
  error set where you want exhaustive handling (e.g. a pure domain validation
  function). Avoid it on public/library APIs — it locks the error contract and is
  fragile under evolution. (`throws` desugars to `throws(any Error)`; a non-throwing
  function is `throws(Never)` — this is how `Result<Value, Never>` expresses "cannot
  fail.")
- **`Result`** — mostly superseded by `async`/`throws`; still useful for storing an
  outcome, or where `Never` needs to say "cannot fail" explicitly.

```swift
struct EmailAddress: Equatable, Sendable {
    let value: String
    init(_ raw: String) throws(ValidationError) {
        guard raw.contains("@") else { throw .invalidEmail }
        self.value = raw
    }
}
```

---

## 7. Access control as an architecture tool

Use `private` / `fileprivate` / `internal` / **`package`** / `public` deliberately.
`package` is the target-group visibility level — valuable in multi-module SPM setups to
let sibling modules in the same package share API without making it `public` to the
whole world. Enforce aggregate invariants with access control: the root exposes
intent-revealing mutating methods; children are `private(set)` or hidden behind
`internal`/`package` so external code cannot mutate them directly (full pattern in
`references/domain-driven-design.md`). Note Swift 6 changed a bare `import` to default
to `internal` rather than implicitly public.

---

## 8. Concurrency

**Actors are an optional aggregate-boundary tool, not a default.** An `actor` fits a
mutable, shared, concurrently-accessed aggregate (an in-memory cache, a sync engine, a
connection pool) — but actors force `await` at every call site and are *reentrant*
(state can change across suspension points), which complicates invariant reasoning.
**Don't reflexively make every aggregate an actor** — most app-side aggregates are
better as value types owned by a `@MainActor` model. Reserve actors for genuine
concurrency boundaries.

**`Sendable` is the type-level contract for crossing isolation domains.** Value types
with `Sendable` members are implicitly `Sendable` — a strong reason to model the domain
with structs/enums, since they cross actor boundaries for free.

**Swift 6.2 changed the defaults.** A module can default to `@MainActor` isolation
(SE-0466), and `nonisolated(nonsending)` (SE-0461) means nonisolated `async` functions
run on the *caller's* executor instead of hopping to the background pool. Net effect:
treat "app code is main-actor by default; opt into background work explicitly with
`@concurrent`" as the 2026 default posture — don't fight the compiler over background-
thread hops for a simple `await apiClient.fetch()`.

Full SE-0466/SE-0461/SE-0470 mechanics, the actor-reentrancy caveat in depth, and the
Swift 6 strict-concurrency migration path (`-strict-concurrency=complete` under Swift 5
mode → fix warnings → flip to Swift 6) are in
`references/architecture-and-concurrency.md`.

---

## 9. Testing

- **Swift Testing is the default for new unit/integration tests**: `@Test`, `#expect`,
  `#require`, `@Suite` structs, `init`/`deinit` instead of `setUp`/`tearDown`,
  parameterized tests, tags/traits, parallel-by-default execution. A fresh suite
  instance per test surfaces shared-state bugs faster than XCTest did.
- **XCTest is still required for UI automation (`XCUIApplication`) and performance
  (`XCTMetric`) tests** — Swift Testing does not cover these; the two coexist in one
  target but **their assertions do not interoperate** (`XCTFail` won't register in a
  `@Test`, `#expect` won't fail an `XCTestCase`) — never mix them in one file.
- **Prefer closure/witness test doubles** (§3) over hand-rolled `MockXProtocol`
  classes; reach for a protocol-conforming in-memory fake when you want a reusable,
  stateful double.
- Control `Date`/`UUID`/`Clock` via swift-dependencies rather than hardcoding them.

Full detail (parameterized tests, snapshot testing, the Coordinator-pattern testing
caveat) is in `references/patterns-and-testing.md`.

```swift
import Testing

@Suite struct SubmitOrderTests {
    @Test func submittingDraftOrderPersistsSubmittedStatus() async throws {
        let repo = InMemoryOrderRepository(seed: [.draftFixture])
        let submit = SubmitOrder(repository: repo, clock: TestClock())
        try await submit(.draftFixture.id)
        let saved = try await repo.find(.draftFixture.id)
        #expect(saved?.status.isSubmitted == true)
    }
}
```

---

## 10. Version verification

Snapshot only — **re-verify against swift.org / GitHub / Swift Package Index before
quoting any of these in generated code or docs**, this ecosystem moves fast:

| Component | Snapshot state | Verify at |
|---|---|---|
| Swift language | 6.x GA; 6.2 introduced the concurrency-default changes (SE-0466/SE-0461); treat newer minor/patch numbers as unverified until checked | swift.org/download |
| The Composable Architecture (TCA) | 1.x line; a 2.0 has been explicitly signaled by Point-Free as in progress but not yet released — confirm current status before assuming 1.x or 2.x APIs | github.com/pointfreeco/swift-composable-architecture |
| Swift Testing | Ships with the Swift 6 toolchain (no independent version number); still has no UI-automation or performance-test support | swift.org/documentation/testing |
| Vapor | 4.x is the stable, production line; a 5.x has been previewed as an early alpha rebuilt on structured concurrency — do not treat 5.x as production-ready without checking | github.com/vapor/vapor |
| Hummingbird | 2.x, modular/minimal, built on SwiftNIO with structured concurrency from the start | github.com/hummingbird-project/hummingbird |

---

## 11. Documentation & doc comments (DocC)

Public API is documented with `///` markup; DocC builds the reference.
- `///` on every public type, method, property, and initializer.
- First line is a summary sentence; use DocC callouts — `- Parameter x:`, `- Returns:`, `- Throws:`.
- Symbol links in backticks (`` `MyType` ``) so DocC cross-references resolve.
- Rich articles/tutorials live in a `.docc` catalog when a guide is warranted.

Cross-cutting doc discipline (drift, when to update): see `documenting-code`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Making every aggregate an `actor` "to be safe" | Value type owned by a `@MainActor` model; reserve actors for genuine concurrency boundaries |
| VIPER (or heavy layered Clean Architecture) for a new SwiftUI feature | MVVM + thin Clean core by default; VIPER's Presenter/View split fights SwiftUI |
| `throws(SpecificError)` on a public/library API | Untyped `throws` at library boundaries; typed throws only inside a bounded domain |
| Writing a third `MockXProtocol` class by hand | A protocol-witness struct of closures, or swift-dependencies |
| Raw `String`/`UUID` for domain identifiers | Phantom-typed identifiers (`Identifier<Owner>` or `Tagged<Owner, UUID>`) |
| `@StateObject` with an `@Observable` model | `@State`/`@Bindable` — `@Observable` pairs with those, not `@StateObject` |
| Deep protocol hierarchies with `associatedtype`/`Self` blocking `any` usage | A protocol-witness struct of closures |
| Force-unwrapping (`!`) instead of an early exit | `guard let ... else { return }` |
| GoF Strategy/Observer/Command reimplemented as class hierarchies | A stored closure (Strategy), `@Observable`/`AsyncSequence` (Observer), an enum of actions (Command) — see `references/patterns-and-testing.md` |
| Mixing `XCTAssert`/`#expect` in the same test file | Keep Swift Testing and XCTest assertions in separate files; they don't interoperate |
| Reaching for TCA on a simple "reader" app | Vanilla SwiftUI + `@Observable`, or MVVM + Clean core — TCA earns its cost on deep navigation/state composition, not small apps |
| Quoting a specific ecosystem version number from memory | Verify against swift.org / GitHub / Swift Package Index first (§10) |

---

## Pre-flight checklist — run before delivering any Swift code

Before finalizing any Swift code, verify:

- [ ] Domain choices modeled as enums with associated values where the case set is closed and exhaustive — not booleans or optional soup
- [ ] Entities are structs with typed (phantom-typed) identity; `class`/`actor` used only where reference identity or a real concurrency boundary is inherent
- [ ] Invariants enforced via `private init` + static factory, not left to caller discipline
- [ ] No raw `String`/`UUID`/`Int` used interchangeably for different domain identifiers
- [ ] Protocol seams that hit `associatedtype`/`Self`/existential friction are witness structs, not deeper protocol hierarchies
- [ ] Dependencies injected via initializer (or swift-dependencies for process-wide state) — no ad hoc singletons
- [ ] Domain/business-logic code has no import of SwiftUI/UIKit/a specific persistence framework
- [ ] `throws` is untyped by default; `throws(Specific)` used only inside a bounded domain, never on a public library boundary
- [ ] No force-unwraps (`!`) in the delivered code path
- [ ] `Sendable` conformance holds for anything crossing an isolation boundary; actors used deliberately, not reflexively
- [ ] New unit/integration tests use Swift Testing (`@Test`/`#expect`); XCTest reserved for UI automation/performance only, in its own file
- [ ] Any architecture choice (MVVM/TCA/etc.) matches §1's decision table and thresholds, not habit or the most recent blog post
- [ ] Any quoted version number (Swift, TCA, Vapor, Hummingbird, Swift Testing) has been checked against current docs, not asserted from this skill's snapshot
