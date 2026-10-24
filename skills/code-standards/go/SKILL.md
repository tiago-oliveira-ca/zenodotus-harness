---
name: go
description: >
  Deep-dive Go (1.21+) standard for DDD, Clean Architecture, SOLID, and Clean Code —
  bounded-context-first layout, aggregates with unexported fields, value objects and the
  zero-value trap, consumer-side interfaces, the transaction/Unit-of-Work problem with
  context.Context, CQRS, the transactional outbox, and when Clean Architecture is NOT worth it.
  Trigger on: "Go DDD", "clean architecture in Go", "hexagonal Go", "Go aggregate", "Go
  repository interface", "CQRS in Go", "outbox pattern Go", "internal package structure", "Go
  error wrapping", "Go project layout", "is this idiomatic Go", or any Go service-design task —
  even without "DDD" when modeling a domain with real invariants in Go.
---

# Go Developer — DDD, Clean Architecture & Design Patterns

Scope: idiomatic Go 1.21+. Where the classical OO formulation of a principle conflicts with
Go idiom, **the Go idiom wins** — but say why, so the user can disagree deliberately rather
than inherit a rule silently.

Several judgment calls below are flagged **[opinion]** — real engineering trade-offs, not
settled fact. Present them as trade-offs. Library/tooling notes (`go-arch-lint`, `sqlc`,
`google/wire`, `uber-go/fx`, testcontainers-go) may drift — tell the user to verify current
status before adopting, don't assert a version or maintenance state from memory.

Concept-level DDD / SOLID / Clean Architecture canon lives in
`code-standards/software-architecture` and its references — this file only maps those
concepts onto Go; load that skill for the language-neutral theory.

## The one rule everything else hangs off

> **The domain package imports nothing outside the standard library.**

Everything in this file is negotiable next to that one. If a design choice would put
`database/sql`, an HTTP framework, or a third-party client import inside the domain package,
that's the thing to fix first, regardless of what else looks clean.

The five-question mental model to run before writing a line: What domain concept is this? →
Which layer does it live in (domain / application / infrastructure / presentation)? → Who
depends on whom (dependencies point inward, always)? → What's the single reason this would
change? → Does a known pattern actually fit, or would it be ceremony?

## How to use this file

| Task focus | Where |
|---|---|
| Domain layer, project layout, where interfaces live, application layer, the transaction problem | This file |
| Infrastructure adapters, presentation/handlers, composition root, and **when NOT to do any of this** | `references/layers-and-pragmatism.md` |
| SOLID in Go, Clean Code specifics, design-pattern translations, testing strategy | `references/patterns-and-testing.md` |
| Review checklist | End of this file (also in `references/patterns-and-testing.md`) |

## Project layout: slice by bounded context first, layer second

```
myservice/
├── cmd/api/main.go              # composition root — the ONLY place that wires
├── internal/
│   ├── order/                   # bounded context (vertical slice)
│   │   ├── order.go             # aggregate root + invariants
│   │   ├── money.go             # value object
│   │   ├── events.go            # domain events
│   │   ├── errors.go            # domain sentinel errors
│   │   ├── repository.go        # PORT: interface, when domain-owned (see below)
│   │   ├── app/                 # application layer: use cases
│   │   ├── postgres/            # infrastructure adapter
│   │   ├── kafka/                # infrastructure adapter
│   │   └── http/                 # presentation adapter
│   └── inventory/               # another bounded context — same shape
├── pkg/                          # only if genuinely importable by outsiders
└── go.mod
```

**[opinion, but a strongly-held one]** A top-level `domain/ application/ infrastructure/`
tree — layer first, everything-in-one-bucket — is the most common mistake ported from Java
Clean Architecture repos into Go. It puts an import boundary between things that change
together (an order's aggregate and its own use cases) and no boundary at all between things
that don't (order's domain and inventory's domain, both dumped in one `domain/` package).
`internal/order/...` next to `internal/inventory/...` is a real modularity boundary;
`internal/domain/...` is a filing cabinet. Slice by bounded context, then layer within it.

**`golang-standards/project-layout` is not what you want to copy from, despite being the
most-starred Go layout repo on GitHub.** Its own README says outright that it is "NOT an
official standard defined by the core Go dev team," and Go contributor Eliben Bendersky has
called its `pkg/` advice "outdated" and said the repo is actively "harmful for Go beginners."
Treat it as a menu of ideas some large projects have used, not a standard to default to. The
bounded-context-first layout in this file instead follows Ben Johnson's *Standard Package
Layout* and Kat Zien's GopherCon talk on structuring Go apps — both of which, notably, now
recommend dropping `cmd/` and `pkg/` entirely for anything that isn't a multi-binary project,
keeping `main.go` at the repository root.

- `internal/` is enforced **by the compiler** — anything not deliberately public goes there.
  This is free architecture enforcement; use it rather than relying on convention.
- The aggregate lives in the package root (`order.Order`), not `internal/order/domain/`. In
  Go the package name *is* the namespace — `domain.Order` stutters against the grain.
- `pkg/` is contentious: don't create it unless something outside the module actually imports
  it.
- **Enforce the dependency rule mechanically, not by review.** Options, roughly in order of
  how DDD/hexagonal-aware they are: `fe3dback/go-arch-lint` (YAML-configured, purpose-built for
  hexagonal/onion/DDD import rules, ships a Docker image for CI); `roblaszczak/go-cleanarch`
  (from Three Dots Labs, specifically validates the Dependency Rule, `go install
  github.com/roblaszczak/go-cleanarch@latest`); `depguard` (bundled in `golangci-lint`, the
  most generally-maintained option for simple allow/deny import rules — but its config format
  changed breakingly around the golangci-lint v1.53 v1→v2 migration, so re-verify any snippet
  against the current format before using it); `import-boss` (Kubernetes-ecosystem tooling,
  usable standalone but niche outside it). Verify current maintenance before adopting any of
  these — this is a space with real churn. A fallback that always works with zero
  dependencies: a test that shells out to `go list -deps ./internal/order` and asserts the
  domain package's transitive deps never include `database/sql`, any `github.com/...` driver,
  etc. Crude, but it actually runs in CI. Note that Go's compiler already forbids circular
  imports, so any of these linters are belt-and-suspenders on top of that, not the only thing
  standing between you and a layering violation.

## Where do interfaces go? The Go divergence from classical Clean Architecture

Classical Clean Architecture: the **domain** declares the repository interface;
infrastructure implements it (Dependency Inversion). Idiomatic Go: **"accept interfaces,
return structs"** — the *consumer* declares the smallest interface it needs, at the point of
use. These mostly agree in practice, because the consumer of `OrderRepository` is usually the
application layer, which already sits inside the boundary.

```go
// internal/order/app/place_order.go — the CONSUMER declares the port.
package app

type OrderRepository interface {
    Save(ctx context.Context, o *order.Order) error
    FindByID(ctx context.Context, id order.ID) (*order.Order, error)
}
```

**[opinion]** Both placements — in the domain package (`internal/order/repository.go`) or
next to the sole consumer — are defensible. Put it in the domain package when multiple use
cases share it and it expresses a real domain concept ("orders are a collection you can look
things up in"). Put it next to the consumer when only one use case needs it, or when it's
really an infrastructure concern in disguise (`Clock`, `IDGenerator`, `EventPublisher`).

What's **not** a judgment call: don't create an `internal/order/ports/ports.go` grab-bag of
fourteen interfaces — that's an interface dumping ground, and it violates Interface
Segregation by sheer gravity. And never define an interface next to its implementation "in
case you need to mock it" — that's the `Service`/`ServiceImpl` reflex from Java, and Go's
idiom (interface at the consumer, sized to what it actually needs) already solves the problem
that reflex is trying to solve.

## Domain layer

### Value objects

Immutable, no identity, self-validating, compared by value. Unexported fields, value
receivers, no setters — methods return new values.

```go
type Money struct {
    cents    int64  // never float64 for money
    currency Currency
}

func NewMoney(cents int64, c Currency) (Money, error) {
    if cents < 0 {
        return Money{}, ErrNegativeAmount
    }
    return Money{cents: cents, currency: c}, nil
}

func (m Money) Add(other Money) (Money, error) {
    if m.currency != other.currency {
        return Money{}, ErrCurrencyMismatch
    }
    return Money{cents: m.cents + other.cents, currency: m.currency}, nil
}
```

Go-specific traps that don't exist in the classical formulation of this pattern:

- **The zero value is always constructible, and you cannot prevent it.** `var m Money`
  bypasses `NewMoney` entirely — there is no way to make a Go type "require" its constructor.
  This is a real, unavoidable weakness of value objects in Go, not a solvable problem. Live
  with it by (a) making the zero value meaningful and safe, and/or (b) re-validating at the
  aggregate boundary. Say this plainly to anyone who assumes Go gives Rust/Swift-style
  constructor guarantees — it doesn't.
- If the struct holds a slice or map, it is **not actually immutable** — callers can mutate
  through the shared backing array/map even with unexported fields. Copy on the way in and
  on the way out if this matters.
- **Typed IDs over raw `string`/`uuid.UUID` everywhere:** `type OrderID uuid.UUID` prevents
  passing a `CustomerID` where an `OrderID` is expected. This is one of the highest-value,
  lowest-cost DDD moves available in Go — recommend it by default.

### Aggregate root

The aggregate is the transactional consistency boundary: one aggregate = one transaction =
one repository. Reference other aggregates **by ID only**, never by pointer.

```go
type Order struct {
    id         ID
    customerID CustomerID   // reference by ID, not *Customer
    status     Status
    lines      []Line
    events     []DomainEvent
}

func New(id ID, customerID CustomerID) (*Order, error) {
    if id == (ID{}) {
        return nil, ErrMissingID
    }
    o := &Order{id: id, customerID: customerID, status: StatusDraft}
    o.raise(Created{OrderID: id, CustomerID: customerID, At: time.Now()})
    return o, nil
}

// AddLine is behaviour, not a setter — the invariant lives with the data.
func (o *Order) AddLine(p ProductID, qty Quantity, unit Money) error {
    if o.status != StatusDraft {
        return fmt.Errorf("add line: %w (status=%s)", ErrOrderNotEditable, o.status)
    }
    o.lines = append(o.lines, Line{productID: p, quantity: qty, unitPrice: unit})
    o.raise(LineAdded{OrderID: o.id, ProductID: p, Quantity: qty})
    return nil
}

func (o *Order) raise(e DomainEvent) { o.events = append(o.events, e) }

// PullEvents drains uncommitted events. Named as a command (it mutates), not a
// getter — Command/Query Separation.
func (o *Order) PullEvents() []DomainEvent {
    e := o.events
    o.events = nil
    return e
}
```

Non-negotiable rules here:

- **No setters.** `o.SetStatus(StatusCancelled)` is not a domain operation; `o.Cancel(reason)`
  is. Setters are exactly how anaemic domain models happen in Go.
- **Unexported fields.** This is *the* mechanism that makes "invalid state unrepresentable"
  achievable in Go — exported fields mean anyone outside the package can break an invariant
  directly, with no method call and no review surface.
- Getters are fine, but keep them minimal. Every getter is an invitation to move logic out of
  the aggregate. If a caller reads three getters and does arithmetic on the results, that
  arithmetic belongs on the aggregate, not the caller.
- Keep aggregates small — if loading one order pulls in 4,000 line items, the aggregate
  boundary itself is wrong, not just the query.

### Reconstitution from the database

The constructor validates creation invariants. The repository loading a *persisted* order
must not re-run those rules or re-raise a `Created` event. Two options, genuinely a judgment
call:

- **[opinion] Option A — an explicit `Reconstitute` constructor**, same package (so it can
  touch unexported fields), documented as infrastructure-only: `func Reconstitute(id ID,
  customerID CustomerID, status Status, lines []Line) *Order`. Pragmatic, but it's exported
  and therefore abusable by anything else in the same package — that's a real cost, not a
  free lunch.
- **Option B — a `Snapshot`/Memento pair**: `func (o *Order) Snapshot() Snapshot` /
  `func FromSnapshot(Snapshot) *Order`. Tidier, keeps the mapping explicit, costs more code.

Pick one and be consistent across aggregates. What's **not** a judgment call: don't solve this
with reflection, and don't put persistence struct tags (`db:"..."`, `json:"..."`) directly on
the aggregate — that's the ORM bleeding into the domain, and it's the most common Clean
Architecture violation actually found in real Go codebases. A boring, explicit mapper
function in the infrastructure layer is correct; reflection-based auto-mapping is not.

### Domain errors

- Sentinel errors (`var ErrNotFound = errors.New(...)`) for identity checks; a custom
  `error` type when the caller needs structured data (`InsufficientInventoryError{ProductID,
  Requested, Available}`), not just an identity to switch on.
- Wrap with `%w` at every layer boundary that adds context; check with `errors.Is`/`errors.As`
  — never compare error strings.
- **Never `panic` for a business rule violation.** Panic is for programmer error and
  unrecoverable invariant breach only, not for "order isn't editable."
- The domain returns domain errors. The presentation layer maps them to status codes/exit
  codes/whatever the transport needs. The domain must never know what an HTTP 409 is.

### Domain services

Only when behaviour genuinely belongs to no single aggregate — and in Go this is usually just
a **function**, not a struct:

```go
func CalculatePrice(o *Order, p PricingPolicy) (Money, error) { ... }
```

If the result is `type PricingService struct{}` with no fields and one method, that's a
function wearing a struct as a costume — simplify it.

## Application layer (use cases)

One use case per type, named as a verb phrase. It orchestrates; it contains **no** business
rules of its own.

```go
type PlaceOrder struct {
    orders   OrderRepository
    products ProductRepository
    events   EventPublisher
    tx       TxManager
}

func (uc *PlaceOrder) Execute(ctx context.Context, cmd PlaceOrderCommand) (PlaceOrderResult, error) {
    var result PlaceOrderResult
    err := uc.tx.Do(ctx, func(ctx context.Context) error {
        o, err := order.New(order.NewID(), order.CustomerID(cmd.CustomerID))
        if err != nil {
            return fmt.Errorf("place order: %w", err)
        }
        for _, item := range cmd.Items {
            p, err := uc.products.FindByID(ctx, order.ProductID(item.ProductID))
            if err != nil {
                return fmt.Errorf("place order: load product %s: %w", item.ProductID, err)
            }
            if err := o.AddLine(p.ID(), order.Quantity(item.Quantity), p.Price()); err != nil {
                return fmt.Errorf("place order: %w", err)
            }
        }
        if err := uc.orders.Save(ctx, o); err != nil {
            return fmt.Errorf("place order: save: %w", err)
        }
        return uc.events.Publish(ctx, o.PullEvents()...)
    })
    return result, err
}
```

Rules:

- `context.Context` is always the first parameter, always.
- **Return DTOs, not aggregates.** Returning `*order.Order` to a handler lets the handler call
  domain methods directly — now business logic can leak into presentation code.
- **The use case owns the transaction boundary, not the repository.** A repository that opens
  its own transaction internally cannot participate in a larger unit of work spanning
  multiple repositories.
- No `if` on business rules in the use case. Seeing `if order.Status == "DRAFT"` here means
  that rule escaped the aggregate — push it back onto `Order`.
- The use case is the unit-test seam: fake the ports, no real database involved.

### The transaction / Unit-of-Work problem — genuinely awkward, no consensus

```go
type TxManager interface {
    Do(ctx context.Context, fn func(ctx context.Context) error) error
}
```

The common Go answer threads the transaction through `context.Context`: the Postgres adapter
stores `*sql.Tx` in the context, and repositories pull it out (falling back to the pool if
absent). **[opinion]** It works and keeps the port signature clean, but hiding a transaction
inside `context.Value` is exactly the kind of implicit dependency `context` misuse is usually
criticized for — passing context everywhere and being unable to run a long business
transaction are the concretely-cited costs.

**A named alternative worth presenting explicitly, not just gesturing at:** Three Dots Labs'
**Transaction Provider pattern** rejects context-threading on the grounds that it "masks the
root issue of mixing the implementation details with the logic." Instead of hiding the `tx`,
a provider hands the use case a callback bound to a struct of repositories that all share one
transaction:

```go
type Adapters struct {
    Orders   OrderRepository
    Products ProductRepository
}

func (p *txProvider) Transact(ctx context.Context, fn func(Adapters) error) error {
    tx, err := p.pool.Begin(ctx)
    if err != nil { return err }
    defer tx.Rollback(ctx) // no-op if committed
    if err := fn(Adapters{Orders: newOrderRepo(tx), Products: newProductRepo(tx)}); err != nil {
        return err
    }
    return tx.Commit(ctx)
}
```

This keeps transaction mechanics entirely in the infrastructure layer and out of the service
signature, at the cost of the use case depending on `Transact(...)` rather than a plain
`TxManager.Do(...)`. Three camps exist and none has won outright: context-threading (clean
signatures, implicit dependency), an explicit `Tx` parameter (honest, but leaks infrastructure
into the port), and the Transaction Provider above (no leakage, more ceremony at the call
site). Pick the version your team will misuse least, and say so explicitly rather than
presenting any one of them as the settled answer.

The underlying enabler for all three: define a `DBTX` interface with just the methods you need
(`ExecContext`/`QueryRowContext`, or `pgx`'s equivalents) so a repository works identically
against a pool or a transaction without knowing which it has.

### CQRS: reads don't need the domain model

A query that loads a full aggregate, calls six getters, and reassembles a view model is pure
overhead. **[opinion, but load-bearing]** Applying the full write-side stack (aggregate →
repository → mapper) to reads is the single biggest source of Clean-Architecture ceremony
fatigue in Go codebases. The fix: write side goes HTTP → command → use case → aggregate →
repository (full stack); read side goes HTTP → query → SQL → view model, skipping the domain
model entirely. This is not a shortcut or a violation — it's the point of separating reads
from writes.

---

Read `references/layers-and-pragmatism.md` next for infrastructure adapters (error
translation at the boundary, persistence records vs. domain types), the presentation layer,
the composition root, domain events + the transactional outbox, and — importantly — the
section on when the full stack is *not* worth building. Read
`references/patterns-and-testing.md` for SOLID-in-Go, Clean Code specifics, the design-pattern
translation table, and testing strategy. The review checklist from that file is reproduced
below so it's always in hand.

## Documentation & doc comments (godoc)

Public identifiers get a doc comment; godoc / pkg.go.dev render them.
- Every exported package, type, func, const, and var has a `//` comment immediately above it.
- The comment **starts with the identifier's name** ("Fetch returns…", "Config holds…") — the godoc convention.
- Package doc: a `// Package <name> …` comment on one file (or a `doc.go`).
- Full sentences; document the contract (what / why / errors), not the obvious mechanics.
- Runnable `Example` functions in `_test.go` double as verified docs — they compile and run under `go test`.

Cross-cutting doc discipline (drift, when to update, generators): see `documenting-code`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `database/sql`, an HTTP framework, or a third-party client imported in the domain package | The domain package imports nothing outside the standard library |
| Layer-first top-level tree (`internal/domain/`, `internal/infrastructure/`) | Slice by bounded context first: `internal/order/...` next to `internal/inventory/...` |
| An `internal/order/ports/ports.go` grab-bag of interfaces | Smallest interface declared at its consumer, sized to what it actually needs |
| Interface defined next to its implementation "in case you need to mock it" | Consumer-side interface — the `Service`/`ServiceImpl` reflex has no place in Go |
| `float64` for money | Integer cents inside a `Money` value object |
| Raw `string`/`uuid.UUID` IDs everywhere | Typed IDs — `type OrderID uuid.UUID` |
| Setters or exported fields on aggregates (`o.SetStatus(...)`) | Unexported fields; intent-revealing commands (`o.Cancel(reason)`) that enforce invariants |
| Referencing another aggregate by pointer | Reference by ID only |
| Persistence struct tags (`db:"..."`, `json:"..."`) on domain types, or reflection auto-mapping | A boring, explicit mapper function in the infrastructure layer |
| Comparing error strings | Wrap with `%w`; check with `errors.Is`/`errors.As` |
| `panic` for a business rule violation | Return a domain error (sentinel or typed) |
| Business rules in the use case (`if order.Status == "DRAFT"`) | Push the rule back onto the aggregate |
| Returning aggregates from use cases to handlers | Return DTOs |
| Repository opening its own transaction internally | The use case owns the transaction boundary |
| Full aggregate → repository → mapper stack for reads | CQRS: query → SQL → view model, skipping the domain model |

## Pre-flight checklist — run before delivering any Go code

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
