# Domain-Driven Design, Clean Architecture & Design Patterns in Rust

Rust's type system is an unusually good fit for tactical DDD — "make illegal states
unrepresentable" is closer to true here than in almost any mainstream language. But getting
there requires *inverting instincts* carried over from Java/C#/TypeScript: layers become
modules or crates (not packages+interfaces), ports are traits defined at the consumer, errors
are `Result` types with `thiserror`, and the reflex to reach for `Arc<Mutex<dyn Trait>>`
everywhere is usually a sign the design hasn't found Rust's actual idiom yet.

This reference is about the *tactical modeling and architecture* layer. For general Rust
production concerns (Tokio task hygiene, Axum handlers, `sqlx` query macros, tracing,
`cargo` CI tooling), see the main `SKILL.md` — this file goes deeper on the DDD/Clean
Architecture parts that a general standard glosses over. Concept-level DDD / SOLID / Clean
Architecture canon lives in `code-standards/software-architecture` and its references; this
file only maps those concepts onto Rust.

## How to use this file

Read the relevant reference file(s) before writing or reviewing code — don't rely on summary
recall for the parts that matter:

| Task focus | Reference file |
|---|---|
| Design pattern → Rust idiom translations, SOLID in Rust, Clean Code specifics, testing strategy | `patterns-and-testing.md` |
| The three genuinely hard, unsettled problems: typestate vs. persistence, transactions across the port boundary, async traits + `dyn` | `deep-dives.md` |

Load `deep-dives.md` **before** advising on any of: a state machine that must be persisted to
a database, a repository/Unit-of-Work design that spans multiple aggregates, or any trait
that needs to become `Arc<dyn Trait>` while also being `async`. These are exactly the spots
where a plausible-sounding answer is often wrong, and where this codebase's source material
found the community itself disagrees.

## Epistemic calibration — read this before asserting anything

The guidance below is stratified into three tiers. Preserve that stratification when you
apply it — don't flatten a contested tradeoff into a confident MUST, and don't present a
version-sensitive fact as timeless.

- **Settled / mainstream** — parse-don't-validate value objects; entity=identity vs
  VO=structural equality; `thiserror` for typed/matchable errors + `anyhow` at the edges;
  ports as traits owned by the consumer; manual composition-root wiring over DI frameworks;
  separate persistence structs mapped via `From`/`TryFrom`; enums + exhaustive `match` for
  domain events; "don't write Java in Rust" as a real anti-pattern family. State these plainly.
- **Genuinely contested — present as a tradeoff, not a verdict:** static (generics) vs
  dynamic (`Arc<dyn Trait>`) dispatch for DI; crate-per-layer vs module-per-layer; `mockall`
  vs hand-written in-memory fakes; how to handle transactions across a repository trait;
  whether a `reconstruct` constructor should re-validate invariants or trust the database.
  When one of these comes up, say what the tradeoff actually is and let the project's
  constraints (team size, compile times, whether a second implementation/fake exists) decide
  — don't manufacture a fake consensus.
  Note that even where an *answer* is reasonably settled (e.g. "transaction inside the
  repository, one aggregate per use case" as the default), the *how* to do the exception case
  well remains contested — keep both halves.
- **Version-sensitive — verify before relying on:** exact crate versions and API surfaces
  (`dynosaur`, `async-trait`, `trait_variant`, `shaku`, `thiserror`, `sqlx`, `proptest`,
  `derive_builder`, `bon`) and the exact stable/dyn-compatibility status of `async fn` in
  traits. Rust ships fast; tell the user to check crates.io/docs.rs and the Rust release notes
  for their toolchain rather than asserting a version number from memory.

## Value objects: parse, don't validate

The organizing principle for any domain primitive that carries an invariant (an email, a
quantity, a price, a non-empty name): wrap it in a newtype with a **private field** and a
**fallible smart constructor**, never a bare public field.

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

impl Email {
    pub fn new(raw: String) -> Result<Self, EmailError> {
        if is_valid(&raw) { Ok(Self(raw)) } else { Err(EmailError::Invalid(raw)) }
    }
    pub fn as_str(&self) -> &str { &self.0 }
}
impl TryFrom<String> for Email {
    type Error = EmailError;
    fn try_from(raw: String) -> Result<Self, Self::Error> { Self::new(raw) }
}
```

Two rules that are easy to violate by reflex and that quietly destroy the guarantee:

- **Never derive `Default`** on an invariant-bearing newtype — `Email::default()` produces a
  value that never went through `new()`.
- **Never `impl Deref<Target = Inner>`** on it. `Deref` is for smart pointers (`Box`, `Rc`);
  on a safety newtype it "undoes the entire point of distinguishing them" by letting every
  inner-type method leak through unchecked.
- **Serde caveat:** a naive `#[derive(Deserialize)]` or `#[serde(transparent)]` bypasses the
  constructor entirely on deserialization. If the type must deserialize, route it through
  `#[serde(try_from = "String")]` so it goes through `TryFrom` — or better, keep serde off
  domain types altogether and deserialize into a separate DTO (see Persistence below).

Recognize the limits honestly: when the type system can't encode the invariant (e.g.
"integer between 1 and 100"), the newtype is a validator wearing a parser's clothes — it's
still worth doing, but don't oversell the guarantee. Treat any residual
`expect("should be unreachable")` as something to be nervous about, not routine.

## Entities vs value objects: equality

- **Value objects** get `#[derive(PartialEq, Eq)]` over every field — two instances with the
  same data are interchangeable.
- **Entities** get a hand-written `PartialEq` that compares **only the id field**. An entity
  with the same id but different attributes at two points in time is still the same entity —
  structural equality would be wrong here.

## Aggregates: ownership as the consistency boundary

Rust's ownership model maps onto DDD's aggregate boundary more directly than in a GC'd
language:

- The aggregate root **owns** its children by value (`Vec<LineItem>`, not `Arc<LineItem>`),
  with private fields — so all mutation is forced through root methods, and the compiler
  itself enforces "external code only references the root."
- **Reference other aggregates by ID**, not by `Arc<OtherAggregate>` — `customer_id:
  CustomerId`, never `Arc<Customer>`. Holding a live reference to another aggregate invites
  exactly the shared-mutable-state problem aggregates exist to prevent.

**The reconstitution problem is real, not hypothetical.** Loading an aggregate from storage
must not re-run creation invariants — the row already represents valid history, and
re-validating it can reject legitimately-persisted state (or re-trigger side effects like ID
generation that should only happen once). The working pattern is two constructors with
different contracts:

```rust
impl Order {
    // Genuinely new: enforces invariants, may generate an id, can fail.
    pub fn create(id: OrderId, lines: Vec<LineItem>) -> Result<Self, OrderError> {
        if lines.is_empty() { return Err(OrderError::EmptyOrder); }
        Ok(Self { id, lines })
    }

    // Rebuilding from storage: infallible, no invariant re-checks, trusts the caller.
    pub fn reconstruct(id: OrderId, lines: Vec<LineItem>) -> Self {
        Self { id, lines }
    }
}
```

Whether `reconstruct` should stay totally unchecked (trust the database) or re-assert
invariants as a defense against bad migrations/manual data fixes is a genuine, unresolved
judgment call — pick one deliberately and document the choice rather than doing it by
accident.

## Domain events

Prefer a plain **enum** over `Box<dyn Trait>` for events within one bounded context — an
exhaustive `match` at every handler is a compile-time guarantee that no event silently goes
unhandled, which is a real advantage over the OOP observer pattern.

Mark a **published** event enum `#[non_exhaustive]` so a new variant doesn't become a
breaking change for downstream `match`es (they're forced to carry a wildcard arm already).
Don't reach for this on purely internal enums — `#[non_exhaustive]` costs ergonomics, so pay
that cost only where the enum crosses a real API boundary.

`Box<dyn Trait>` events are for the rare case of a genuinely open-ended, cross-context event
stream you can't enumerate — not the default.

## Error handling: handle vs report, not "library vs app"

The library-vs-application heuristic (`thiserror` in libraries, `anyhow` in apps — see the
main `SKILL.md`) is a useful starting rule of thumb, but the sharper question — the one that
actually determines the right choice at a given call site — is: **does the caller need to
behave differently depending on which failure happened?**

- **Yes → a typed `thiserror` enum** the caller can `match` on. This is virtually always true
  in the domain layer: a repository's "not found" and "constraint violated" are different
  responses to the caller, so they need distinct variants.
- **No, the caller only needs to report/log it → `anyhow`/`eyre`.** This is virtually always
  true at `main`, request handlers, and other edges.

```rust
#[derive(Debug, thiserror::Error)]
pub enum RepositoryError {
    #[error("no order found with id {0}")]
    NotFound(OrderId),
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),   // #[from] gives you `?`-based translation at the boundary
}
```

Practical rules: avoid `unwrap`/`expect` in domain code (reserve `panic!` for truly
unreachable invariant violations, per the Rust Book); error types should implement `Error +
Send + Sync + 'static` and `Display` (the API Guidelines' C-GOOD-ERR); don't implement the
deprecated `description()` method. Note that `thiserror`'s proc-macro expansion has a real,
measurable compile-time cost on a lean crate — negligible once the tree already uses other
proc-macros, but worth knowing before you're surprised by it on a small domain-only crate.

## Ports, adapters, and dispatch

**Ports are traits, and they're defined where they're consumed** — the domain or application
layer declares the `Repository` trait; infrastructure implements it. This is Dependency
Inversion, and it's how essentially every real Rust DDD codebase does it.

**Interface Segregation matters more here than in Java**, because a fat trait punishes test
fakes directly: every method on a wide `Repository` trait must be implemented (or
`unimplemented!()`-stubbed) in every in-memory fake you write. Keep ports narrow and
role-specific.

**Don't create a trait for a single implementation with no test-fake need.** "A trait for one
impl, just in case" is the Rust flavor of interface-itis — add the port when a second
implementation or a fake actually exists, not preemptively.

### Static vs dynamic dispatch — a real tradeoff, not a rule

| | Generics (`fn f<R: Repo>(r: R)`) | `Arc<dyn Repo>` |
|---|---|---|
| Dispatch cost | Zero — monomorphized, inlinable | vtable indirection (small, real) |
| Compile/binary size | Monomorphization bloat across call sites | One instantiation, smaller |
| Runtime implementation selection | Not possible — type fixed at compile time | Yes — pick an impl from config |
| Heterogeneous collections (`Vec<...>` of mixed impls) | Not possible | Yes |
| Async | Native `async fn` in the trait just works | See `deep-dives.md` — not dyn-compatible by default |

Default to **generics in the domain/library core** — it's zero-cost and the difference from
`dyn` rarely matters until measured. Reach for `Arc<dyn Trait>` at the **composition root**
specifically when you need runtime implementation selection (e.g. choosing Postgres vs
in-memory based on config) or a non-generic container type — that's also usually the moment
an `if`/`else` returning two different concrete types stops compiling ("`if` and `else` have
incompatible types"), which is the compiler telling you type erasure is now required, not
optional.

## Dependency wiring

**Manual composition-root wiring is the Rust community norm**, not an artifact of small
projects: construct concrete adapters in `main.rs` (or an equivalent startup module), wrap in
`Arc` where shared, inject into use-case structs directly. DI frameworks like `shaku` exist
and offer compile-time guarantees, but they are not the dominant pattern — the type system
already gives most of what a Java-style container buys, so the manual version stays legible
without a framework to learn. Verify `shaku`'s current maintenance status before recommending
it for a new project.

## Persistence: keep the ORM out of the domain

The dominant, well-attested pattern is a **separate persistence struct**, private to the
infrastructure layer, mapped to the domain type through an explicit `From`/`TryFrom`:

```rust
#[derive(sqlx::FromRow)]
struct OrderRow { id: Uuid, status: String /* … */ }   // infra-only, never leaves this module

impl TryFrom<OrderRow> for Order {
    type Error = RepositoryError;
    fn try_from(row: OrderRow) -> Result<Self, Self::Error> {
        Ok(Order::reconstruct(OrderId(row.id), /* … */))
    }
}
```

**Never put `sqlx::FromRow`, `serde`, or ORM derives directly on domain types** — that's the
"ORM bleed" this pattern exists to prevent, and it also sidesteps orphan-rule friction if
domain and infrastructure ever end up in separate crates. `sqlx` (compile-time-checked SQL,
not an ORM) is the most common choice in Rust DDD codebases; note that practitioners coming
from Hibernate/Spring-style ecosystems generally agree nothing as mature exists yet in Rust,
and several teams deliberately stay "low-level by hand" with `sqlx` rather than reach for
`SeaORM`/`Diesel` specifically to keep this mapping explicit.

## Project structure: modules first, crates when justified

- **Default: one crate, layers as modules** (`domain`, `application`, `infrastructure`), with
  the dependency direction enforced by review discipline plus `pub(crate)` visibility.
- **Escalate to crate-per-layer** only when you want the compiler to make the Dependency Rule
  a hard build error (infra genuinely cannot compile if it's not a listed dependency of
  domain), or when compile times / team ownership boundaries justify it. A Cargo workspace
  shares one `Cargo.lock` and `target/`, so "each crate recompiles everything" is largely a
  myth — the real costs are orphan-rule friction (you can't `impl` a foreign trait for a
  foreign type across the split, which is itself a reason not to put `sqlx::FromRow` on
  domain types) and the ceremony of `pub` + `Cargo.toml` wiring at each boundary.

Don't split into crates preemptively "because Clean Architecture." Start with modules; split
when a specific, concrete pain (compile time, a team boundary, wanting the compiler to police
the boundary) actually shows up.

This is the same tension the main `SKILL.md`'s feature-based module layout addresses at the
production-standards level; treat this section as the DDD-specific lens on the same decision,
not a competing structure.

## Anti-patterns: signs you're writing Java in Rust

| Smell | What's actually wrong | Rust idiom instead |
|---|---|---|
| `Arc<Mutex<dyn Trait>>` as the default for shared state | Reaching for shared-mutable-state plumbing before ownership/message-passing | Push concurrency to infrastructure; prefer channels or restructure ownership |
| Getters/setters on a value object | VOs are immutable; getters/setters imply mutable internal state that shouldn't exist | Expose behavior, not accessors; construct a new VO instead of mutating |
| A trait with exactly one implementation, "for testability later" | Interface-itis — indirection with no current payoff | Add the trait when a second impl or a fake actually exists |
| FactoryFactory-style creation ceremony | Porting a GC-language creational pattern that Rust doesn't need | Plain constructor functions, `From`/`TryFrom` |
| Reaching for `unsafe`/`Arc<Mutex<T>>` because the borrow checker "won't let you" | The design has a real ownership problem, not a language limitation | Refactor ownership/boundaries rather than fighting the checker with a hammer |

See `patterns-and-testing.md` for the fuller GoF-pattern-to-Rust-idiom table (Strategy →
closures, State → enums, Singleton → `OnceLock`/`LazyLock`, Observer → channels, etc.), SOLID
applied to Rust specifically, and the testing approach (pure aggregate tests with no mocks,
`proptest` for value-object invariants, hand-written fakes vs `mockall`, `testcontainers` +
`cargo nextest` for integration tests).
