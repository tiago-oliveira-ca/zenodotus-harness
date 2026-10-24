# Infrastructure, presentation, composition root, and when to skip all of it

## Contents
1. [Infrastructure layer](#1-infrastructure-layer)
2. [Presentation layer](#2-presentation-layer)
3. [Domain events and the transactional outbox](#3-domain-events-and-the-transactional-outbox)
4. [Composition root](#4-composition-root)
5. [Pragmatism: when NOT to do this](#5-pragmatism-when-not-to-do-this)

---

## 1. Infrastructure layer

```go
package postgres

type OrderRepository struct {
    db DBTX // interface satisfied by both *pgxpool.Pool and pgx.Tx
}

func (r *OrderRepository) FindByID(ctx context.Context, id order.ID) (*order.Order, error) {
    row := r.conn(ctx).QueryRow(ctx, `SELECT id, customer_id, status FROM orders WHERE id = $1`, uuid.UUID(id))

    var rec orderRecord
    if err := row.Scan(&rec.ID, &rec.CustomerID, &rec.Status); err != nil {
        if errors.Is(err, pgx.ErrNoRows) {
            return nil, fmt.Errorf("find order %s: %w", id, order.ErrNotFound) // translate!
        }
        return nil, fmt.Errorf("find order %s: %w", id, err)
    }
    return toDomain(rec) // mapper
}
```

- **Translate infrastructure errors into domain errors at this boundary, always.**
  `pgx.ErrNoRows` must never reach the application layer — if it does, the use case is now
  coupled to a specific driver's error type, which is exactly what the port was supposed to
  prevent.
- `orderRecord` is the persistence model, carrying `db:` tags. It lives here and never leaves.
  `toDomain`/`fromDomain` mapper functions are boring, explicit, and correct — resist
  generating them via reflection; the explicitness is the point, not a limitation to work
  around.
- Repository interfaces are **collection-like** (`Save`, `FindByID`, `Delete`), not
  query-DSL-like (`FindByStatusAndDateRangeOrderedBy(...)`). Put that kind of query on the
  read/CQRS side instead — trying to express it through the write-side repository interface
  is how repositories grow into ISP violations.
- `sqlc` is worth evaluating for the read side **[opinion]** — generated, type-safe queries
  with no ORM in the loop. Verify its current feature set against its docs before committing
  to it; tooling in this space moves.
- GORM is popular but pulls hard toward putting struct tags on domain types directly, since
  that's the path of least resistance with an ORM. If a project uses it, keeping that
  discipline (tags only on separate record structs) is entirely on the team, not the tool.

## 2. Presentation layer

```go
func (h *OrderHandler) PlaceOrder(w http.ResponseWriter, r *http.Request) {
    var req placeOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        writeError(w, http.StatusBadRequest, "malformed body")
        return
    }
    res, err := h.placeOrder.Execute(r.Context(), req.toCommand())
    if err != nil {
        writeDomainError(w, err) // single place that maps domain → HTTP
        return
    }
    writeJSON(w, http.StatusCreated, toResponse(res))
}

func writeDomainError(w http.ResponseWriter, err error) {
    var insufficient *order.InsufficientInventoryError
    switch {
    case errors.As(err, &insufficient):
        writeError(w, http.StatusConflict, insufficient.Error())
    case errors.Is(err, order.ErrNotFound):
        writeError(w, http.StatusNotFound, "order not found")
    case errors.Is(err, order.ErrOrderNotEditable):
        writeError(w, http.StatusUnprocessableEntity, err.Error())
    default:
        slog.Error("unhandled error", "err", err)
        writeError(w, http.StatusInternalServerError, "internal error")
    }
}
```

- Request/response DTOs live here with `json:` tags, and are **not** the same types as the
  application layer's commands, even when the fields look identical right now. The
  duplication *is* the decoupling — accept the extra boilerplate rather than collapsing the
  two to save a struct.
- The handler's job is exactly: decode → map → call the use case → map → encode. Nothing else
  — no business logic, no direct domain method calls.
- One central domain-error → transport-status mapping function per transport, not scattered
  `switch`es across every handler.
- Kafka consumers, CLI commands, and gRPC handlers are presentation too — the same rules
  apply to them as to HTTP handlers.

## 3. Domain events and the transactional outbox

Raising events on the aggregate and publishing them right after save has a real correctness
gap: the DB commit can succeed while the message-broker publish fails, silently losing the
event. If the system needs at-least-once delivery, publish via a **transactional outbox** —
insert the events into an `outbox` table inside the *same* transaction as the aggregate, and
have a separate relay process read and publish them asynchronously.

**[opinion]** For internal, non-critical events (cache invalidation, analytics pings), a
direct publish is fine and an outbox is over-engineering for the stakes involved. For anything
another bounded context depends on for *correctness* (not just freshness), use the outbox —
the failure mode of silently losing a small percentage of events is the kind of thing that's
discovered in production, months later, and is expensive to diagnose after the fact.

One more subtlety worth flagging explicitly rather than hiding: publishing *after* the
aggregate is saved but *while still inside* a `tx.Do(...)`-style transaction wrapper is
subtly wrong — the publish call happens before the transaction actually commits, so a
publish can succeed for data that then rolls back. The correct shapes are: publish only after
the wrapping transaction function returns successfully (outside the closure), or use the
outbox pattern so the event write is part of the same atomic unit as the aggregate write. If
example code elsewhere shows the simpler (publish-inside-tx) version for readability, call out
that it's simplified and not the version to actually ship.

## 4. Composition root

Exactly one place: `cmd/api/main.go` (or the equivalent entry point). Everything is wired
here and nowhere else.

```go
func main() {
    cfg := config.Load()
    pool, err := pgxpool.New(ctx, cfg.DatabaseURL)
    if err != nil { log.Fatal(err) }
    defer pool.Close()

    orderRepo := postgres.NewOrderRepository(pool)
    productRepo := postgres.NewProductRepository(pool)
    publisher := kafka.NewPublisher(cfg.Brokers)
    txManager := postgres.NewTxManager(pool)

    placeOrder := app.NewPlaceOrder(orderRepo, productRepo, publisher, txManager)

    handler := httpapi.NewOrderHandler(placeOrder)
    mux := http.NewServeMux()
    handler.Register(mux)

    srv := &http.Server{Addr: cfg.Addr, Handler: mux}
    // ... graceful shutdown on SIGTERM
}
```

- **Manual wiring first. [opinion]** It's explicit, entirely compile-checked, and readable
  top to bottom. A hundred lines of `main.go` doing nothing but construction is not, by
  itself, a problem that justifies pulling in a framework. This is the community consensus,
  not just a house preference — Ben Johnson's `main` is "fairly small and trivial code" that
  just news up a repository and attaches it to the handler.
- **`google/wire` is archived and unmaintained** (archived by its owner Aug 25, 2025; last
  release v0.7.0). It still works — it generates plain Go with zero runtime reflection, so
  existing wire-based codebases don't break — but do not start a *new* dependency on it. A
  community fork (`goforj/wire`) exists but is not named or endorsed in `google/wire`'s own
  README; treat it as community-supported, not a drop-in replacement with the same trust
  level.
- If manual wiring genuinely becomes unmanageable at scale — deep dependency chains with
  mixed lifetimes — prefer **`uber-go/fx`** instead. It's actively maintained (Uber's own
  README calls it "the backbone of nearly all Go services at Uber," SemVer-stable at v1) and
  adds managed lifecycle hooks (`fx.Lifecycle`, `OnStart`/`OnStop`) on top of `uber-go/dig`'s
  runtime-reflection DI. The tradeoff against wire's old compile-time-safety pitch is real —
  fx failures surface at runtime, not compile time — but it's the actively-maintained option,
  which now matters more than the safety-property difference did.
- **No global state.** No `init()` doing real work, no package-level DB handle sitting outside
  the composition root. Globals are the composition root's responsibilities leaking into
  every file that happens to import the package.

## 5. Pragmatism: when NOT to do this

This is the section most Clean Architecture write-ups skip, and it matters as much as the
rest of the document.

The full stack — aggregates, value objects, ports, mappers, DTOs at every boundary, an
outbox — costs real implementation time and real lines of code. It earns that cost when:

- The domain has genuine complexity: non-trivial invariants, real state machines, business
  rules that actually change over time.
- The service will live for years and be touched by people who didn't write it.
- There's a real need to swap infrastructure, or to test business rules without spinning up a
  database.

**It does not pay for itself for a CRUD service that reads and writes rows with no real
invariants.** For that, `handler → sqlc → response` in one package is the correct
architecture, and wrapping it in four layers and a repository abstraction over a single
implementation is cargo-culting a solution to a problem the service doesn't have. The layers
are a response to complexity that's actually present — not a substitute for having some.

**The escalation path that works in practice:** start with `handler → service → db` in one
package. When the invariants get hard to keep straight in your head, extract the aggregate.
When the aggregate would need a database import to do its job, extract the port. Let the
structure be *pulled out by pain* as the domain actually gets more complex — not *pushed in
by ceremony* on day one because a document says a real system should look this way.
