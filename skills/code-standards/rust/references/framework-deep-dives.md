# Rust — Framework Deep-Dives

Extracted from `../SKILL.md`: the deep-dive bodies of Web APIs with Axum (§7),
Serialization with Serde (§8), Database with SQLx (§9), and Observability (§11).
Section numbers match the stubs in `SKILL.md`, so §-references resolve here.

---

## 7. Web APIs with Axum

Axum is the recommended web framework, built on Tokio and Tower.

### Router & Handlers

```rust
// src/features/users/handler.rs
use axum::{extract::{Path, State}, http::StatusCode, response::Json, Router};
use uuid::Uuid;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/users", post(create_user).get(list_users))
        .route("/users/:id", get(get_user).put(update_user).delete(delete_user))
}

async fn get_user(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<UserResponse>, AppError> {
    let user = state.user_service.get_user(UserId(id)).await?;
    Ok(Json(UserResponse::from(user)))
}

async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUserRequest>,
) -> Result<(StatusCode, Json<UserResponse>), AppError> {
    let user = state.user_service.create_user(payload.into()).await?;
    Ok((StatusCode::CREATED, Json(UserResponse::from(user))))
}
```

### State Management

```rust
// src/lib.rs — shared application state
#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub user_service: Arc<dyn UserService>,
    pub config: Arc<Config>,
}
```

- **Always wrap shared state in `Arc`.** Axum clones `State` into each handler; `Arc` ensures cheap cloning.
- **Use `Arc<dyn Trait>` for services** to allow injection of mock implementations in tests.

### Error Responses

Implement `IntoResponse` for your error type to return structured JSON errors:

```rust
// src/error.rs
use axum::{http::StatusCode, response::{IntoResponse, Response}, Json};
use serde_json::json;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("Resource not found: {0}")]
    NotFound(String),
    #[error("Unauthorized")]
    Unauthorized,
    #[error("Validation failed: {0}")]
    Validation(String),
    #[error("Internal server error")]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match &self {
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg.clone()),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, "Unauthorized".to_string()),
            AppError::Validation(msg) => (StatusCode::UNPROCESSABLE_ENTITY, msg.clone()),
            AppError::Internal(e) => {
                tracing::error!("Internal error: {:?}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error".to_string())
            }
        };
        (status, Json(json!({ "error": message }))).into_response()
    }
}
```

### Middleware with Tower

```rust
// src/main.rs
use tower_http::{cors::CorsLayer, trace::TraceLayer, timeout::TimeoutLayer};
use std::time::Duration;

let app = Router::new()
    .merge(users::router())
    .layer(
        ServiceBuilder::new()
            .layer(TraceLayer::new_for_http())
            .layer(TimeoutLayer::new(Duration::from_secs(30)))
            .layer(cors_layer())
    )
    .with_state(app_state);
```

---

## 8. Serialization with Serde

`serde` is the standard for all serialization/deserialization in Rust.

```rust
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

// ✅ Correct: separate request and response types
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateUserRequest {
    pub email: String,
    pub display_name: String,
    pub role: UserRole,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct UserResponse {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub role: UserRole,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum UserRole {
    Admin,
    Standard,
}
```

- **Use `rename_all`** to consistently convert between Rust `snake_case` and API `camelCase`.
- **Separate request and response types.** Never reuse the same struct for both deserialization and serialization if the fields differ.
- **Use `#[serde(skip_serializing_if = "Option::is_none")]`** to omit null fields from JSON output.
- **Validate after deserialization.** Axum's `Json` extractor returns 422 on malformed JSON; add domain validation in the service layer.

---

## 9. Database with SQLx

`sqlx` is the preferred async database library for its compile-time checked queries.

```rust
// src/features/users/repository.rs
use sqlx::PgPool;

pub struct PgUserRepository {
    pool: PgPool,
}

impl PgUserRepository {
    pub fn new(pool: PgPool) -> Self { Self { pool } }

    pub async fn find_by_id(&self, id: Uuid) -> Result<Option<UserRow>, sqlx::Error> {
        sqlx::query_as!(
            UserRow,
            "SELECT id, email, display_name, role, created_at FROM users WHERE id = $1",
            id
        )
        .fetch_optional(&self.pool)
        .await
    }

    pub async fn insert(&self, user: &NewUser) -> Result<UserRow, sqlx::Error> {
        sqlx::query_as!(
            UserRow,
            r#"
            INSERT INTO users (id, email, display_name, role)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, display_name, role, created_at
            "#,
            user.id,
            user.email,
            user.display_name,
            user.role as _,
        )
        .fetch_one(&self.pool)
        .await
    }
}
```

- **Use `query_as!` macros** to get compile-time verified queries and automatic mapping to structs.
- **Use `sqlx::migrate!`** for embedded migrations — run at application startup.
- **Connection pooling:** Always use `PgPool`; configure `max_connections` for production.
- **Use raw SQL over ORMs** when query complexity warrants it. Avoid N+1 queries; prefer JOINs or `IN` clauses.
- **Pagination:** Always limit result sets — never return unbounded queries.
- **Transactions:** Use `pool.begin()` → `tx.commit()` explicitly; `tx` auto-rolls back on drop if not committed.

```rust
// ✅ Correct: explicit transaction
let mut tx = pool.begin().await?;
update_user_balance(&mut tx, user_id, amount).await?;
insert_transaction_log(&mut tx, record).await?;
tx.commit().await?;
```

---

## 11. Observability (Tracing & Logging)

Use `tracing` — not `log` — for structured, async-aware instrumentation.

```rust
// Cargo.toml
[dependencies]
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

// src/main.rs
tracing_subscriber::registry()
    .with(
        tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "info".into()),
    )
    .with(tracing_subscriber::fmt::layer().json())  // structured JSON logs for production
    .init();
```

```rust
// src/features/users/service.rs
use tracing::{instrument, info, warn, error};

#[instrument(skip(self), fields(user_id = %id))]
pub async fn get_user(&self, id: UserId) -> Result<User, UserError> {
    info!("Fetching user");
    let user = self.repo.find_by_id(id).await?;
    match &user {
        None => warn!("User not found"),
        Some(u) => info!(email = %u.email, "User fetched"),
    }
    user.ok_or(UserError::NotFound(id.0))
}
```

- **`#[instrument]`** automatically creates spans for functions and records arguments.
- **Log at the right level:** `error!` for unrecoverable issues, `warn!` for expected but notable anomalies, `info!` for significant business events, `debug!` for developer diagnostics.
- **Never log secrets:** skip sensitive fields with `#[instrument(skip(password, token))]`.
- **Use `tower-http::trace::TraceLayer`** to automatically trace all HTTP requests.
