# FastAPI Standards

Apply these FastAPI standards whenever generating, reviewing, or refactoring FastAPI code — they
are aligned with the official FastAPI documentation, PEP 8, and community-proven patterns.

General Python style (PEP 8/20/257, naming, type hints, docstrings, exceptions, idioms) is
covered by the parent `../SKILL.md` — read it first. This file only covers what's specific
to FastAPI, including its production/operational side (app factory and lifespan wiring, auth
patterns, transactional service layer, ASGI test transport).

---

## 1. Project Structure

Organize code by **feature/domain**, not by file type. Avoid putting all code in a single `main.py`.

```
project/
├── app/
│   ├── main.py                  # App factory, lifespan, router registration
│   ├── config.py                # Settings via pydantic-settings
│   ├── dependencies.py          # Shared FastAPI dependencies
│   ├── database.py              # Async engine + session factory
│   │
│   ├── features/
│   │   ├── heroes/
│   │   │   ├── router.py        # APIRouter with endpoint definitions
│   │   │   ├── schemas.py       # Pydantic request/response models
│   │   │   ├── models.py        # SQLAlchemy ORM models
│   │   │   ├── service.py       # Business logic (orchestration)
│   │   │   ├── repository.py    # DB query logic (data access layer)
│   │   │   ├── dependencies.py  # Feature-specific FastAPI dependencies
│   │   │   └── exceptions.py    # Feature-specific custom exceptions
│   │   └── users/
│   │       └── ...
│   │
│   └── shared/
│       ├── exceptions.py        # Global exception handlers
│       ├── pagination.py        # Reusable pagination schemas
│       └── security.py          # Auth utilities (hashing, JWT)
│
├── tests/
│   ├── conftest.py
│   ├── features/
│   │   └── heroes/
│   │       ├── test_service.py
│   │       └── test_router.py
│   └── factories.py
│
├── alembic/                     # Database migrations
├── pyproject.toml
└── Dockerfile
```

**Key Principles:**

- **Layered Architecture:** `router → service → repository`. Routers handle HTTP; services handle business logic; repositories handle DB queries.
- **Service Layer:** Business logic lives in `service.py`. Routers must not contain business logic.
- **Repository Pattern:** All database interactions are encapsulated in `repository.py` functions. Services call repositories, never SQLAlchemy directly.

---

## 2. Pydantic Schemas (v2)

FastAPI uses Pydantic v2. All request/response data must be validated through Pydantic schemas.

- **Separate Models per Operation:** Define distinct schemas for Create, Read, and Update operations (e.g., `HeroCreate`, `HeroRead`, `HeroUpdate`). Never reuse schemas that expose different fields.
- **Never Return ORM Models Directly:** Always return a Pydantic `Read` schema from endpoints, never a raw SQLAlchemy model.
- **Use `model_config`:** Configure serialization behavior (e.g., `from_attributes=True` for ORM mode) via `model_config = ConfigDict(from_attributes=True)`.
- **Field Validation:** Use Pydantic's `Field()` to add constraints (`min_length`, `max_length`, `gt`, `ge`, `regex`, description, examples).
- **Settings via `pydantic-settings`:** Use `BaseSettings` for all application configuration loaded from environment variables.
- **`model_validate_json()` over `model_validate(json.loads(...))`:** For JSON payloads, the former is faster as it avoids the intermediate dict.

```python
# ✅ Correct: Separate schemas, ORM mode, field constraints
from pydantic import BaseModel, Field, ConfigDict
import uuid

class HeroBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="The hero's name")
    power_level: int = Field(..., ge=1, le=3, description="Power level from 1 (Low) to 3 (High)")

class HeroCreate(HeroBase):
    team_id: uuid.UUID

class HeroRead(HeroBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    team_name: str

class HeroUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    power_level: int | None = Field(None, ge=1, le=3)
```

---

## 3. Async Programming (`async`/`await`)

FastAPI is built on ASGI. Correct use of `async`/`await` is critical for performance.

- **`async def` for I/O-bound endpoints:** All path operations hitting a database, external API, or file system must be `async def`.
- **`def` for CPU-bound work:** Use regular `def` for pure computation. FastAPI runs these in a thread pool automatically.
- **Never block the event loop:** Never call blocking code (e.g., `requests.get()`, `time.sleep()`, synchronous file I/O) inside an `async def`. Use `httpx.AsyncClient`, `asyncio.sleep()`, and `aiofiles` instead.
- **Run blocking code with `run_in_executor`:** If you must call a blocking library from async context, use `asyncio.get_event_loop().run_in_executor()`.
- **`asyncio.gather()`:** Use it to run multiple independent async operations concurrently.

```python
# ✅ Correct: Fully async endpoint
@router.get("/{hero_id}", response_model=HeroRead)
async def get_hero(
    hero_id: uuid.UUID,
    service: HeroService = Depends(get_hero_service),
) -> HeroRead:
    return await service.get_hero(hero_id=hero_id)

# ❌ Wrong: Blocking call inside async context
@router.get("/{hero_id}")
async def get_hero(hero_id: int):
    response = requests.get(f"https://external.api/{hero_id}")  # BLOCKS the event loop!
    return response.json()
```

---

## 4. Database with Async SQLAlchemy

- **`create_async_engine`:** Always use the async engine with an async-compatible driver (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite).
- **`AsyncSession` via Dependency:** Yield an `AsyncSession` per-request using a FastAPI dependency. Never share sessions across requests.
- **`expire_on_commit=False`:** Set this when creating `async_sessionmaker` to avoid lazy-load errors after commit in async contexts.
- **`await` all DB calls:** Every ORM call (`session.execute()`, `session.commit()`, `session.get()`) must be awaited.
- **Use `select()` from `sqlalchemy`:** Use SQLAlchemy 2.0 style `select(Model).where(...)` statements, not the legacy `.query()` API.
- **Connection Pooling:** Configure `pool_size` and `max_overflow` on the engine for production.
- **Migrations with Alembic:** Use Alembic for all schema migrations. Never use `Base.metadata.create_all()` in production.

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# app/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 5. Dependency Injection

FastAPI's `Depends()` system is the backbone of clean, testable, reusable service composition.

- **Use `Depends()` for:** DB sessions, current user, permission checks, pagination params, rate limiters.
- **Keep Dependencies Focused:** Each dependency should do one thing. Avoid putting business logic in dependencies.
- **Chain Dependencies:** Dependencies can themselves declare dependencies — use this for composing layered auth/authz checks.
- **Use `Annotated` Pattern (FastAPI ≥ 0.95):** Prefer `Annotated[Type, Depends(fn)]` for cleaner function signatures.

```python
# ✅ Correct: Clean layered dependencies with Annotated
from typing import Annotated
from fastapi import Depends
from app.dependencies import get_db
from app.features.users.service import get_current_user
from app.features.heroes.service import HeroService

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

def get_hero_service(db: DB) -> HeroService:
    return HeroService(db=db)

HeroServiceDep = Annotated[HeroService, Depends(get_hero_service)]

@router.get("/{hero_id}", response_model=HeroRead)
async def get_hero(
    hero_id: uuid.UUID,
    current_user: CurrentUser,
    service: HeroServiceDep,
) -> HeroRead:
    return await service.get_hero(hero_id=hero_id, user=current_user)
```

---

## 6. Routing & API Design

- **Use `APIRouter`:** Define routes in feature-specific `router.py` files. Register them in `main.py` with a prefix and tags.
- **API Versioning:** Prefix all routers with `/api/v1/` (or use sub-applications for major version splits).
- **`response_model`:** Always declare `response_model` on every endpoint for automatic serialization and OpenAPI spec accuracy.
- **`status_code`:** Explicitly declare the correct success `status_code` (e.g., `201` for creates, `204` for deletes).
- **Use `response_model_exclude_unset` / `response_model_exclude_none`:** Trim empty/null fields from responses when appropriate.

```python
# app/features/heroes/router.py
router = APIRouter(prefix="/heroes", tags=["Heroes"])

@router.post("/", response_model=HeroRead, status_code=201)
async def create_hero(payload: HeroCreate, service: HeroServiceDep) -> HeroRead:
    return await service.create_hero(data=payload)

@router.delete("/{hero_id}", status_code=204)
async def delete_hero(hero_id: uuid.UUID, service: HeroServiceDep) -> None:
    await service.delete_hero(hero_id=hero_id)

# app/main.py
from app.features.heroes.router import router as heroes_router
app.include_router(heroes_router, prefix="/api/v1")
```

---

## 7. Authentication & Authorization

- **JWT with OAuth2 Password Bearer:** Use `PyJWT` for JWT encoding/decoding and FastAPI's `OAuth2PasswordBearer` for the security scheme. Do **not** use `python-jose` — it is effectively unmaintained and carries unpatched advisories (CVE-2024-33663/33664); `PyJWT` is the library the official FastAPI security tutorial now uses. `joserfc` is the alternative when you need full JOSE/JWE, not just JWT.
- **Password Hashing:** Use `pwdlib` (Argon2 by default, with a bcrypt fallback) or hash directly with `argon2-cffi`/`bcrypt`. Do **not** use `passlib` — it is unmaintained and `passlib[bcrypt]` 1.7.4 breaks against `bcrypt` ≥ 4.1. Never store plain-text passwords.
- **Short-lived Access Tokens:** Issue access tokens with short expiry (15 min) and rotate refresh tokens.
- **Get Current User via Dependency:** Implement a `get_current_user` dependency that validates the JWT and returns the user, raising `HTTPException(401)` on failure.
- **Authentication and Authorization as Separate Dependencies:** Keep `get_current_user` ("who is this" — 401 on failure) separate from `get_current_active_user` / permission checks ("are they allowed" — 403 on failure). Collapsing them into one dependency loses the ability to return 401 vs 403 correctly; see `zeno-stack/zeno-error-handling` and `zeno-stack/zeno-api-design` for that distinction at the HTTP layer.
- **RBAC via Dependencies:** Implement role checks as dependencies (e.g., `require_admin = Depends(get_current_admin_user)`).
- **Route-level Protection:** Apply auth dependencies at router or endpoint level, never rely on obscurity.

```python
# app/shared/security.py
import jwt  # PyJWT
from pwdlib import PasswordHash
from app.config import settings

pwd_hash = PasswordHash.recommended()  # Argon2, bcrypt fallback for legacy hashes

def hash_password(password: str) -> str:
    return pwd_hash.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hash.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    return jwt.encode(
        {**data, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

# Decoding: jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
# raises jwt.ExpiredSignatureError / jwt.InvalidTokenError (both subclass jwt.PyJWTError)


# Authorization layered on top of authentication — separate dependency, 403 not 401
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user
```

---

## 8. Security Best Practices

- **No Secrets in Code:** Load all secrets (DB URL, secret keys, API keys) from environment variables using `pydantic-settings`. Never commit `.env` files with secrets.
- **HTTPS Everywhere:** Deploy behind a reverse proxy (Nginx, Traefik) that terminates TLS. Set `SECURE_*` headers.
- **CORS:** Use `CORSMiddleware` with an explicit `allow_origins` list. Never use `allow_origins=["*"]` in production.
- **Rate Limiting:** Use `fastapi-limiter` (backed by Redis) to throttle sensitive endpoints (login, register, password reset).
- **Input Validation for XSS/Injection:** Pydantic provides the first line of defense. Use `Field(regex=...)` and strict types to reject unexpected input.
- **SQL Injection Prevention:** Always use SQLAlchemy's parameterized queries. Never concatenate user input into SQL strings.
- **`DEBUG` off in production:** Never expose `debug=True` or detailed tracebacks to clients in production.
- **Avoid Verbose Error Messages:** Catch exceptions globally and return safe, sanitized error responses. Never leak stack traces.
- **Audit Logging:** Log auth events (login, logout, failed auth, permission denied) with contextual information (user, IP, timestamp).
- **Dependency Vulnerability Scanning:** Run `pip-audit` or `safety` in CI to detect known CVEs.

```python
# app/main.py — Secure CORS setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["https://app.example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 9. Error Handling

- **Use `HTTPException`** for standard HTTP errors (`404`, `403`, `422`, etc.).
- **Custom Exception Classes:** Define domain-specific exceptions (e.g., `HeroNotFoundException`) and register a global `@app.exception_handler` to convert them to consistent `HTTPException` responses.
- **Consistent Error Schema:** Define a shared Pydantic `ErrorResponse` schema for all error payloads.
- **Validation Error Handling:** FastAPI's 422 responses are automatic via Pydantic. Customize the shape via `RequestValidationError` handler if needed.
- **Never expose internals:** Catch `Exception` globally and return `500` without stack trace details in production.

```python
# app/shared/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse

class HeroNotFoundException(Exception):
    def __init__(self, hero_id: uuid.UUID):
        self.hero_id = hero_id

async def hero_not_found_handler(request: Request, exc: HeroNotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Hero {exc.hero_id} not found."})

# app/main.py
app.add_exception_handler(HeroNotFoundException, hero_not_found_handler)
```

---

## 10. Performance Optimization

#### Async & Concurrency

- Ensure all I/O is non-blocking (see Section 4).
- Use `asyncio.gather()` to run independent async tasks concurrently.
- Use `BackgroundTasks` for fire-and-forget operations (e.g., sending emails post-request).

#### Database

- **Avoid N+1 Queries:** Use `selectinload()` or `joinedload()` in SQLAlchemy to eager-load relationships.
- **Load Only What You Need:** Use `.options(load_only(...))` to fetch only required columns.
- **Pagination:** Always paginate list endpoints using `limit` / `offset` or cursor-based pagination. Never return unbounded result sets.
- **Indexing:** Add database indexes on foreign keys and filtered columns.
- **Connection Pooling:** Configure a connection pool sized appropriately for your concurrency level.

#### Caching

- **Redis Caching:** Cache expensive, read-heavy query results using `redis-py` (async) or `aiocache`.
- **Cache-Control Headers:** Set appropriate `Cache-Control` headers for public read endpoints.

#### Response

- **Use `ORJSONResponse`:** For high-throughput APIs, replace the default `JSONResponse` with FastAPI's built-in `ORJSONResponse` for faster serialization.
- **Streaming Responses:** Use `StreamingResponse` for large file downloads or server-sent events.

```python
# ✅ Correct: Parallel async calls + eager loading
async def get_hero_with_team(hero_id: uuid.UUID, db: AsyncSession) -> Hero:
    result = await db.execute(
        select(Hero).where(Hero.id == hero_id).options(selectinload(Hero.team))
    )
    return result.scalar_one_or_none()
```

---

## 11. Application Lifespan & Configuration

- **Use `@asynccontextmanager` Lifespan:** Replace deprecated `@app.on_event` startup/shutdown with the modern `lifespan` context manager to initialize/teardown resources (DB pools, Redis, ML models). Call `await engine.dispose()` on shutdown to release pooled connections.
- **App Factory:** Build the app inside a `create_app()` function rather than a module-level `app = FastAPI()`. The factory is what lets tests build a fresh app per test with `dependency_overrides` instead of mutating a shared global.
- **`pydantic-settings` for Config:** Load all configuration from environment variables with type validation. Never hardcode configuration.

```python
# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = []
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

settings = Settings()

# app/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown — release pooled connections
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="My App", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(heroes_router, prefix="/api/v1")
    return app


app = create_app()
```

---

## 12. Testing Standards

- **`pytest` + `pytest-asyncio`:** Use async test functions with `@pytest.mark.asyncio`.
- **`httpx.AsyncClient`:** Use `httpx` with `ASGITransport` for async integration tests — do NOT use `TestClient` for async endpoints.
- **Test Database:** Use a separate test database (or `aiosqlite` in-memory). Override the `get_db` dependency in tests.
- **`factory_boy` + `faker`:** Use factories for generating test data — avoid raw `insert` calls scattered throughout tests.
- **Three Test Layers:**
  1. **Unit:** `service.py` and `repository.py` functions (mock the DB session).
  2. **Integration:** Full HTTP roundtrip via `httpx.AsyncClient` against a real test DB.
  3. **Schema:** Pydantic schema validation tests for edge cases.
- **Coverage ≥ 90%** measured with `pytest-cov`.

```python
# tests/conftest.py — fresh app per test via the factory, DB swapped by override
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
```

`ASGITransport` drives the app in-process — no real socket, no server process to manage, and
`dependency_overrides` swaps the real DB session for a per-test in-memory one without touching
route code. See `zeno-stack/zeno-python-testing` for the pytest fixture and mocking
fundamentals this builds on.

```python
# tests/features/heroes/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.dependencies import get_db

@pytest.mark.asyncio
async def test_create_hero_success(db_session, auth_headers):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/heroes/",
            json={"name": "Iron Man", "power_level": 3, "team_id": "..."},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["name"] == "Iron Man"
```

---

## 13. API Documentation

- **Automatic OpenAPI:** FastAPI generates OpenAPI 3.x docs automatically. Enrich them proactively.
- **`summary` and `description` on Endpoints:** Add these to every path operation for consumer-friendly docs.
- **`response_description`:** Document the success response in each endpoint.
- **Schema `examples`:** Add `openapi_examples` or `Field(examples=[...])` to schemas for interactive docs.
- **Tags and Descriptions:** Group endpoints by router `tags` and add `openapi_tags` metadata in `main.py`.

```python
@router.get(
    "/{hero_id}",
    response_model=HeroRead,
    summary="Get a hero by ID",
    response_description="The requested hero",
)
async def get_hero(hero_id: uuid.UUID, service: HeroServiceDep) -> HeroRead:
    """Retrieve a single hero resource by its unique identifier."""
    return await service.get_hero(hero_id=hero_id)
```

---

## 14. Deployment & Tooling

#### Production Server

- **Uvicorn + Gunicorn:** Run with `gunicorn -k uvicorn.workers.UvicornWorker` for multi-worker production deployments. Use `--workers` = 2× CPU cores.
- **Docker:** Always containerize the app. Use a multi-stage Dockerfile and a non-root user.

#### Tooling Table

| Tool                  | Purpose                                            |
|-----------------------|----------------------------------------------------|
| `black`               | Opinionated code formatter                         |
| `isort`               | Import sorting                                     |
| `ruff`                | Fast linter (replaces flake8 + many plugins)       |
| `mypy`                | Static type checking                               |
| `pytest-asyncio`      | Async test runner                                  |
| `httpx`               | Async HTTP client for integration tests            |
| `factory_boy`         | Test data factories                                |
| `pydantic-settings`   | Environment variable config management             |
| `alembic`             | Database schema migrations                         |
| `asyncpg`             | High-performance async PostgreSQL driver           |
| `PyJWT`               | JWT encoding/decoding (not `python-jose` — unmaintained, CVE-2024-33663/33664) |
| `pwdlib[argon2]`      | Password hashing (not `passlib` — unmaintained, breaks vs bcrypt ≥ 4.1) |
| `fastapi-limiter`     | Rate limiting via Redis                            |
| `pip-audit`           | Security vulnerability scanning                    |
| `pre-commit`          | Git hook runner for linting/formatting enforcement |

Configure `black`, `isort`, `ruff`, and `mypy` in `pyproject.toml`. Enforce via `pre-commit` hooks and CI pipeline.

---

## 15. Transactional Service Layer & Race-Safe Writes

- **Let the DB enforce uniqueness:** Rely on the database's atomic unique constraint rather than a race-prone application-level "check then insert". Catch `IntegrityError`, roll back, and translate it into a domain exception the router maps to an HTTP status.
- **Constraint must actually exist:** Application-level duplicate handling only works if the underlying column has a unique index (`unique=True` on the mapped attribute). Without the DB constraint, catching `IntegrityError` can't prevent a concurrent race — there is nothing to race against.
- **Deterministic ordering before pagination:** Always apply an explicit `.order_by(...)` before `.offset().limit()` — without it, offset/limit pagination is not guaranteed stable across requests.

```python
# app/features/users/service.py
class DuplicateUserError(Exception):
    """Raised when a unique user field conflicts with an existing row."""


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: UserCreate) -> User:
        user = User(email=payload.email, username=payload.username,
                    hashed_password=hash_password(payload.password))
        self.db.add(user)
        try:
            # Rely on the DB's atomic unique constraint rather than a race-prone
            # application-level "check then insert"
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateUserError from exc
        await self.db.refresh(user)
        return user

    async def list(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        total = (await self.db.execute(select(func.count(User.id)))).scalar_one()
        # Explicit ordering — without it, offset/limit pagination is not guaranteed stable
        result = await self.db.execute(select(User).order_by(User.id).offset(skip).limit(limit))
        return list(result.scalars()), total
```

The router stays thin: it delegates to the service and translates the small set of domain
exceptions into HTTP status codes (e.g., `DuplicateUserError` → `HTTPException(400)`). No
business logic in the handler body.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| All code in a single `main.py`, organized by file type | Feature/domain structure with `router → service → repository` layers |
| Business logic inside routers | Keep it in `service.py`; routers handle HTTP only |
| Services calling SQLAlchemy directly | Encapsulate all DB queries in `repository.py` |
| One Pydantic schema reused for Create/Read/Update | Distinct schemas per operation (`HeroCreate`, `HeroRead`, `HeroUpdate`) |
| Returning raw SQLAlchemy models from endpoints | Return a Pydantic `Read` schema (`from_attributes=True`) |
| Blocking calls (`requests.get()`, `time.sleep()`, sync file I/O) inside `async def` | `httpx.AsyncClient`, `asyncio.sleep()`, `aiofiles`, or `run_in_executor` |
| Sharing a DB session across requests | Yield an `AsyncSession` per-request via a dependency |
| Legacy `.query()` API | SQLAlchemy 2.0 style `select(Model).where(...)` |
| `Base.metadata.create_all()` in production | Alembic migrations |
| `allow_origins=["*"]` in production CORS | Explicit `allow_origins` allowlist |
| Secrets hardcoded or committed in `.env` | `pydantic-settings` loading from environment variables |
| Storing plain-text passwords, or hashing with unmaintained `passlib`/`python-jose` | `pwdlib` (Argon2) for hashing, `PyJWT` for tokens |
| Leaking stack traces / verbose error details to clients | Global exception handlers returning safe, sanitized responses |
| N+1 queries and unbounded list responses | Eager-load with `selectinload()`/`joinedload()`; always paginate |
| Deprecated `@app.on_event` startup/shutdown | `@asynccontextmanager` `lifespan` context manager |
| Paginated query with no `ORDER BY` | Explicit `.order_by(Model.id)` before `.offset().limit()` |
| Catching `IntegrityError` with no unique DB constraint backing it | Add `unique=True` on the mapped column; the DB, not the app, must enforce the race-free guarantee |
| Single dependency doing both authentication and authorization | Separate `get_current_user` (401) from `get_current_active_user`/permission check (403) |
| Module-level `app = FastAPI()` mutated by tests | `create_app()` factory + `dependency_overrides` on a fresh app per test |

---

## Pre-flight checklist — run before delivering any FastAPI code

When writing or reviewing FastAPI code, verify:

- [ ] **Layering**: Router → service → repository, with business logic kept out of routers
- [ ] **Schemas**: Separate Create/Read/Update Pydantic models; ORM models never returned directly
- [ ] **Async**: All I/O-bound endpoints are `async def`; no blocking calls inside them
- [ ] **Database**: `AsyncSession` injected per-request; SQLAlchemy 2.0 `select()` style; migrations via Alembic
- [ ] **Dependency injection**: `Depends()` / `Annotated` used for DB sessions, auth, and shared concerns
- [ ] **Routing**: `response_model` and correct `status_code` declared on every endpoint
- [ ] **Auth**: JWT via `OAuth2PasswordBearer`, short-lived access tokens, passwords hashed with `bcrypt`/`argon2`
- [ ] **Security**: No secrets in code, explicit CORS allowlist, no `debug=True` in production
- [ ] **Error handling**: Domain exceptions mapped via global exception handlers; no leaked stack traces
- [ ] **Performance**: N+1 queries avoided (`selectinload`/`joinedload`), list endpoints paginated
- [ ] **Testing**: `pytest-asyncio` + `httpx.AsyncClient` over `ASGITransport` with `dependency_overrides` against an isolated test DB, coverage ≥ 90%, unit/integration/schema layers present
- [ ] **Authn vs authz**: Authentication and authorization are separate dependencies, mapping to 401 vs 403
- [ ] **Pagination stability**: List endpoints have a deterministic `ORDER BY` before offset/limit
- [ ] **Race safety**: Unique-field conflicts rely on a real DB unique constraint, not an app-level precheck
- [ ] **Deployment**: Multi-stage Docker build, non-root user, `gunicorn -k uvicorn.workers.UvicornWorker`
