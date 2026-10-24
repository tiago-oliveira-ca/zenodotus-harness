---
name: zeno-api-design
description: >
  REST API design discipline covering resource naming and URL structure, HTTP method and
  status-code semantics, response envelopes, pagination, filtering/sorting/search, auth,
  versioning, and rate limiting for production APIs. Use when designing new endpoints,
  reviewing an existing API contract, adding pagination or filters, standardizing error
  responses, or planning a versioning or deprecation strategy. Trigger on: "design an API
  endpoint", "REST API", "API contract", "resource naming", "pagination", "cursor
  pagination", "filtering and sorting", "API versioning", "rate limiting", "status code",
  "error response format", "OpenAPI spec", or any request to add, review, or version an
  HTTP API.
---

# REST API Design

Conventions for consistent, developer-friendly REST APIs. Apply this whenever a new endpoint
is added or an existing contract is reviewed — inconsistent APIs (mixed casing, ad hoc status
codes, one-off error shapes) create integration bugs that surface only in client code, far
from the endpoint that caused them.

## Resource Naming and URL Structure

Resources are nouns, plural, lowercase, kebab-case. The HTTP method carries the verb — never
the URL.

```
GET    /api/v1/users
GET    /api/v1/users/:id
POST   /api/v1/users
PUT    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

# Sub-resources for relationships
GET    /api/v1/users/:id/orders
POST   /api/v1/users/:id/orders

# Actions that don't map to CRUD — use verbs sparingly, only for genuine state
# transitions or side effects with no resource-shaped equivalent
POST   /api/v1/orders/:id/cancel
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh

# Query params carry filtering, sorting, pagination — never encode them in the path
GET    /api/v1/orders?status=active&sort=volume&limit=20&offset=0
```

| Good | Bad | Why |
|---|---|---|
| `/api/v1/team-members` | `/api/v1/getUsers` | verb belongs in the HTTP method, not the URL |
| `/api/v1/orders` (plural) | `/api/v1/user` (singular) | collections are plural even for a single-item route |
| `/api/v1/team-members` (kebab-case) | `/api/v1/team_members` (snake_case) | kebab-case is the URL convention; reserve snake/camelCase for JSON bodies |
| `/api/v1/users/123/orders` | `/api/v1/users/123/getOrders` | nested resource for ownership, no verb suffix |

## HTTP Methods and Status Codes

| Method | Idempotent | Safe | Use for |
|---|---|---|---|
| GET | Yes | Yes | Retrieve resources |
| POST | No | No | Create resources, trigger actions |
| PUT | Yes | No | Full replacement of a resource |
| PATCH | No* | No | Partial update of a resource |
| DELETE | Yes | No | Remove a resource |

*PATCH can be made idempotent with careful implementation (e.g. set-to-value rather than
increment-by-value semantics).

```
# Success
200 OK                    — GET, PUT, PATCH (with response body)
201 Created               — POST (include Location header)
204 No Content             — DELETE, PUT (no response body)

# Client errors
400 Bad Request            — validation failure, malformed JSON
401 Unauthorized           — missing or invalid authentication
403 Forbidden               — authenticated but not authorized
404 Not Found                — resource doesn't exist
409 Conflict                  — duplicate entry, state conflict
422 Unprocessable Entity  — semantically invalid (valid JSON, bad data)
429 Too Many Requests      — rate limit exceeded

# Server errors
500 Internal Server Error — unexpected failure (never expose internal details)
502 Bad Gateway               — upstream service failed
503 Service Unavailable    — temporary overload, include Retry-After
```

Never use 200 for everything and signal failure only in the body — that forces every client
to parse the payload before it can tell success from failure:

```
# BAD
{ "status": 200, "success": false, "error": "Not found" }

# GOOD — status code carries the outcome
HTTP/1.1 404 Not Found
{ "error": { "code": "not_found", "message": "User not found" } }
```

Likewise, don't return 500 for validation errors (use 400/422 with field-level detail), and
don't return 200 for a resource that was just created (use 201 with a `Location` header).

## Response Envelope

```json
// Success — single resource
{
  "data": {
    "id": "abc-123",
    "email": "alice@example.com",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

```json
// Success — collection, with pagination metadata
{
  "data": [
    { "id": "abc-123", "name": "Alice" },
    { "id": "def-456", "name": "Bob" }
  ],
  "meta": { "total": 142, "page": 1, "per_page": 20, "total_pages": 8 },
  "links": {
    "self": "/api/v1/users?page=1&per_page=20",
    "next": "/api/v1/users?page=2&per_page=20",
    "last": "/api/v1/users?page=8&per_page=20"
  }
}
```

```json
// Error — field-level detail for validation failures
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Must be a valid email address", "code": "invalid_format" },
      { "field": "age", "message": "Must be between 0 and 150", "code": "out_of_range" }
    ]
  }
}
```

Pick one envelope convention and hold every endpoint to it. Two workable options:

- **Data-wrapper envelope** (`{ data, meta?, links? }` / `{ error: { code, message, details? } }`)
  — recommended for public/partner APIs, since clients can branch on the shape alone.
  See `zeno-error-handling` for the matching typed-error hierarchy that produces this shape.
- **Flat response** — return the resource directly on success, an error object on failure,
  and let the HTTP status code be the sole signal of which one a client received. Simpler,
  common for internal service-to-service APIs.

Don't mix the two within a single API surface.

## Pagination

| Style | How | Pros | Cons | Use for |
|---|---|---|---|---|
| Offset | `?page=2&per_page=20` → `LIMIT 20 OFFSET 20` | simple, supports "jump to page N" | slow on large offsets, unstable under concurrent inserts | admin dashboards, small datasets (<10K), search results (users expect page numbers) |
| Cursor | `?cursor=eyJpZCI6MTIzfQ&limit=20` → `WHERE id > :cursor_id ORDER BY id LIMIT 21` | consistent performance at any depth, stable under concurrent inserts | can't jump to an arbitrary page, cursor is opaque | infinite scroll, feeds, large datasets, public APIs (default) |

Cursor implementation fetches one extra row to determine `has_next`:

```json
{ "data": [...], "meta": { "has_next": true, "next_cursor": "eyJpZCI6MTQzfQ" } }
```

## Filtering, Sorting, and Search

```
# Equality
GET /api/v1/orders?status=active&customer_id=abc-123

# Comparison (bracket notation)
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/orders?created_at[after]=2025-01-01

# Multiple values (comma-separated)
GET /api/v1/products?category=electronics,clothing

# Nested fields (dot notation)
GET /api/v1/orders?customer.country=US

# Sorting — leading "-" for descending, comma-separated for multi-field
GET /api/v1/products?sort=-featured,price,-created_at

# Full-text search
GET /api/v1/products?q=wireless+headphones

# Sparse fieldsets — reduce payload to only what the client needs
GET /api/v1/orders?fields=id,total,status&include=customer.name
```

## Authentication and Authorization

```
# Bearer token — user-facing clients
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API key — server-to-server
X-API-Key: sk_live_abc123
```

Keep the two checks distinct and ordered: authenticate first (401 if the caller can't be
identified), then authorize (403 if they're identified but not allowed). Collapsing them into
one check loses the ability to tell a client "log in" from "you can't do that":

```typescript
app.get("/api/v1/orders/:id", async (req, res) => {
  const order = await Order.findById(req.params.id);
  if (!order) return res.status(404).json({ error: { code: "not_found" } });
  if (order.userId !== req.user.id) return res.status(403).json({ error: { code: "forbidden" } });
  return res.json({ data: order });
});
```

## Rate Limiting

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

# When exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60
{ "error": { "code": "rate_limit_exceeded", "message": "Rate limit exceeded. Try again in 60 seconds." } }
```

| Tier | Limit | Window | Use case |
|---|---|---|---|
| Anonymous | 30/min | Per IP | Public endpoints |
| Authenticated | 100/min | Per user | Standard API access |
| Premium | 1000/min | Per API key | Paid API plans |
| Internal | 10000/min | Per service | Service-to-service |

The counter store itself (Redis, gateway, or platform-native limiter) is not this skill's
concern — that's `zeno-redis-patterns`. This skill owns the HTTP contract: which headers are
returned, which status code signals the limit, and how tiers map to numbers.

## Versioning

```
# URL path versioning (recommended) — explicit, easy to route, cacheable
/api/v1/users
/api/v2/users

# Header versioning — clean URLs, harder to test, easy for clients to forget
GET /api/users
Accept: application/vnd.myapp.v2+json
```

Strategy:

1. Start with `/api/v1/` — don't introduce a second version until you need one.
2. Maintain at most two active versions (current + previous).
3. Deprecation timeline: announce (6 months' notice for public APIs) → add a `Sunset` header
   (`Sunset: Sat, 01 Jan 2026 00:00:00 GMT`) → return `410 Gone` after the sunset date.
4. Non-breaking changes don't need a new version: new response fields, new optional query
   params, new endpoints.
5. Breaking changes require a new version: removed/renamed fields, changed field types,
   changed URL structure, changed auth method.

## Implementation Sketch

```typescript
// Next.js API route
export async function POST(req: NextRequest) {
  const parsed = createUserSchema.safeParse(await req.json());
  if (!parsed.success) {
    return NextResponse.json({
      error: {
        code: "validation_error",
        message: "Request validation failed",
        details: parsed.error.issues.map(i => ({ field: i.path.join("."), message: i.message })),
      },
    }, { status: 422 });
  }
  const user = await createUser(parsed.data);
  return NextResponse.json({ data: user }, { status: 201, headers: { Location: `/api/v1/users/${user.id}` } });
}
```

```python
# Django REST Framework
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create(**serializer.validated_data)
        return Response(
            {"data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
            headers={"Location": f"/api/v1/users/{user.id}"},
        )
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Verb in the URL (`/getUsers`, `/user/123/getOrders`) | Nouns for resources; the HTTP method carries the verb |
| `200 OK` with `success: false` in the body | Use the real status code — 4xx/5xx for failure, 2xx for success |
| `500` for a validation failure | `400`/`422` with field-level `details` |
| `200` for a newly created resource | `201 Created` with a `Location` header |
| Offset pagination on a large, high-write collection | Cursor pagination — stable under concurrent inserts, consistent performance |
| Mixing the data-wrapper and flat-response envelopes in one API | Pick one envelope convention per API surface and hold every endpoint to it |
| In-memory per-process rate limiting in production | A shared store (Redis/gateway/platform limiter) — see `zeno-redis-patterns` |
| Breaking a field's type or removing it without a version bump | Treat as breaking; ship behind a new version with a deprecation timeline |
| Authorization check that returns 404 or 401 for "not yours" | 403 Forbidden once identity is established — 401 means "who are you", 403 means "not allowed" |

## Pre-flight checklist — run before delivering any REST API design

- [ ] Resource URLs are plural, kebab-case nouns with no verbs
- [ ] Correct HTTP method chosen per endpoint (GET/POST/PUT/PATCH/DELETE)
- [ ] Status codes are semantic — not 200/500 for everything
- [ ] Request body validated against a schema (Zod, Pydantic, Bean Validation, …)
- [ ] Error responses follow one standard envelope with `code` + `message`
- [ ] List endpoints are paginated (offset or cursor, matched to the access pattern)
- [ ] Authentication is required, or the endpoint is explicitly marked public
- [ ] Authorization is checked after authentication, with the right 401 vs 403
- [ ] Rate limiting is configured against a shared store, not in-process state
- [ ] Responses never leak internal details (stack traces, SQL errors, secrets)
- [ ] Versioning strategy is explicit; breaking changes go behind a new version
- [ ] OpenAPI/Swagger (or equivalent) spec is updated to match
