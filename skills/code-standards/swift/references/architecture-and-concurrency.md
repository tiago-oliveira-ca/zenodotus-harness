# Swift Architecture Comparison & Concurrency Reference

The full MVVM/TCA/VIPER comparison, the staged-adoption path, the Swift 6/6.2
concurrency mechanics, the server-side Swift caveat, and the version-landscape detail.
`SKILL.md` §1 and §8 carry the decision rules and summary; read this file for the
underlying comparison and the deeper mechanics behind SE-0466/SE-0461.

## Community architecture comparison (2025–2026)

| Architecture | Testability | Boilerplate | Team scale | SwiftUI fit | Learning curve | Momentum | Maintenance risk |
|---|---|---|---|---|---|---|---|
| Vanilla SwiftUI + `@Observable` | Medium | Very low | Small | Native | Low | High | Low (Apple-owned) |
| MVVM | Good | Low–med | Small–large | Native | Low | High | Low |
| **MVVM + Clean core** (recommended default) | High | Medium | Med–large | Good | Medium | High | Low |
| TCA | Very high | Med–high | Med–large | Very good (built for it) | High | Strong but niche | Medium (3rd-party, small-team maintenance, functional paradigm) |
| VIPER | High | Very high | Large | Poor | High | Declining | Medium |
| MVC (UIKit) | Low | Low | Small | N/A (UIKit) | Low | Legacy | Med (Massive VC) |
| MVP | Good | Medium | Medium | Poor (UIKit-oriented) | Medium | Legacy-ish | Medium |
| Redux/unidirectional (non-TCA) | High | Med–high | Medium | Good | Medium–high | Modest | Medium |

**Narrative verdicts:**

- **MVVM** pairs naturally with SwiftUI — `@Observable` model *is* the ViewModel. Its
  failure mode is the "Massive ViewModel"; keep business rules in use cases/domain, not
  the VM. Best balance for most production apps. Note the `@Observable` migration
  nuance: it replaces `ObservableObject`/`@Published` and pairs with `@State`/
  `@Bindable`, **not** `@StateObject` — `@State` re-initializes the object on each view
  rebuild and then discards the new instance, which bites anyone relying on init side
  effects.
- **TCA** is the most opinionated, most testable option: value-type `State`, enum
  `Action`, a `Reducer` with a result-builder `body`, `Store`, `@Dependency` (like
  `@Environment` but usable outside views), 100%-testable state sharing/effects. Fits
  SwiftUI's data-driven model well and even lets you use value types where vanilla
  SwiftUI needs reference types. Costs are real: steep learning curve; "Massive
  Reducer" risk; whole-tree action processing plus a single global state struct create
  performance and build-time pressure at scale; deep call stacks complicate debugging;
  and it's a third-party dependency with a small maintenance team — effectively a
  bus-factor risk for critical paths. Don't reach for it while still learning SwiftUI,
  and don't use it on a simple "reader" app. The Observation-era `@ObservableState`
  removed the need for `ViewStore`, easing one of the historic pain points.
- **VIPER** (View-Interactor-Presenter-Entity-Router) delivers strict separation and
  testability at very high boilerplate ("many small files"); it's UIKit-era and rare in
  SwiftUI, where its Presenter/passive-View split fights the framework. Generally
  over-engineering for SwiftUI in 2026.
- **MVC/MVP** are legacy/UIKit contexts; MVC is fine for prototypes but yields Massive
  View Controllers.
- **Redux-like unidirectional flow** (without TCA) gives predictability but rebuilds
  much of what TCA already solved, without TCA's tooling.

## Staged adoption path

1. **Start (any new app):** vanilla SwiftUI + `@Observable` models + repository
   *protocols* + initializer injection. Model the domain with structs,
   enums-with-associated-values, and typed IDs from day one. Write tests in Swift
   Testing.
2. **When you have >1 feature team, cross-platform code sharing, or real domain
   rules:** split into SPM targets (Domain/Infrastructure/Presentation), introduce
   use-case structs, adopt swift-dependencies for controllable clock/UUID/API/
   file-system.
3. **When state composition, deep navigation, and exhaustive testability become
   dominant concerns *and* the team is fluent in SwiftUI:** evaluate TCA
   feature-by-feature — it composes with plain SwiftUI.
4. **Server-side:** apply fuller DDD/Clean layering (see below); pick Vapor for
   production today, or Hummingbird for a lean, concurrency-first stack.

## Concrete escalation thresholds

- Compile times climbing, or a "Massive ViewModel"/"Massive Reducer" forming → split
  modules, extract use cases, or split reducers before it calcifies.
- Protocol indirection causing `any`/existential churn or `associatedtype`/`Self` pain →
  switch that seam to a protocol-witness struct of closures.
- Writing a `MockXProtocol` class for the third time → adopt closure/witness doubles +
  swift-dependencies.
- Bus-factor anxiety about a third-party framework (TCA) → keep domain/use-case logic in
  plain Swift modules that don't import it, so it stays confined to the presentation
  edge and replaceable.
- Swift 6 migration stalling on data-race errors → adopt
  `-strict-concurrency=complete` incrementally under Swift 5 mode; lean on value types
  and `@MainActor`-by-default (6.2) to shrink the surface.

## Swift Concurrency implications for architecture, in full

- **Actors as aggregate boundaries — sometimes.** An `actor` fits a mutable, shared,
  concurrently-accessed aggregate (an in-memory cache, a sync engine, a connection
  pool). But actors force `await` at every call site and are *reentrant* — state can
  change across suspension points — which complicates invariant reasoning. Don't
  reflexively make every aggregate an actor; most app-side aggregates are better as
  value types owned by a `@MainActor` model. Reserve actors for genuine concurrency
  boundaries. As one practitioner framing goes: "an actor is only as safe as the types
  that cross its boundaries."
- **`Sendable` is the type-level contract** for crossing isolation domains. Value types
  with `Sendable` members are implicitly `Sendable` — a strong reason to model the
  domain with structs/enums, since they cross actor boundaries for free.
- **Structured concurrency in use cases:** `async let`, `TaskGroup`, and cancellation
  propagation belong inside use-case/interactor code, not views.
- **Swift 6 strict concurrency (complete checking, default in Swift 6 mode)** turns
  data-race classes into compile errors: sending non-`Sendable` values across isolation
  boundaries, unsynchronized global mutable state (SE-0412), etc. Migration path:
  enable `-strict-concurrency=complete` under Swift 5 mode, fix warnings, then flip to
  Swift 6 mode. Swift 6 also added region-based isolation so the compiler can prove some
  non-`Sendable` values are used safely without warning.
- **Swift 6.2 "Approachable Concurrency" changes the defaults architecturally.** Two
  distinct-but-related build settings:
  - **SE-0466 "default actor isolation"** — a module can default to `@MainActor`
    (Xcode build setting `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`; new app projects
    enable it by default; an SPM package opts in via
    `.defaultIsolation(MainActor.self)` — a new package does **not** set it
    automatically).
  - **`SWIFT_APPROACHABLE_CONCURRENCY = YES`** — an umbrella flag enabling **SE-0461**
    (`nonisolated(nonsending)`: nonisolated `async` functions run on the *caller's*
    executor instead of hopping to the global pool) and **SE-0470**
    (`InferIsolatedConformances`).
  - **Net effect:** the idiomatic model becomes "app code is main-actor by default; you
    *opt into* background concurrency explicitly with the `@concurrent` attribute" —
    the escape hatch that pushes work to a background executor. This removes a common
    class of friction (fighting the compiler over background-thread hops for a simple
    `await apiClient.fetch()`).
  - Some secondary sources conflate SE-0466 with the Approachable-Concurrency umbrella;
    treat them as two separate settings, both on by default in new Xcode projects that
    opt into the modern defaults — verify current Xcode-version defaults before relying
    on this.

## Server-side Swift caveat (Vapor/Hummingbird)

Guidance diverges from the client-side table above: on the server there's no SwiftUI
data-flow to fight, so **classic Clean Architecture/DDD layering pays off more directly**
— controllers → services/use-cases → repositories (Fluent or raw), much closer to a
typical FastAPI/Java layered-backend shape.

- **Vapor** is batteries-included (Fluent ORM, Leaf templating, JWT) — the established
  choice for production today.
- **Hummingbird** is modular/minimal, built on SwiftNIO with structured concurrency from
  the start and a result-builder router — a leaner alternative when you don't need
  Vapor's full package.
- A next-generation Vapor has been previewed as an early alpha, planned as a rebuild on
  a Hummingbird-based HTTP server with full structured concurrency and no
  `EventLoopFuture` — treat it as experimental only until it reaches a stable release;
  the current stable Vapor line remains the production default and is supported long
  after any next-gen release ships.
- Actors and `Sendable` discipline matter *more* on the server than on the mostly-
  main-actor client — real parallelism, many in-flight requests.

## Version-landscape detail

This section is a snapshot, not a fact to assert without checking. As of this skill's
authoring (mid-2026):

- Swift language: 6.x is GA; 6.2 introduced the concurrency-default changes described
  above. A 6.4+ line has been signaled but should be treated as preview/unverified
  until confirmed against swift.org.
- TCA: on the 1.x line in production use; Point-Free has explicitly signaled a 2.0 in
  progress (deprecation passes preparing for it) but not yet released as of this
  writing — confirm current status on GitHub before assuming either 1.x-only or
  2.x-available APIs.
- Swift Testing: ships bundled with the Swift 6 toolchain, no independent version
  number to track; still lacks UI-automation and performance-test support (both remain
  XCTest-only).
- Vapor: stable production line is 4.x; a 5.x alpha exists as an early,
  not-production-ready preview of a structured-concurrency rebuild.
- Hummingbird: 2.x is current, modular and SwiftNIO-based.

**Re-check every one of these against swift.org, the relevant GitHub repo, or the Swift
Package Index before quoting a specific version number in generated code, a
`Package.swift`, or documentation** — this is explicitly the fastest-moving part of the
Swift ecosystem and the fact most likely to be stale by the time this skill is read.
