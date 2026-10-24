# Deep Dives — the three genuinely hard problems

These three areas are where a confident-sounding answer is most likely to be wrong, because
the underlying tension is real and the Rust community has not fully resolved it. Read the
relevant section fully before advising — don't summarize from memory, and don't present the
contested parts as settled.

## Contents
1. [Typestate vs. persistence](#1-typestate-vs-persistence)
2. [Transactions across the port boundary](#2-transactions-across-the-port-boundary)
3. [Async traits + `dyn` (verify against current Rust release)](#3-async-traits--dyn)

---

## 1. Typestate vs. persistence

**The pattern.** Typestate encodes an aggregate's lifecycle state *in its type*, via
zero-sized `PhantomData` markers: `Order<Draft>`, `Order<Paid>`, `Order<Shipped>`. An illegal
transition (shipping a draft order) becomes a *type error*, not a runtime check, and it's
zero-cost — this is a genuinely powerful pattern, used for real in crash-consistency work
(e.g. filesystem state machines) and protocol/handshake implementations.

**Why it breaks specifically against a database.** The type parameter is compile-time-only
information. A row loaded from storage carries its state as *runtime* data — there's no way
to `SELECT` your way into knowing at compile time whether a given row is `Draft` or `Paid`.
You cannot deserialize directly into `Order<Paid>` because the type parameter isn't part of
the serialized representation. The forced resolution is to fall back to a runtime wrapper —
typically an enum:

```rust
enum AnyOrder {
    Draft(Order<Draft>),
    Paid(Order<Paid>),
    Shipped(Order<Shipped>),
}
```

...and this happens **exactly at the boundary where you'd most want the compile-time
guarantee** — loading from the database. The enum wrapper (or a `dyn` boundary) negates the
benefit right where persistence meets the domain.

**Verdict — as settled as this gets:** use typestate for **in-memory builders, protocol/
handshake state machines, and short-lived workflows that never round-trip through storage.**
For a DB-backed aggregate whose state must persist and reload, use a **runtime enum status
field** with transition methods that return `Result` (accepting runtime rather than
compile-time enforcement of the transition rules) — this is the pragmatic default.

There is dissent at the margins: some codebases load as `AnyOrder::try_from(row)` and then
immediately `match` into a typed handling path for the remainder of a single use case, getting
some of the typestate benefit for the in-memory portion of that one operation. Even
proponents of this approach concede the boundary conversion itself is unavoidable — the
disagreement is only about how much of the win survives past that boundary, not about
whether the boundary conversion is needed.

---

## 2. Transactions across the port boundary

**This is the single hardest DDD-in-Rust problem, and there is no settled consensus.**
Multiple public repositories exist specifically to explore this question rather than to
demonstrate a solved pattern — take that as a signal of how open it still is.

### Option (a) — transaction inside the repository method (default)

Each repository method opens and commits its own transaction internally (`pool.begin() … tx
.commit()`). This is the simplest option, and it is **sufficient whenever the DDD rule "one
aggregate per use case / per transaction" is actually followed** — which should be the
default design goal regardless of persistence concerns. Its limitation is real but narrow: it
cannot make two separate repository calls atomic with each other.

**Recommend this as the default.** Most of the "transactions are hard in Rust" pain
disappears once a use case is scoped to a single aggregate, which is good aggregate design
independent of the persistence question.

### Option (b) — a Unit-of-Work port wrapping `sqlx::Transaction` as a struct

A UoW trait hands out something shaped like `Transaction<'a, Postgres>` for the use-case layer
to hold across multiple repository calls. The documented costs are specific and worth
repeating rather than glossing over:

- `pool.begin()` returns a value with a `'static`-or-borrowed lifetime that **ripples through
  every struct that holds the UoW** — every use-case type touching it needs a lifetime
  parameter, which is real syntactic noise and a genuine on-ramp cost for newcomers.
- **Silent rollback on drop.** `sqlx` rolls back a transaction if it's dropped without an
  explicit `.commit()` — with no compiler error and no runtime error, just silently-undone
  work. A typestate-based UoW could catch a forgotten commit at compile time, but doing so
  makes the API meaningfully harder to use — another instance of the typestate-vs-ergonomics
  tension above.
- Repositories returned as `Box<dyn Repository + 'a>` to fit this shape reintroduce heap
  allocation and vtable dispatch that a generics-first design was trying to avoid.

### Option (c) — closure-based Unit-of-Work (generally the least-bad option)

```rust
uow.transaction(|tx| async move {
    let order = order_repo.find_by_id(tx, id).await?;
    // ...
    order_repo.save(tx, &order).await
}).await?;
```

Scoping the transaction's lifetime to the closure contains the borrow-checker friction better
than handing out a `'a`-bound value. This is the option most practitioners converge toward
when they need cross-repository atomicity — but it still leaks an abstraction (the closure
parameter is shaped like whatever `sqlx` (or your chosen driver) exposes), and composing
*multiple* repositories inside one closure can re-raise the same borrow issues option (b) has.

### Synthesis

Adopt "one aggregate per transaction" and put the transaction **inside the repository method**
(option a) as the default — this dissolves most instances of the problem before it starts.
Reach for a **closure-based UoW** (option c) only when a use case genuinely must mutate
multiple aggregates atomically, and go in accepting the lifetime/abstraction leakage as the
price of that requirement. Avoid the `'a`-threaded UoW struct (option b) unless you've already
felt the pain of (c) and have a specific reason to prefer it. Whether a truly
database-agnostic UoW port is achievable at all in Rust is itself an open question — in every
option surveyed, the port ends up shaped by the underlying driver's ownership/lifetime model,
because the transaction is an owned, lifetime-bound resource rather than a GC'd object like it
would be in Java/C#.

---

## 3. Async traits + `dyn`

**Verify the facts in this section against the Rust release notes for whatever toolchain the
project is actually on** — this is the single fastest-moving area covered by this skill, and
the specific crate versions below are a snapshot, not a guarantee.

**Background (stable facts, unlikely to change):** `async fn` in traits (AFIT) and
return-position `impl Trait` in traits (RPITIT) were stabilized together. Async closures
stabilized somewhat later. Check `rustc --version` and the changelog for the installed
toolchain before asserting exact version numbers to the user.

**The fact that matters most and is easy to get wrong:** a trait containing a native `async
fn` is **not automatically `dyn`-compatible ("object-safe")**. Trying to use it as `dyn Trait`
produces an object-safety error, because each `impl`'s `async fn` desugars to a distinct,
compiler-generated `impl Future` state machine with a different size and layout per
implementation — there is no single vtable signature that fits all of them. This has been
true since AFIT stabilized and, as of the most recent verification in this skill's source
material (mid-2026), remained true — **confirm this hasn't changed** before telling a user
their trait objects will "just work" with async methods.

**What to actually recommend, by need:**

1. **Only ever calling the port through generics** (`fn handler<R: Repo>(repo: R)`) — native
   `async fn` in the trait just works, zero cost. This should be the default for the
   domain/application core.
2. **Need `Arc<dyn Repo>`** (runtime implementation selection, a non-generic container/state
   type) — two established workarounds, pick based on how much you care about the allocation:
   - **`dynosaur`** — generates a wrapper type that uses static dispatch where possible and
     only boxes the future under genuine dynamic dispatch, giving most of the performance of
     generics with the flexibility of `dyn`. It is pre-1.0 — **check its current version and
     API on docs.rs before use**; treat it as maturing rather than finished.
   - **`#[async_trait]`** (the older, simpler, still-valid route) — desugars every async
     method to a boxed future (`Pin<Box<dyn Future + Send + 'async_trait>>`), which *is*
     `dyn`-compatible by construction. Costs one heap allocation per call. Perfectly
     reasonable when you want `Arc<dyn Trait>` and the extra allocation is not on a hot path.
3. **Need the returned future to be provably `Send`** (so it can cross into `tokio::spawn`
   from generic code) — native AFIT can't express "this future is `Send`" at the trait
   definition, because the `impl Future` is opaque to the trait signature. The standard
   workaround is a macro (commonly `trait_variant`-style) that generates a parallel
   `Send`-flavored trait from one definition; a caller/impl must pick the `Send` or
   non-`Send` variant up front, which doesn't compose well if a type wants to be conditionally
   `Send`. `#[async_trait]`'s expansion bakes in `Send` by default, which is part of why some
   codebases keep using it even after adopting generics elsewhere.

**Recommended default for an async repository/port trait:**
- Generics + native `async fn` for anything only ever called generically.
- `#[async_trait]` when you need `Arc<dyn Trait>` and simplicity beats the extra allocation.
- `dynosaur` when you need `Arc<dyn Trait>` and the allocation genuinely matters — after
  confirming its current maturity.
- Add a `Send`-bound workaround only once something actually needs to cross a `tokio::spawn`
  boundary — don't add it preemptively.
- Supertrait the port `Send + Sync` whenever it will be stored as `Arc<dyn Port + Send +
  Sync>`.
