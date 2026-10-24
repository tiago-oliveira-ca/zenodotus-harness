# SOLID, Clean Code, design patterns, and testing in Go

## Contents
1. [SOLID, translated to Go](#1-solid-translated-to-go)
2. [Clean Code in Go](#2-clean-code-in-go)
3. [Design patterns, Go-flavoured](#3-design-patterns-go-flavoured)
4. [Testing](#4-testing)
5. [Review checklist](#5-review-checklist)

---

## 1. SOLID, translated to Go

| Principle | Go translation |
|---|---|
| **SRP** | Applies to **packages** more than to structs in Go. A `utils` or `common` package is an SRP violation wearing a friendly name — it has as many reasons to change as things get dumped into it. |
| **OCP** | Achieved with interfaces + composition, not inheritance (Go has none). Add a new implementation to extend behavior; don't edit an existing `switch` to add a case if you can add an implementation instead. |
| **LSP** | Any implementation of an interface must honour its documented contract, **including error semantics** — an `io.Writer` that panics instead of returning an error breaks LSP even though it satisfies the interface signature. |
| **ISP** | **Go's strongest suit.** `io.Reader` is one method. If an interface has eight methods, it's really eight different consumers' needs jammed together. Domain/application ports should typically be 1–3 methods. |
| **DIP** | Both sides depend on the interface. Defining it at the consumer (see the main SKILL.md's "Where do interfaces go?" section) gives DIP for free, without a separate "ports" ceremony layer. |

Go-specific corollaries worth stating on their own:

- **`any`/the empty interface is a type-system escape hatch, not a design tool.** Generics
  (1.18+) removed most of its historically legitimate uses. Type-switching on `any` inside the
  domain layer is a strong signal the model itself is wrong, not that the language forced it.
- **Don't design an interface purely so a test can mock it.** If an interface has exactly one
  production implementation and exists only for a test double, ask whether the test should
  just use a real in-memory implementation instead of a mock behind an otherwise-pointless
  abstraction.
- **Embedding is not inheritance.** It's composition with syntax sugar, and it does **not**
  give dynamic dispatch back to the outer type — a method promoted via embedding still runs
  against the embedded type's own view of itself. Embedding to "reuse" methods will eventually
  produce a surprise when the outer type expected to override a promoted method's behavior.

## 2. Clean Code in Go

**Naming**
- Package names: short, lowercase, no underscores, no plurals — `order`, not `orders` or
  `order_service`.
- Avoid stutter: `order.Order` reads fine; `order.OrderService` doesn't — prefer
  `order.Service` when a name would otherwise repeat the package name.
- Getters have no `Get` prefix: `o.Status()`, not `o.GetStatus()`.
- Interface names get an `-er` suffix for a single behaviour (`Publisher`, `Reader`). Domain
  ports can reasonably break this when it's clearer not to (`OrderRepository` communicates
  more than `OrderSaver` would).
- Receiver names: 1–2 letters, consistent across every method on the same type.

**Functions**
- One thing. If the name needs "and" to describe it, split it.
- ~20 lines is a smell threshold to notice, not a hard law — a long `switch` statement is
  fine on its own.
- **No boolean parameters.** `Send(msg, true)` is unreadable at the call site — use an enum-
  like type or two separate functions instead.
- Return early; keep the happy path at minimum indentation. This is the single strongest and
  most load-bearing Go style convention for readability — don't treat it as optional style.
- Named return values: use them for documentation on multi-return signatures, or when a
  deferred function needs to modify the result. Otherwise skip them — naked returns in a long
  function are a readability trap, not a convenience.

**Errors**
- Handle every error. A discarded `_ = doThing()` needs a comment explaining why it's safe to
  ignore.
- Wrap with context: `fmt.Errorf("place order: %w", err)` — lowercase, no trailing
  punctuation, and skip filler like "failed to".
- Sentinel errors for identity checks; custom error types when the caller needs structured
  data back.
- Never `panic` across a package boundary.

**Concurrency**
- **The domain layer is synchronous and single-threaded.** No goroutines, channels, or
  mutexes inside an aggregate — concurrency is an infrastructure concern, full stop.
- Aggregates are not goroutine-safe and shouldn't try to be; serialize concurrent access at the
  transaction/optimistic-locking level instead of adding locking inside the aggregate.

**Comments**
- Doc comments on every exported identifier, starting with the identifier's own name.
  Explain **why**, not what the code already says.
- Comment the invariants on an aggregate explicitly. Those are exactly the things a future
  reader will otherwise "simplify away" without realizing they were load-bearing.

## 3. Design patterns, Go-flavoured

Reach for these only when the underlying problem is actually present in the code — not
because a name from this table sounds relevant.

| Pattern | Go form | Use when |
|---|---|---|
| Repository | Interface at the consumer, concrete struct in `postgres/` (or similar) | Always, for aggregates |
| Factory | `func New(...) (*T, error)` | Whenever construction has invariants to enforce |
| Functional options | `func WithTimeout(d time.Duration) Option` | Optional config on **infrastructure** types. Not on domain aggregates — invariants must be required inputs, never optional ones |
| Strategy | An interface passed as a parameter | Pluggable pricing/tax/shipping policy, etc. |
| Decorator | Wrap an interface, embed it, override one method | Logging, metrics, retries, caching on adapters — arguably the cleanest legitimate use of embedding in Go |
| Adapter / Anti-Corruption Layer | `infrastructure/external/...` | Translating a third-party model into your domain's own ubiquitous language |
| Specification | `type Spec interface{ IsSatisfiedBy(*Order) bool }` | Composable business rules — often overkill; reach for it only when rules genuinely need to combine |
| Observer | `EventPublisher` port + domain events | Decoupling side effects from the aggregate that raises them |
| Outbox | Write events to a table in the same transaction as the aggregate | Whenever at-least-once event delivery correctness actually matters (see the outbox section) |
| Singleton | A package-level var, wired once at the composition root | Almost never worth naming as a "pattern" separately |
| Builder | Rarely needed | Go's struct literals with named fields already fill this role most of the time |

**Anti-patterns to flag on sight:**
- `SomethingService` structs with no fields and one method — simplify to a plain function.
- `interface{}`/`any` in domain signatures — use generics or a concrete type instead.
- A generic `Repository[T]` with `Save/Find/Delete/List/Count` for every aggregate — this
  looks like reuse but is an ISP violation and a leaky abstraction; aggregates are not
  actually interchangeable, so a one-size-fits-all repository interface either has unused
  methods per aggregate or forces every aggregate into the same query shape.
- Config structs threaded all the way down into the domain layer — the domain has no
  business knowing about configuration at all.

## 4. Testing

- **Domain: pure unit tests, zero mocks, zero infrastructure.** If testing an aggregate seems
  to need a mock, that's a sign the aggregate has a dependency it shouldn't have — aggregates
  should be testable as plain values with no test-double machinery at all.
- **Application: fake the ports. [opinion, but well-corroborated]** Prefer hand-written
  in-memory fakes (`type inMemoryOrderRepo struct{ m map[order.ID]*order.Order }`) over
  generated mocks for small, consumer-defined ports. Fakes exhibit real behavior and survive
  refactors of the calling code; mocks assert on call sequences and end up turning a test into
  a transcript of the current implementation rather than a check of behavior. This is not a
  fringe opinion — Andrew Gerrand (Go team) and Ben Johnson both say the same thing in almost
  the same words.
- **When a generated mock genuinely earns its keep** — a large interface, or a test that needs
  to verify call order/count rather than just behavior — use **`go.uber.org/mock`**, not
  `golang/mock`. `golang/mock` has been unmaintained since June 2023; its own README points
  users to Uber's fork, which is a drop-in replacement (swap the `github.com/golang/mock/gomock`
  import for `go.uber.org/mock/gomock`). **`mockery`** (generates `testify/mock`-style mocks) is
  the other common choice and has better generics support. Don't start a new dependency on
  `golang/mock` in 2026-era code.
- **Infrastructure: integration tests against a real database.** testcontainers-go is the
  usual tool for this — verify its current API before relying on example code, this is an
  area that changes.
- **Table-driven tests are the Go default** — use subtests (`t.Run(...)`) so individual
  failures name themselves in test output rather than reporting one big failure.
- **Test naming:** `TestPlaceOrder_WhenProductOutOfStock_ReturnsInsufficientInventory` —
  Go convention generally prefers this readable form over `given_when_then` snake_case.
- **Test invariants explicitly.** Every distinct `return Err...` inside an aggregate deserves
  its own test case — an aggregate with five error returns and one happy-path test is under-
  tested regardless of overall coverage percentage.

## 5. Review checklist

**Domain**
- [ ] Domain package imports nothing outside stdlib (verified in CI, not just by eye)
- [ ] No struct tags (`db:`, `json:`) on domain types
- [ ] Aggregate fields unexported; no setters
- [ ] All invariants enforced in constructors and command methods
- [ ] Typed IDs, not raw strings/UUIDs
- [ ] Other aggregates referenced by ID, never by pointer
- [ ] Domain errors are sentinels or typed; never `panic` for business rules
- [ ] No goroutines/channels/mutexes inside the domain

**Application**
- [ ] `context.Context` is the first parameter everywhere
- [ ] Use case returns DTOs, not aggregates
- [ ] Transaction boundary is owned by the use case, not the repository
- [ ] No business `if`s in the use case — rules live on the aggregate
- [ ] Ports are 1–3 methods (ISP)
- [ ] Reads bypass the domain model (CQRS)

**Infrastructure**
- [ ] Driver errors translated to domain errors at the boundary
- [ ] Persistence records + mappers used; records never escape their package
- [ ] Repository interface is collection-like, not a query DSL

**Presentation**
- [ ] Handlers do decode → map → call → map → encode, and nothing more
- [ ] One central domain-error → transport-status mapping function per transport
- [ ] Presentation DTOs kept separate from application commands

**General**
- [ ] All wiring lives in the composition root; no globals, no working `init()`
- [ ] Errors wrapped with `%w`; checked with `errors.Is`/`errors.As`
- [ ] Every use case has a unit test with faked ports
- [ ] Every aggregate error path has its own test
- [ ] The amount of architecture here is actually justified by the domain's complexity —
      re-check against the pragmatism section if this feels like a CRUD service in a costume
