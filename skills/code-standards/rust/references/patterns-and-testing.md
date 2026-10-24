# Design patterns, SOLID, Clean Code, and testing in Rust

## Contents
1. [GoF patterns translated to Rust idiom](#1-gof-patterns-translated-to-rust-idiom)
2. [SOLID applied to Rust specifically](#2-solid-applied-to-rust-specifically)
3. [Clean Code specifics with tooling backing](#3-clean-code-specifics-with-tooling-backing)
4. [Testing strategy](#4-testing-strategy)

---

## 1. GoF patterns translated to Rust idiom

| GoF pattern | Idiomatic Rust |
|---|---|
| Strategy | A trait, a generic parameter, or — often simplest — a plain closure |
| State | An **enum** + `match` for anything that must be persisted or serialized; typestate (`PhantomData`) for in-memory/protocol state machines (see deep-dive #1) |
| Builder | A dedicated builder struct, often generated via `derive_builder` or `bon`; sometimes a typestate variant when construction has required-in-order steps |
| Singleton | `OnceLock`/`LazyLock` from `std` — no need for a hand-rolled pattern |
| Visitor | A trait over a heterogeneous AST — this one translates cleanly and stays genuinely useful |
| Factory | Plain constructor functions or `From`/`TryFrom` impls — rarely needs its own abstraction |
| Decorator | A wrapper struct implementing the same trait as the thing it wraps |
| Observer | Channels (`tokio::sync::mpsc`, `std::sync::mpsc`) rather than a list of listener objects |
| Repository | A trait (the port) + one or more adapter implementations |
| Null Object | `Option<T>` / `Option::None` — the standard library already has this pattern built in |

**A claim worth stating carefully, not overselling:** it's a defensible synthesis — not an
established, citable fact — that many GoF behavioral/creational patterns exist specifically to
work around the absence of sum types, closures, and pattern matching in the languages GoF was
written for. Strategy really does collapse cleanly into a closure; State really does collapse
into an enum. But don't present this as a universal law — structural patterns (and Mediator
in particular, which fights the borrow checker) remain awkward to express in Rust, and no
primary source makes the strong universal version of this claim.

## 2. SOLID applied to Rust specifically

- **SRP** — applies at the module/crate level in Rust more than the class level: a
  module/crate is your unit of "one reason to change."
- **OCP has a Rust-specific wrinkle:** adding a new variant to an existing enum **is a
  breaking change** for any downstream code with an exhaustive `match` on it — the opposite of
  Java, where adding a subclass doesn't break existing callers. `#[non_exhaustive]` (see
  Domain Events in the main skill file) is the escape hatch, at the cost of forcing every
  external `match` to carry a wildcard arm. "Open for extension" via enums has a real
  compatibility cost that class-based extension in other languages doesn't.
- **LSP is uncheckable by the compiler in Rust.** A trait specifies method *signatures*, not
  *behavioral contracts* — nothing stops an implementation from weakening a postcondition or
  throwing where the trait's other implementations don't. LSP compliance in Rust is entirely a
  matter of manual discipline and code review, not a language guarantee.
- **ISP** — narrow, role-specific traits keep test fakes cheap (see Ports in the main file).
- **DIP** — traits as abstractions at the boundary, but specifically *don't* invert a
  dependency where there's exactly one implementation and no need for a fake — that's
  interface-itis, not Dependency Inversion.

## 3. Clean Code specifics with tooling backing

These are backed by real lints/tooling, not just style opinion:

- `clippy::pedantic` in CI, `rustfmt` for formatting — non-negotiable baseline.
- `#![warn(missing_docs)]` to force doc coverage on public items; `#[must_use]` on
  constructors and `Result`-like return values so callers can't silently drop them.
- Avoid `unwrap`/`expect` in domain code — clippy lints (`clippy::unwrap_used`,
  `clippy::expect_used`) exist specifically to enforce this at CI time, not just by
  convention.
- **Command-Query Separation gets structural help from the borrow checker**: a `&self` method
  is a query, a `&mut self` method is a command — the distinction is enforced by the compiler,
  not just a naming convention as in most languages.
- **Avoid `Arc<Mutex<_>>` in the domain layer specifically** — its presence there is usually a
  signal that the shared-mutable-state problem aggregates + ownership are meant to design away
  has crept back in. Push concurrency concerns to infrastructure.

## 4. Testing strategy

- **Aggregate tests as pure functions, with no mocks at all.** Because an aggregate owns its
  state and exposes behavior through methods that return `Result` (and/or emit domain events),
  it can be tested as a plain value: construct it, call a method, assert on the returned
  state/error/event. This is the single biggest testing win DDD-in-Rust offers, and it needs
  no test double machinery whatsoever.
- **Hand-written in-memory fakes vs. `mockall` — a genuine judgment call, not settled.** Both
  are used in real codebases. `mockall` auto-generates mocks from a trait definition and is
  convenient across controller/use-case/repository layers. Hand-written `InMemoryRepository`
  fakes are often preferred specifically for repositories, because they're reusable stateful
  fakes rather than being coupled to a specific expected call sequence the way a generated mock
  often is. Pick based on whether you need call-sequence assertions (favors `mockall`) or a
  reusable stateful double (favors hand-written).
- **`proptest` for value-object invariants.** Generate arbitrary inputs and assert the smart
  constructor upholds its invariant (or that a round-trip through serialization preserves it);
  `proptest` shrinks failures to a minimal reproducing case automatically. `quickcheck` is the
  other mainstream option and does the same job with per-type rather than per-value
  `Strategy`s — either is a legitimate choice, this is not a meaningfully contested decision.
- **`testcontainers` + `cargo nextest` for integration tests against real infrastructure.**
  Spin up a real Postgres (or other dependency) in Docker for adapter-layer tests rather than
  mocking the database — this is where you actually validate the `From`/`TryFrom` persistence
  mapping described in the main skill file. A common pattern wraps each repository integration
  test in its own transaction that gets rolled back at the end, which both isolates tests from
  each other and lets them run in parallel safely.
- **Test naming:** no single official convention exists, but a clear community norm is
  behavior-oriented naming that reads like a sentence, e.g.
  `subscribe_returns_a_400_when_fields_are_present_but_invalid` — prefer this over
  implementation-oriented names like `test_subscribe_1`.
