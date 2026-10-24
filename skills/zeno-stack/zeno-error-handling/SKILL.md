---
name: zeno-error-handling
description: >
  Robust error handling patterns across TypeScript, Python, and Go — typed error hierarchies,
  the operational-vs-programmer-error distinction, centralized error handlers, the Result
  pattern, retry with exponential backoff, circuit breakers, React error boundaries, and
  user-facing vs developer-facing error messages. Use when designing error types for a new
  module, adding retry logic around an unreliable dependency, reviewing an endpoint for
  missing or swallowed error handling, or writing user-facing error copy. Trigger on: "error
  handling", "typed errors", "exception hierarchy", "retry with backoff", "circuit breaker",
  "error boundary", "don't swallow errors", "custom exception", "AppError", or any review of
  try/catch, error propagation, or failure-path code.
---

# Error Handling Patterns

Consistent, robust error handling for production applications. Errors are part of your API
contract, not an afterthought bolted on after the happy path works.

## Core Principles

1. **Fail fast and loudly** — surface errors at the boundary where they occur; don't bury them.
2. **Typed errors over string messages** — errors are structured, first-class values.
3. **Operational vs. programmer errors** — an operational error (bad input, resource not
   found, a downstream timeout) is expected and should be handled gracefully; a programmer
   error (null dereference, broken invariant) is a bug and should be allowed to crash loudly
   in development rather than be caught and hidden. Mark which kind an error is so handlers
   can make that call automatically instead of guessing.
4. **User messages ≠ developer messages** — show friendly text to users, log full context
   server-side.
5. **Never swallow errors silently** — every `catch` block must handle, re-throw, or log.
6. **Document every error code** a client may receive; it's part of the API surface (see
   `zeno-api-design` for the response envelope these errors are rendered into).

## TypeScript / JavaScript

### Typed Error Hierarchy

```typescript
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly isOperational: boolean = true,
    public readonly details?: unknown,
  ) {
    super(message)
    this.name = this.constructor.name
    // Maintain the prototype chain in transpiled ES5 so `instanceof` checks
    // (e.g. `error instanceof NotFoundError`) work correctly.
    Object.setPrototypeOf(this, new.target.prototype)
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404)
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details: { field: string; message: string }[]) {
    super(message, 'VALIDATION_ERROR', 422, true, details)
  }
}

export class UnauthorizedError extends AppError {
  constructor(reason = 'Authentication required') {
    super(reason, 'UNAUTHORIZED', 401)
  }
}

export class RateLimitError extends AppError {
  constructor(public readonly retryAfterMs: number) {
    super('Rate limit exceeded', 'RATE_LIMITED', 429)
  }
}
```

`isOperational` is the hook a top-level handler uses to decide policy: operational errors get
logged and turned into a clean HTTP response; non-operational ones (anything that reaches the
handler *without* being one of your typed errors) should be logged as an incident and may
warrant process-level alerting, not just a 500 response.

### Centralized Error Handler

One handler, called from every route's `catch`, is what prevents each endpoint from inventing
its own error shape:

```typescript
function handleApiError(error: unknown): Response {
  if (error instanceof AppError) {
    return NextResponse.json(
      { error: { code: error.code, message: error.message, ...(error.details ? { details: error.details } : {}) } },
      { status: error.statusCode },
    )
  }

  if (error instanceof z.ZodError) {
    return NextResponse.json(
      {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: error.issues.map(i => ({ field: i.path.join('.'), message: i.message })),
        },
      },
      { status: 422 },
    )
  }

  // Unexpected (non-operational) error — log full details, return a generic message
  console.error('Unexpected error:', error)
  return NextResponse.json(
    { error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } },
    { status: 500 },
  )
}

export async function POST(req: NextRequest) {
  try {
    // ... handler logic
  } catch (error) {
    return handleApiError(error)
  }
}
```

### Result Pattern (no-throw style)

For operations where failure is expected and common (parsing, external calls), prefer
returning a `Result` over throwing — it forces the caller to handle both branches at the type
level instead of hoping they remembered a `try/catch`:

```typescript
type Result<T, E = AppError> = { ok: true; value: T } | { ok: false; error: E }

const ok = <T,>(value: T): Result<T> => ({ ok: true, value })
const err = <E,>(error: E): Result<never, E> => ({ ok: false, error })

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await db.users.findUnique({ where: { id } })
    if (!user) return err(new NotFoundError('User', id))
    return ok(user)
  } catch {
    return err(new AppError('Database error', 'DB_ERROR'))
  }
}

const result = await fetchUser('abc-123')
if (!result.ok) {
  logger.error('Failed to fetch user', { error: result.error })
  return
}
console.log(result.value.email) // TypeScript knows result.value here
```

### React Error Boundary

```typescript
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info)
    console.error('Unhandled React error:', error, info)
  }

  render() {
    if (this.state.hasError) return this.props.fallback
    return this.props.children
  }
}

// <ErrorBoundary fallback={<p>Something went wrong. Please refresh.</p>}><MyComponent /></ErrorBoundary>
```

## Python

```python
class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: str, status_code: int = 500, is_operational: bool = True):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.is_operational = is_operational

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}", "NOT_FOUND", 404)

class ValidationError(AppError):
    def __init__(self, message: str, details: list[dict] | None = None):
        super().__init__(message, "VALIDATION_ERROR", 422)
        self.details = details or []
```

```python
# FastAPI global exception handlers
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected error", exc_info=exc)  # non-operational — log full context
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )
```

Never catch bare `except:` and continue silently — see `code-standards/python` for the
specific-exception-and-chain-with-`from`-e convention that error handling in Python relies on.

## Go

```go
package domain

import "errors"

// Sentinel errors for type-checking
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrConflict     = errors.New("conflict")
)

// Wrap errors with context — never lose the original
func (r *UserRepository) FindByID(ctx context.Context, id string) (*User, error) {
    user, err := r.db.QueryRow(ctx, "SELECT * FROM users WHERE id = $1", id)
    if errors.Is(err, sql.ErrNoRows) {
        return nil, fmt.Errorf("user %s: %w", id, ErrNotFound)
    }
    if err != nil {
        return nil, fmt.Errorf("querying user %s: %w", id, err)
    }
    return user, nil
}

// At the handler level, unwrap to determine the response
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
    user, err := h.service.GetUser(r.Context(), chi.URLParam(r, "id"))
    if err != nil {
        switch {
        case errors.Is(err, domain.ErrNotFound):
            writeError(w, http.StatusNotFound, "not_found", err.Error())
        case errors.Is(err, domain.ErrUnauthorized):
            writeError(w, http.StatusForbidden, "forbidden", "Access denied")
        default:
            slog.Error("unexpected error", "err", err)
            writeError(w, http.StatusInternalServerError, "internal_error", "An unexpected error occurred")
        }
        return
    }
    writeJSON(w, http.StatusOK, user)
}
```

## Retry with Exponential Backoff

Retry only operational, transient failures — never retry a 4xx client error, since retrying
guarantees the same rejection. Add jitter so many clients retrying the same downstream outage
don't retry in lockstep (a "thundering herd").

```typescript
interface RetryOptions {
  maxAttempts?: number
  baseDelayMs?: number
  maxDelayMs?: number
  retryIf?: (error: unknown) => boolean
}

async function withRetry<T>(fn: () => Promise<T>, options: RetryOptions = {}): Promise<T> {
  const { maxAttempts = 3, baseDelayMs = 500, maxDelayMs = 10_000, retryIf = () => true } = options
  let lastError: unknown

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      if (attempt === maxAttempts || !retryIf(error)) throw error
      const jitter = Math.random() * baseDelayMs
      const delay = Math.min(baseDelayMs * 2 ** (attempt - 1) + jitter, maxDelayMs)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  throw lastError
}

// Retry transient network errors, not 4xx client errors
const data = await withRetry(() => fetch('/api/data').then(r => r.json()), {
  maxAttempts: 3,
  retryIf: (error) => !(error instanceof AppError && error.statusCode < 500),
})
```

## Circuit Breakers

For a dependency that's failing repeatedly, stop calling it for a cooldown window instead of
retrying into a known-bad target — this bounds cascading latency and gives the downstream
service room to recover:

- **Closed** (normal): requests pass through; failures are counted in a rolling window.
- **Open**: once the failure count crosses a threshold, calls fail immediately (no network
  round trip) until a cooldown elapses.
- **Half-open**: after cooldown, allow a small number of trial requests through; a success
  closes the circuit again, a failure re-opens it.

Combine with retry, not instead of it: retry handles a single transient blip, the circuit
breaker handles a dependency that's down for longer than a few backoff cycles.

## User-Facing Error Messages

Map error codes to human-readable text; never surface stack traces or internal details to a user.

```typescript
const USER_ERROR_MESSAGES: Record<string, string> = {
  NOT_FOUND: 'The requested item could not be found.',
  UNAUTHORIZED: 'Please sign in to continue.',
  FORBIDDEN: "You don't have permission to do that.",
  VALIDATION_ERROR: 'Please check your input and try again.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  INTERNAL_ERROR: 'Something went wrong on our end. Please try again later.',
}

export function getUserMessage(code: string): string {
  return USER_ERROR_MESSAGES[code] ?? USER_ERROR_MESSAGES.INTERNAL_ERROR
}
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Bare `catch {}` / `except:` that swallows the error | Handle, re-throw, or log — every catch block does one of the three |
| Throwing raw strings or unstructured objects | A typed error hierarchy rooted in one `AppError`/base exception with a `code` |
| One-off error JSON shape per endpoint | One centralized handler producing the standard `{ error: { code, message } }` envelope |
| Retrying a 4xx validation error | Retry only operational/transient failures; check status before retrying |
| Fixed-delay retry loop, no jitter | Exponential backoff with jitter, capped at a max delay |
| Retrying indefinitely into a downed dependency | A circuit breaker that stops calling once failures cross a threshold |
| Stack traces or SQL errors shown to end users | A user-message lookup table keyed by error code, logged detail stays server-side |
| Treating every caught exception as equally severe | Distinguish operational (expected, handle gracefully) from programmer errors (bug, log as incident) |

## Pre-flight checklist — run before delivering any error-handling change

- [ ] Every `catch`/`except` block handles, re-throws, or logs — nothing is silently swallowed
- [ ] Custom error classes extend one base (`AppError`) with a `code` and `statusCode`/status field
- [ ] Operational errors are distinguished from unexpected/programmer errors
- [ ] API errors are rendered through one centralized handler into the standard envelope
- [ ] User-facing messages contain no stack traces, SQL, or other internal detail
- [ ] Full error context (stack, request id) is logged server-side for every non-operational error
- [ ] Retry logic only retries retriable failures, uses exponential backoff with jitter, and caps attempts
- [ ] A dependency prone to sustained outages is protected by a circuit breaker, not bare retry
- [ ] Async functions surface errors to their caller — no fire-and-forget without a fallback
- [ ] React components that can throw during render are wrapped in an `ErrorBoundary`
