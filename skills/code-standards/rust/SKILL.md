---
name: rust
description: >
  Comprehensive Rust standards for production services: ownership/borrowing idioms, typed error
  handling (thiserror/anyhow), traits and generics, Tokio async, Axum web APIs, Serde, SQLx,
  observability, testing (including database-gated integration tests), unsafe policy, and CI
  tooling — plus deep DDD/Clean Architecture references. Use whenever writing, reviewing, or
  refactoring Rust. Trigger on: "write Rust", "Rust service", "borrow checker", "lifetimes",
  "Tokio", "Axum", "SQLx", "Serde", "thiserror", "anyhow", "cargo", "clippy", "Rust DDD", "Rust
  testing", "is this idiomatic Rust", or any Rust development task.
---

# Rust Code Standards & Best Practices

As an AI assistant, you must adhere strictly to the following Rust development best practices and coding standards when generating, reviewing, or refactoring Rust code. These standards are aligned with the official Rust Book, Rust API Guidelines, Rust 2024 Edition, and community-proven patterns.

## Domain-Driven Design and Architecture

The sections below cover general production standards. For tactical DDD and Clean
Architecture in Rust — value objects, entities, aggregates, domain events, ports/adapters,
the static-vs-dynamic-dispatch and async-trait tradeoffs that trip up teams porting OOP habits
into Rust — read the dedicated reference files before designing or reviewing a Rust domain
model:

| Task focus | Reference file |
|---|---|
| Value objects, aggregates, domain events, ports/adapters, error handling philosophy, dependency wiring, persistence mapping, DDD-oriented project structure, anti-patterns | `references/domain-driven-design.md` |
| Design pattern → Rust idiom translations, SOLID in Rust, Clean Code specifics, testing strategy | `references/patterns-and-testing.md` |
| The three genuinely hard, unsettled problems: typestate vs. persistence, transactions across the port boundary, async traits + `dyn` | `references/deep-dives.md` |

Load `references/deep-dives.md` **before** advising on any of: a state machine that must be
persisted to a database, a repository/Unit-of-Work design that spans multiple aggregates, or
any trait that needs to become `Arc<dyn Trait>` while also being `async`. These are exactly
the spots where a plausible-sounding answer is often wrong, and where the community itself
disagrees.

`references/domain-driven-design.md` also carries an epistemic-calibration note (settled vs
contested vs version-sensitive guidance) — read it before asserting anything from that file
as a flat rule.

---

## 1. Project Structure

Organize code by **feature/domain** using Cargo workspaces for larger projects. Separate library logic from binary entry points.

### Single-Crate Application

```
my-app/
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── main.rs              # Binary entry point — minimal, delegates to lib
│   ├── lib.rs               # Library root — re-exports public API
│   ├── config.rs            # Configuration loading (env vars, files)
│   ├── error.rs             # Crate-level error types (thiserror)
│   │
│   ├── features/
│   │   ├── users/
│   │   │   ├── mod.rs       # Module declaration + re-exports
│   │   │   ├── handler.rs   # HTTP handlers (Axum extractors)
│   │   │   ├── service.rs   # Business logic
│   │   │   ├── repository.rs # Data access (DB queries)
│   │   │   ├── model.rs     # Domain structs
│   │   │   └── error.rs     # Feature-specific error types
│   │   └── orders/
│   │       └── ...
│   │
│   └── shared/
│       ├── middleware.rs    # Tower middleware (auth, logging)
│       ├── pagination.rs    # Reusable pagination types
│       └── validation.rs   # Shared validation helpers
│
├── tests/                   # Integration tests (separate crates)
│   ├── common/
│   │   └── mod.rs           # Shared test helpers
│   ├── users_api.rs
│   └── orders_api.rs
│
├── migrations/              # SQLx / Diesel migrations
└── Dockerfile
```

### Multi-Crate Workspace (Recommended for Large Projects)

```
workspace/
├── Cargo.toml               # Workspace root — virtual manifest
├── Cargo.lock
│
├── crates/
│   ├── domain/              # Pure domain logic — no I/O, no frameworks
│   │   └── src/lib.rs
│   ├── application/         # Use cases / application services
│   │   └── src/lib.rs
│   ├── infrastructure/      # DB, HTTP clients, external services
│   │   └── src/lib.rs
│   └── api/                 # Axum web layer (binary)
│       └── src/main.rs
│
└── tests/                   # Workspace-level integration tests
```

**Workspace `Cargo.toml`:**

```toml
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.dependencies]
# Pin to the current stable release of each crate; verify against crates.io before use.
tokio = { version = "1", features = ["full"] }
axum = "0.8"
serde = { version = "1", features = ["derive"] }
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio", "migrate"] }
thiserror = "2"
anyhow = "1"
tracing = "0.1"
```

**Key Principles:**

- **Layered Architecture:** `handler → service → repository`. Handlers parse HTTP; services orchestrate business logic; repositories handle data access.
- **`main.rs` is thin:** Keep `main.rs` minimal — bootstrap the runtime, configure dependencies, and start the server. All logic lives in `lib.rs` and modules below it.
- **One module per file:** Prefer `users/mod.rs` with sub-files over monolithic files.
- **`pub(crate)` by default:** Expose items only to the crate unless they are part of the public API.

---

## 2. Naming Conventions

Follow Rust's official naming conventions strictly:

| Item | Convention | Example |
|---|---|---|
| Types (structs, enums, traits) | `UpperCamelCase` | `UserRepository`, `PaymentMethod` |
| Functions / methods | `snake_case` | `get_user_by_id`, `calculate_total` |
| Variables / parameters | `snake_case` | `user_id`, `request_payload` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_SECS` |
| Modules / files | `snake_case` | `user_service`, `payment_handler` |
| Lifetimes | short `'a`, `'b` or descriptive `'req` | `'static`, `'conn` |
| Type parameters | single uppercase or descriptive | `T`, `E`, `Req`, `Resp` |

- **Getters** in Rust do **not** use the `get_` prefix by convention: prefer `user.name()` over `user.get_name()`.
- **Bool returns:** Use predicate names — `is_active()`, `has_permission()`, `can_withdraw()`.
- **Constructors:** Use `new()` for the primary constructor; `with_*` builder methods for optional configuration.

---

## 3. Ownership, Borrowing & Lifetimes

Rust's ownership model is the foundation of memory safety. Follow these rules:

- **Prefer borrowing over cloning.** Pass `&T` (or `&str`, `&[T]`) instead of moving or cloning when the caller still needs the value after the call.
- **Clone only when necessary.** Cloning has a cost; justify every `.clone()`. Use `Arc<T>` for shared ownership across threads.
- **Prefer immutability.** Declare bindings with `let` by default; only use `let mut` when mutation is required.
- **Avoid fighting the borrow checker.** If the borrow checker rejects your design, the design likely has a problem — refactor rather than reaching for `unsafe` or excessive `Arc<Mutex<T>>`.
- **Lifetimes:** Prefer owned types in public APIs to avoid exposing lifetime parameters to callers. Use lifetimes in structs only when the lifetime is part of the domain semantics.

```rust
// ✅ Correct: borrow, don't clone
fn send_welcome(email: &str) -> Result<(), EmailError> { ... }

// ❌ Wrong: unnecessary clone
fn send_welcome(email: String) -> Result<(), EmailError> { ... }

// ✅ Correct: use Arc for shared ownership across threads
use std::sync::Arc;
let shared_config = Arc::new(config);
tokio::spawn(async move { use_config(Arc::clone(&shared_config)).await });
```

---

## 4. Error Handling

Rust error handling is explicit and compile-time enforced. Never suppress errors silently.

### Core Rules

- **Never use `unwrap()` in production code.** It panics on `Err` or `None`. If you are certain a value is always present, use `expect()` with a reason; but prefer removing the `Option`/`Result` through proper design.
- **Never use `unwrap()` in tests either** — use `assert!(result.is_ok())` or `?` propagation instead, so tests produce meaningful failure messages.
- **Use `?` for error propagation.** Avoid deeply nested `match` arms when `?` suffices.
- **Differentiate recoverable and unrecoverable errors.** Use `Result<T, E>` for recoverable failures; `panic!` only for programming bugs (invariant violations that should never occur at runtime).
- **Never panic in libraries.** Libraries must return `Result`; let callers decide how to handle failures.

### `thiserror` — Structured Error Types (Libraries & Domain)

Use `thiserror` to define structured, match-friendly error enums with zero boilerplate:

```rust
// src/features/users/error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum UserError {
    #[error("User with id={0} not found")]
    NotFound(uuid::Uuid),

    #[error("Email address '{email}' is already registered")]
    DuplicateEmail { email: String },

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Invalid input: {0}")]
    Validation(String),
}
```

### `anyhow` — Application-Level Error Aggregation

Use `anyhow` in application/binary code for ergonomic error propagation with context:

```rust
// src/main.rs — application entry point
use anyhow::{Context, Result};

#[tokio::main]
async fn main() -> Result<()> {
    let config = Config::load()
        .context("Failed to load application configuration")?;

    let pool = PgPool::connect(&config.database_url)
        .await
        .context("Failed to connect to PostgreSQL")?;

    run_server(pool, config).await
}
```

### Hybrid Pattern (Recommended)

```
Library crates → thiserror (structured, matchable errors)
Application crates → anyhow (flexible aggregation with context)
Boundary → convert thiserror errors into anyhow via From<> / ?
```

For the sharper "handle vs report" heuristic behind this rule of thumb — which matters most
in the domain layer — see `references/domain-driven-design.md`.

### Error Conversion

Implement `From<T>` (or use `#[from]` in thiserror) to allow seamless `?` conversion:

```rust
// ✅ Correct: ? converts sqlx::Error → UserError::Database via #[from]
pub async fn find_user(&self, id: Uuid) -> Result<User, UserError> {
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_optional(&self.pool)
        .await?  // sqlx::Error automatically converts to UserError::Database
        .ok_or(UserError::NotFound(id))?;
    Ok(user)
}
```

---

## 5. Types, Traits & Generics

Rust's type system is its strongest feature. Use it to encode invariants at compile time.

### Newtype Pattern

Wrap primitives in domain-specific types to prevent mixing values of the same base type:

```rust
// ✅ Correct: different types, can't accidentally swap them
pub struct UserId(uuid::Uuid);
pub struct OrderId(uuid::Uuid);
pub struct EmailAddress(String);

impl EmailAddress {
    pub fn try_new(raw: &str) -> Result<Self, ValidationError> {
        if !raw.contains('@') {
            return Err(ValidationError::InvalidEmail(raw.to_string()));
        }
        Ok(Self(raw.to_lowercase()))
    }
    pub fn as_str(&self) -> &str { &self.0 }
}
```

### Traits

- **Define traits for polymorphism,** not for every interface. Only create a trait when you have (or expect) multiple implementations or need to write generic code against it.
- **Use `trait` objects (`dyn Trait`) sparingly.** Prefer generics over `dyn Trait` when performance matters and the set of implementations is bounded.
- **`impl Trait` in return position** (RPIT) for simple cases; `dyn Trait` in `Box<dyn Trait>` when the type is erased at runtime.
- **Blanket implementations:** Use `impl<T: Foo> Bar for T` carefully to avoid coherence issues.

For the deeper static-vs-dynamic dispatch tradeoff behind the repository pattern below —
including when `Arc<dyn Trait>` is actually the right call — see
`references/domain-driven-design.md`.

```rust
// ✅ Correct: trait repository abstraction for testability
#[async_trait::async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: UserId) -> Result<Option<User>, RepositoryError>;
    async fn save(&self, user: &User) -> Result<(), RepositoryError>;
}

pub struct PgUserRepository { pool: PgPool }

#[async_trait::async_trait]
impl UserRepository for PgUserRepository {
    async fn find_by_id(&self, id: UserId) -> Result<Option<User>, RepositoryError> { ... }
    async fn save(&self, user: &User) -> Result<(), RepositoryError> { ... }
}
```

### Generics

- **Bound generics tightly:** Only restrict type parameters to the traits actually used in the function body.
- **Use `where` clauses** for complex multi-bound generics to improve readability.

```rust
// ✅ Correct: tight bounds with where clause
pub fn serialize_response<T>(payload: T) -> JsonResponse
where
    T: Serialize + Send + 'static,
{ ... }
```

### Enums over Bool Parameters

```rust
// ❌ Wrong: bool arguments are unreadable at call sites
fn create_user(email: &str, is_admin: bool) { ... }
create_user("a@b.com", true); // what does `true` mean?

// ✅ Correct: enum documents intent
enum UserRole { Admin, Standard }
fn create_user(email: &str, role: UserRole) { ... }
create_user("a@b.com", UserRole::Admin);
```

---

## 6. Async / Await with Tokio

Rust's async is cooperative and poll-based. Tokio is the standard async runtime.

### Core Rules

- **Never block inside an `async fn`.** Blocking the executor thread starves other tasks.
  - ❌ Forbidden: `std::thread::sleep()`, `std::fs::read()`, CPU-heavy loops in `async fn`
  - ✅ Use: `tokio::time::sleep()`, `tokio::fs::read()`, `tokio::task::spawn_blocking()`
- **`async fn main()` via `#[tokio::main]`** is the standard entry point. Use `tokio::runtime::Builder` only when you need custom runtime configuration.
- **Do not hold `std::sync::Mutex` across `await` points.** Use `tokio::sync::Mutex` for async-compatible locking or restructure to release the lock before awaiting.
- **Prefer structured concurrency:** `tokio::join!` for concurrent independent futures; `tokio::select!` for racing or cancellation.
- **Always handle `JoinHandle` results.** Spawned tasks can panic; check `task.await` for errors.

```rust
// ✅ Correct: concurrent independent operations
let (user, orders) = tokio::join!(
    user_service.get_user(user_id),
    order_service.get_orders(user_id),
);

// ✅ Correct: offload blocking work to dedicated thread pool
let result = tokio::task::spawn_blocking(|| {
    expensive_cpu_computation(&data)  // runs on a dedicated blocking thread
}).await?;

// ❌ Wrong: blocking inside async
async fn bad_handler() {
    std::thread::sleep(Duration::from_secs(1)); // blocks the executor!
}
```

### Cancellation Safety

- Futures in Rust are cancelled by dropping them. When using `tokio::select!`, any branch that is not selected is **dropped**.
- Design futures to be cancellation-safe (no partial state mutations) or use `tokio::sync::CancellationToken` for cooperative cancellation.

---

## 7. Web APIs with Axum

Full deep-dive (router/handler layout, `AppState`, `IntoResponse` error mapping, the Tower
middleware stack) lives in `references/framework-deep-dives.md` — load it before writing
or reviewing Axum code. Orientation: Axum (on Tokio + Tower) is the recommended web
framework; handlers return `Result<_, AppError>` where `AppError: IntoResponse`; shared
state is a `Clone` struct of `Arc`-wrapped services injected via `State`.

---

## 8. Serialization with Serde

Full deep-dive (request/response type split, `rename_all` conventions, enum
representations) lives in `references/framework-deep-dives.md` — load it before designing
API types. Orientation: serde is the standard for all (de)serialization; keep separate
request and response types, use `#[serde(rename_all = "camelCase")]` at the API boundary,
and run domain validation after deserialization.

---

## 9. Database with SQLx

Full deep-dive (compile-time-checked `query_as!` repositories, transactions, pooling and
pagination rules) lives in `references/framework-deep-dives.md` — load it before writing
repository/SQL code. Orientation: sqlx `query_as!` gives compile-time-verified SQL; use
`PgPool`, `sqlx::migrate!` at startup, explicit `pool.begin()` → `tx.commit()`
transactions, and always paginate. Database-gated integration testing for SQLx code lives
in §13 (Testing Standards), which remains in this file.

---

## 10. Configuration & Environment Variables

```rust
// src/config.rs
use anyhow::{Context, Result};

#[derive(Debug, Clone)]
pub struct Config {
    pub database_url: String,
    pub server_host: String,
    pub server_port: u16,
    pub jwt_secret: String,
    pub log_level: String,
}

impl Config {
    pub fn load() -> Result<Self> {
        dotenvy::dotenv().ok(); // loads .env file if present (non-fatal)

        Ok(Config {
            database_url: std::env::var("DATABASE_URL")
                .context("DATABASE_URL must be set")?,
            server_host: std::env::var("SERVER_HOST")
                .unwrap_or_else(|_| "0.0.0.0".to_string()),
            server_port: std::env::var("SERVER_PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()
                .context("SERVER_PORT must be a valid port number")?,
            jwt_secret: std::env::var("JWT_SECRET")
                .context("JWT_SECRET must be set")?,
            log_level: std::env::var("LOG_LEVEL")
                .unwrap_or_else(|_| "info".to_string()),
        })
    }
}
```

- **Never hardcode secrets** or environment-specific values in source code.
- **Fail fast on startup** if required configuration is missing — use `.context()` to produce actionable error messages.
- **Document every env var** in a `.env.example` file committed to the repo.

---

## 11. Observability (Tracing & Logging)

Full deep-dive (subscriber setup, `#[instrument]` usage, log-level guidance) lives in
`references/framework-deep-dives.md` — load it before adding instrumentation.
Orientation: use `tracing` (never `log`) with an env-filtered JSON subscriber in
production; `#[instrument]` spans on service functions, skip secret fields, and
`tower-http`'s `TraceLayer` for HTTP request traces.

---

## 12. Security Best Practices

- **No secrets in source control.** Use environment variables or a secrets manager (Vault, AWS SSM).
- **CORS:** Configure `tower-http::cors::CorsLayer` with an explicit allow-list. Never use wildcard origins in production.
- **Authentication:** Validate JWTs in a Tower middleware layer before requests reach handlers. Use `jsonwebtoken` crate.
- **Password hashing:** Use `argon2` or `bcrypt` crates. Never store plain-text passwords. Never use MD5/SHA1 for passwords.
- **Input validation:** Validate all input at the API boundary. Use types to enforce invariants (Newtype pattern, `try_new()` constructors).
- **SQL Injection:** `sqlx` macros use parameterized queries — never string-concatenate user input into SQL.
- **`unsafe` code policy:** Minimize and isolate all `unsafe` blocks. Every `unsafe` block **must** have a comment explaining why it is safe.
- **Dependency auditing:** Run `cargo audit` in CI to detect known CVEs in dependencies.
- **Rate limiting:** Apply rate limiting middleware (e.g., `tower-governor`) to sensitive endpoints (auth, registration).

---

## 13. Testing Standards

### Unit Tests

Place unit tests in the same file as the code under test within a `#[cfg(test)]` module:

```rust
// src/features/users/service.rs

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use tokio;

    #[tokio::test]
    async fn test_get_user_not_found_returns_error() {
        let mut mock_repo = MockUserRepository::new();
        mock_repo
            .expect_find_by_id()
            .returning(|_| Ok(None));

        let service = UserService::new(Arc::new(mock_repo));
        let result = service.get_user(UserId(Uuid::new_v4())).await;

        assert!(matches!(result, Err(UserError::NotFound(_))));
    }
}
```

### Integration Tests

Place integration tests in the `tests/` directory; they test the public API only:

```rust
// tests/users_api.rs
use axum_test::TestServer;

#[tokio::test]
async fn test_create_user_returns_201() {
    let server = setup_test_server().await;

    let response = server
        .post("/api/v1/users")
        .json(&serde_json::json!({
            "email": "test@example.com",
            "displayName": "Test User",
            "role": "standard"
        }))
        .await;

    response.assert_status_created();
    let body = response.json::<serde_json::Value>();
    assert_eq!(body["email"], "test@example.com");
}
```

### Testing Rules

- **`cargo test` green before every commit.** No exceptions.
- **Use `#[tokio::test]`** for async test functions.
- **Mock repositories with `mockall`** to isolate service-layer unit tests from the database.
- **Use real test databases** for repository integration tests. Use a separate `TEST_DATABASE_URL`.
- **Three test layers:**
  1. **Unit:** service logic with mocked repositories
  2. **Integration:** full HTTP round-trip with a real test database
  3. **Doc tests:** examples in `///` doc comments must compile and pass
- **Test naming:** `test_<method_name>_<scenario>_<expected>` — e.g., `test_find_user_unknown_id_returns_not_found`.

### Database-gated integration tests

- **Gate SQL-touching tests on an env var, and make the skip loud.** Keep them in one
  `tests/pg_store.rs`-style suite that reads `<APP>_TEST_DB_URL` at the top; when it's unset,
  print a visible "`<APP>_TEST_DB_URL` not set — skipping Postgres tests" line and return.
  Never skip silently — a suite that quietly runs zero tests looks green while proving nothing.
- **Run the gated suite sequentially** (a single test entry point, or `--test-threads=1`) when
  its tests share destructive state in one database.
- **Split ports so the fake/real boundary is principled.** Behavioural invariants (service
  logic, contract rules) depend on narrow read-port traits with in-memory fakes and stay in the
  default `cargo test` run. Write paths whose correctness IS the SQL — unique-index claim
  races, `ON CONFLICT` arbitration, FK enforcement — stay on the concrete store and are tested
  only in the gated suite. The split criterion: *what would this test prove against a fake?*
  When the subject is the database's arbitration, a mock passing proves nothing.

---

## 14. Documentation

- **Every public item must have a `///` doc comment.** Include a description, key parameters, return value, and errors.
- **Doc tests:** Code examples in doc comments are compiled and run by `cargo test`. Keep them accurate and runnable.
- **Use `# Examples`, `# Errors`, `# Panics`** sections for completeness.

```rust
/// Fetches a user by their unique identifier.
///
/// # Arguments
///
/// * `id` - The unique identifier of the user to fetch.
///
/// # Returns
///
/// The `User` domain object if found.
///
/// # Errors
///
/// Returns [`UserError::NotFound`] if no user with the given ID exists.
/// Returns [`UserError::Database`] if the database query fails.
///
/// # Examples
///
/// ```rust,no_run
/// # async fn example(service: UserService) -> Result<(), Box<dyn std::error::Error>> {
/// let user = service.get_user(UserId(uuid::Uuid::new_v4())).await?;
/// println!("{}", user.email);
/// # Ok(())
/// # }
/// ```
pub async fn get_user(&self, id: UserId) -> Result<User, UserError> { ... }
```

---

## 15. Performance

- **Avoid unnecessary allocations.** Prefer `&str` over `String`, `&[T]` over `Vec<T>` in function signatures.
- **Use `smallvec` or `arrayvec`** for small, fixed-maximum-size collections to avoid heap allocation.
- **Prefer iterators over manual loops.** Iterator chains are lazy and often better optimized by the compiler.
- **Zero-cost abstractions are real:** Generics monomorphize at compile time — use them freely for abstraction.
- **Profile before optimizing.** Use `perf`, `flamegraph`, or `cargo-flamegraph` to identify actual bottlenecks.
- **Avoid `Arc<Mutex<T>>` for hot paths.** Use message passing (`tokio::sync::mpsc`) or lock-free structures instead.
- **Connection pool sizing:** Set `max_connections` on `PgPool` based on your database server limits and concurrency needs (typically 2–4 × CPU cores for I/O-bound workloads).

---

## 16. Unsafe Code Policy

```rust
// ✅ Correct: unwrap() is justified, unsafe is documented
// SAFETY: We know `slice` is non-empty because we checked `!slice.is_empty()` above.
let first = slice.first().unwrap();

// ✅ Correct: every unsafe block has a SAFETY comment
unsafe {
    // SAFETY: `ptr` is non-null and points to a valid `T` because it was
    // created from a `Box<T>` via `Box::into_raw()` and has not been freed.
    let value = &*ptr;
}
```

- **Minimize `unsafe`.** Every `unsafe` block must have a `// SAFETY:` comment explaining the invariants that make it safe.
- **Isolate `unsafe` behind safe abstractions.** Never expose raw pointers in public APIs.
- **Prefer safe crates** over writing your own `unsafe` code (e.g., use `bytes`, `memmap2`, `bytemuck`).
- **Run `cargo miri test`** in CI to catch undefined behavior in unsafe code.

---

## 17. Tooling & CI

### Required Tooling Table

| Tool | Purpose | Command |
|---|---|---|
| `rustfmt` | Opinionated code formatting | `cargo fmt` |
| `clippy` | Idiomatic linting (warnings → errors in CI) | `cargo clippy -- -D warnings` |
| `cargo audit` | Security vulnerability scanning | `cargo audit` |
| `cargo miri` | UB detection in unsafe code | `cargo miri test` |
| `cargo tarpaulin` | Code coverage reporting | `cargo tarpaulin --out Xml` |
| `cargo nextest` | Faster test runner | `cargo nextest run` |
| `cargo outdated` | Check for outdated dependencies | `cargo outdated` |
| `cargo deny` | License & dependency policy enforcement | `cargo deny check` |
| `tokio-console` | Async task profiler/debugger | (runtime instrumentation) |

### `rustfmt.toml` (recommended)

```toml
edition = "2024"
max_width = 100
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
```

### `clippy.toml` / `#![deny]` in `lib.rs`

```rust
// src/lib.rs — enforce at compile time
#![deny(
    clippy::all,
    clippy::pedantic,
    clippy::unwrap_used,       // ban unwrap in production code
    clippy::expect_used,       // require justification for expect
    clippy::panic,             // ban panic! in library code
    missing_docs,              // require doc comments on public items
)]
#![allow(clippy::module_name_repetitions)] // acceptable in domain modules
```

### Minimal CI Pipeline (GitHub Actions example shape)

```yaml
# .github/workflows/ci.yml
jobs:
  check:
    steps:
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
      - run: cargo audit
      - run: cargo nextest run
      - run: cargo tarpaulin --out Xml
```

---

## 18. Documentation & doc comments (rustdoc)

Public items are documented with `///`; rustdoc builds the reference and **runs the examples as tests**.
- `///` outer doc on every public `fn`, `struct`, `enum`, `trait`, and module (`//!` for module/crate-level).
- First line is a one-sentence summary; follow with sections (`# Examples`, `# Errors`, `# Panics`, `# Safety`).
- Every public API's `# Examples` block is a **doc-test** — it must compile and pass (`cargo test --doc`); this is the cheapest drift guard.
- `#![deny(missing_docs)]` on public crates to enforce coverage.

Cross-cutting doc discipline (drift, when to update): see `documenting-code`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `unwrap()` in production or test code | Propagate with `?`, handle explicitly, or use `expect()` with a reason |
| Taking `String`/`Vec<T>` by value when the caller still needs it | Borrow — `&str`, `&[T]` |
| Blocking inside `async fn` (`std::thread::sleep`, `std::fs::read`, CPU-heavy loops) | `tokio::time::sleep`, `tokio::fs`, `tokio::task::spawn_blocking` |
| Holding `std::sync::Mutex` across an `await` point | `tokio::sync::Mutex`, or release the lock before awaiting |
| Raw `Uuid`/`String`/`i64` for domain keys | Newtype pattern (`UserId`, `EmailAddress`) with `try_new()` validation |
| Bool function parameters (`create_user(email, true)`) | An enum that documents intent (`UserRole::Admin`) |
| One struct serving both request deserialization and response serialization | Separate request and response types |
| `panic!` in library code for recoverable failures | Return `Result` and let callers decide |
| String-concatenating user input into SQL | Parameterized `sqlx` query macros |
| Wildcard CORS origins in production | Explicit allow-list in `CorsLayer` |
| Hardcoded secrets or environment-specific values in source | Env vars / secrets manager; fail fast on startup with `.context()` |
| `unsafe` block without a `// SAFETY:` comment | Document the invariants; isolate `unsafe` behind safe abstractions |
| `Arc<Mutex<T>>` on hot paths | Message passing (`tokio::sync::mpsc`) or lock-free structures |
| Unbounded queries returning entire result sets | Always paginate / limit |

---

## Pre-flight checklist — run before delivering any Rust code

Before finalizing any Rust code, verify:

- [ ] **No `unwrap()` in production paths** — all errors are propagated or explicitly handled
- [ ] **`thiserror` used for domain/library errors,** `anyhow` used at the application layer
- [ ] **No blocking calls inside `async fn`** — use `tokio::task::spawn_blocking` when needed
- [ ] **Newtype pattern for domain IDs and value objects** — no raw UUID/String/i64 for domain keys
- [ ] **Separate request/response types** — no struct serves dual deserialization + serialization
- [ ] **State wrapped in `Arc`** — shared Axum state is cheaply cloneable
- [ ] **All `unsafe` blocks have `// SAFETY:` comments**
- [ ] **Repository trait abstraction** — services depend on traits, not concrete implementations
- [ ] **`#[cfg(test)]` unit tests** co-located with code; integration tests in `tests/`
- [ ] **Every public symbol has `///` doc comment**
- [ ] **`cargo fmt`, `cargo clippy -- -D warnings`, `cargo test` all pass**
- [ ] **No secrets or environment-specific values in source code**
- [ ] **`cargo audit` clean** — no known CVEs in dependency tree
