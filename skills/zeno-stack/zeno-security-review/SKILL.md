---
name: zeno-security-review
description: >
  Application-code security review: secrets management, input validation, SQL injection,
  auth/authz, XSS, CSRF, rate limiting, sensitive-data exposure, and dependency hygiene, with
  a pre-deployment checklist. Use when adding authentication, handling user input or file
  uploads, creating API endpoints, working with secrets, or touching payment/sensitive data.
  For scanning the Claude Code harness itself, use `zeno-security-scan` instead — this skill
  is for the application. Trigger on: "security review", "is this secure", "add
  authentication", "handle user input", "new API endpoint", "SQL injection", "XSS", "CSRF",
  "IDOR", "BOLA", "SSRF", "JWT validation", "OAuth redirect", "deserialization",
  "secrets management", "rate limiting", "pre-deployment security checklist", "OWASP".
---

# Zeno Security Review

Application-level security review for anything touching auth, user input, secrets, or
sensitive data. Distinct from `zeno-security-scan`, which audits the Claude Code harness
configuration itself (`CLAUDE.md`, `settings.json`, MCP servers, hooks) — a different attack
surface entirely.

OWASP Top 10 2025 framing: SSRF and access control are one category (A01) — this skill treats
them together. Software supply chain is its own top-3 category (A03) — see Dependency and
supply-chain hygiene below. Fail-open error handling is itself a security finding (A10) —
cross-reference `zeno-silent-failure-hunter`. XSS is an injection subtype, not a standalone
category.

**Which wins vs the semgrep plugin:** per CLAUDE.md, the semgrep plugin owns automated
SAST/secrets/supply-chain scanning — `/security-review` must call its MCP tools rather than rely
on manual reading. This skill is the *manual review discipline* layered on top: the reviewer's
pattern knowledge for what scanners miss (authz logic, BOLA/BFLA, business-logic flaws). Run
semgrep first; apply this skill to what it can't see.

## When to run this

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating a new API endpoint
- Working with secrets or credentials
- Implementing payment or other sensitive-data features
- Integrating a third-party API

## Secrets management

Never hardcode a secret — always source it from environment configuration, and fail loudly if
it's missing:

```typescript
// Wrong — hardcoded secret in source
const apiKey = "sk-proj-xxxxx"

// Right — sourced from env, verified present
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets read from environment variables
- [ ] `.env.local` (or equivalent) is in `.gitignore`
- [ ] No secrets present anywhere in git history
- [ ] Production secrets live in the hosting platform's secret store, not a committed file

## Input validation

Validate every input against an explicit schema before it reaches business logic — whitelist
the shape you accept, don't blacklist what you reject:

```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150),
})

export async function createUser(input: unknown) {
  try {
    const validated = CreateUserSchema.parse(input)
    return await db.users.create(validated)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: error.issues }
    }
    throw error
  }
}
```

File uploads need the same treatment plus size and type gates:

```typescript
function validateFileUpload(file: File) {
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) throw new Error('File too large (max 5MB)')

  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) throw new Error('Invalid file type')

  const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]
  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif']
  if (!extension || !allowedExtensions.includes(extension)) {
    throw new Error('Invalid file extension')
  }
  return true
}
```

- [ ] Every user input validated against a schema
- [ ] File uploads restricted by size, MIME type, and extension
- [ ] No raw user input reaches a query or shell command
- [ ] Error messages don't leak internal/sensitive detail

## SQL injection prevention

Never build a query by string concatenation — always use parameterized queries or a query
builder that parameterizes for you:

```typescript
// Wrong — string interpolation is a SQL injection vector
const query = `SELECT * FROM users WHERE email = '${userEmail}'`

// Right — parameterized
await db.query('SELECT * FROM users WHERE email = $1', [userEmail])

// Right — query builder that parameterizes internally
const { data } = await supabase.from('users').select('*').eq('email', userEmail)
```

- [ ] All database queries use parameterized queries or a parameterizing builder
- [ ] No string concatenation feeds into SQL
- [ ] See `zeno-postgres-patterns` for schema- and index-level hardening

## Authentication and authorization

Store session tokens in `httpOnly` cookies, not `localStorage` — `localStorage` is readable by
any script that executes on the page, so an XSS bug becomes a session-theft bug:

```typescript
// Wrong — readable by any injected script
localStorage.setItem('token', token)

// Right — inaccessible to JavaScript, scoped, expiring
res.setHeader('Set-Cookie', `token=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

Check authorization *before* the operation it guards, not after:

```typescript
export async function deleteUser(userId: string, requesterId: string) {
  const requester = await db.users.findUnique({ where: { id: requesterId } })
  if (requester.role !== 'admin') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 403 })
  }
  await db.users.delete({ where: { id: userId } })
}
```

On Postgres/Supabase, push the same guarantee into the database with Row Level Security so a
missed application-layer check isn't the only line of defense:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own data" ON users FOR UPDATE USING (auth.uid() = id);

-- Multi-tenant variant: scope by tenant, derived server-side — never from client input
CREATE POLICY "Tenant isolation" ON orders FOR ALL
  USING (tenant_id = (SELECT tenant_id FROM memberships WHERE user_id = auth.uid()));
```

- [ ] Tokens in `httpOnly` cookies, never `localStorage` (one instance of the broader rule: tokens never in web storage)
- [ ] Authorization checked before every sensitive operation, not after
- [ ] Row Level Security enabled where the database supports it — tenant-scoped, not just self-access
- [ ] Role-based access control implemented, not inferred from the UI hiding a button

## Authorization depth — IDOR / BOLA / BFLA / mass assignment

Authentication proves *who you are*; it never proves you may touch *this object*. The #1 API
vulnerability class (BOLA — broken object-level authorization) is a handler that loads a
record by a client-supplied id without scoping the query to the requester. UUIDs are not
access control — they only slow enumeration.

```typescript
// BOLA — loads by param id, never scopes to the caller
const order = await db.order.findUnique({ where: { id: req.params.id } })
return res.json(order)                       // any authenticated user reads any order

// Fixed — ownership is part of the query, not an afterthought
const order = await db.order.findFirst({
  where: { id: req.params.id, userId: req.user.id }   // or tenantId
})
if (!order) return res.status(404).end()     // 404, not 403 — don't confirm existence
```

Greppable red flags for any PR touching handlers:

```bash
# object loads that may skip owner scoping
grep -rEn 'findUnique\(|findById|get\(id|\.get\(.*params|Objects\.get\(' src/
# mass-assignment sinks — whole request body bound to a model
grep -rEn 'update\(.*req\.body|create\(.*\.\.\.body|save\(\*\*request|Object\.assign\(.*body' src/
# privileged routes that may lack a function-level gate
grep -rEn '/admin|/internal|isAdmin|role ===|require_role' src/
```

| Symptom in code | Class | Verdict | Fix |
|---|---|---|---|
| Loads record by client id, no `userId`/`tenantId` in the query | BOLA / IDOR | Critical | Scope the query; 404 on miss |
| Ownership checked *after* a mutation or side-effect | BOLA (TOCTOU) | Critical | Check inside the same query, or before the write |
| Admin endpoint gated only by the UI hiding the link | BFLA | Critical | Server-side role check on every privileged route and HTTP method |
| `PUT/PATCH` binds the full request body to a model | Mass assignment | High | Allowlist writable fields; never spread `req.body` |
| Same handler, different verb (GET gated, DELETE not) | BFLA | High | Gate every method |
| GraphQL resolver reads a node without an object check | BOLA | Critical | Every resolver re-checks object authz — schema depth is not authz |
| Tenant id taken from request body or a client-settable claim | Tenant break | Critical | Derive tenant from the server-side session |

Multi-tenancy checks: tenant/org id derived server-side, never from a request field; every
query against shared tables carries the tenant predicate; a two-account test proves account A
cannot touch account B's objects via *any* endpoint or verb; RLS as defense-in-depth; one
centralized `can(user, action, resource)` helper rather than per-handler re-implementations.

```typescript
test('cannot read another users object (BOLA)', async () => {
  const res = await fetch(`/api/orders/${otherUsersOrderId}`,
    { headers: { Authorization: `Bearer ${userToken}` } })
  expect(res.status).toBe(404)          // not 200, not 403
})
test('cannot escalate role via mass assignment', async () => {
  await fetch('/api/profile', { method: 'PATCH',
    headers: { Authorization: `Bearer ${userToken}` },
    body: JSON.stringify({ name: 'x', role: 'admin' }) })
  expect((await getProfile(userToken)).role).not.toBe('admin')
})
```

## JWT, OAuth, and session pitfalls

Token *validation* is where JWT auth breaks, not token issuance:

```typescript
// Vulnerable — trusts the token's own alg header; enables alg-confusion and alg:none
jwt.verify(token, key)

// Fixed — pin algorithm, issuer, and audience explicitly
jwt.verify(token, key, {
  algorithms: ['RS256'],            // single expected alg — never a list mixing HS + RS
  issuer: 'https://auth.example.com',
  audience: 'https://api.example.com',
})
```

| Symptom | Verdict | Fix |
|---|---|---|
| `verify()` with no `algorithms` pin | Critical | Pin the single expected alg — blocks HS/RS confusion and `alg:none` |
| Verifier accepts a list mixing HMAC + RSA | Critical | One alg per key type; an RS256 server must never HMAC-verify with the public key as secret |
| No `aud`/`iss` validation | High | Exact-match both — a shared IdP's signature is otherwise valid across every service |
| `jwt.decode()` used for authz decisions | Critical | `decode` does not check the signature; use `verify` |
| Access/refresh token in `localStorage` | High | Memory, or `HttpOnly Secure SameSite` cookie |
| Refresh token not rotated on use | High | Rotate + reuse-detection: a replayed refresh token revokes the whole token family |
| OAuth `redirect_uri` matched by prefix/regex/wildcard | Critical | Exact string allowlist — loose matching is code theft → account takeover |
| Missing or unverified OAuth `state` | High | Cryptographically random state (≥128-bit), bound to session, checked before the callback processes |
| Authorization-code flow without PKCE | High | PKCE for all clients (OAuth 2.1 / RFC 9700), not just mobile |
| Session id not regenerated on login | High | Regenerate on privilege change — kills session fixation |
| Logout only clears the cookie | Medium | Revoke the server-side session/refresh token too |

```bash
grep -rEn "verify\([^,]+,[^,]+\)$" src/                         # verify() with no options
grep -rEn "algorithms?\s*[:=].*(none|HS256.*RS256)" src/         # alg:none or mixed lists
grep -rEn "decode\(|jwt\.decode|jwtDecode" src/                  # decode without verify
grep -rEn "localStorage|sessionStorage" src/ | grep -iE "token|jwt"
grep -rEn "redirect_uri|redirectUri" src/                        # then check exact-match
```

## SSRF

Any server-side fetch of a client-influenced URL is SSRF-suspect — webhooks, image proxies,
URL previews, PDF renderers. Allowlist-validate the URL, then **pin the resolved IP and
connect to the pinned IP**: a validator that resolves DNS, checks the result, then hands the
*hostname* back to the HTTP client is a TOCTOU hole (DNS rebinding).

A validator must survive all of these before the finding is closed:

- [ ] Cloud metadata blocked: `169.254.169.254`, `metadata.google.internal`, Azure/Alibaba
      IMDS — including decimal (`2852039166`), hex (`0xA9FEA9FE`), octal, and IPv6-mapped encodings
- [ ] Localhost/link-local/private ranges blocked *after normalization*: `127.0.0.1`,
      `0.0.0.0`, `::1`, `10/8`, `172.16/12`, `192.168/16`, `169.254/16`
- [ ] Redirects re-validated per hop — the client must not silently follow a 30x into an internal address
- [ ] Parser differentials blocked: `http://expected@evil/`, `http://evil#expected` — validate the host the *connection* uses
- [ ] DNS rebinding blocked: resolve once, pin the IP, never re-resolve at connect time
- [ ] Scheme allowlisted to `http`/`https` — no `file://`, `gopher://`, `dict://`
- [ ] Cloud side: IMDSv2 (session-token-required) enforced as defense-in-depth

```bash
grep -rEn "fetch\(|axios\.(get|post)\(|got\(|urlopen|requests\.(get|post)" . | grep -iE "req|body|param|url|user"
grep -rEn "webhook|callback_url|image_url|avatar_url|preview|proxy|fetchUrl" src/
```

Verdict: a user-URL fetch with no IP pinning and no metadata/private-range block is Critical
when it can reach an internal network or cloud metadata; High otherwise.

## Unsafe deserialization

Never deserialize untrusted input with a format that can instantiate arbitrary types or run
code. Prefer data-only formats (JSON + schema validation). If native deserialization is
unavoidable: HMAC-sign the payload and verify before deserializing, and restrict types.

| Language | Dangerous sink | Safe alternative |
|---|---|---|
| Python | `pickle.load(s)`, `yaml.load` without a safe Loader, `jsonpickle`, `dill`, `numpy.load(allow_pickle=True)` | `json`; `yaml.safe_load`; `allow_pickle=False` |
| Java | `ObjectInputStream.readObject`, XStream/Kryo defaults, SnakeYAML `load`, Jackson default typing | JSON + schema; disable polymorphic typing; deserialization filters |
| PHP | `unserialize()` on user data | `json_decode`; `unserialize($x, ['allowed_classes' => false])` |
| Node/JS | `node-serialize`, `funcster`, `eval`/`vm` on payloads | `JSON.parse` + a validator (zod) |
| .NET | `BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter` | `System.Text.Json` (BinaryFormatter is removed in modern .NET) |
| Ruby | `Marshal.load`, pre-safe `YAML.load` | `JSON.parse`; `YAML.safe_load` |

```bash
grep -rEn "pickle\.load|yaml\.load\(|Marshal\.load|unserialize\(|readObject\(|BinaryFormatter|node-serialize|allow_pickle\s*=\s*True" .
```

Any path from request/file/queue data to one of these sinks with no type restriction is a
confirmed Critical (RCE-class). Static pickle scanners are not a mitigation — remove the sink.

## XSS prevention

Sanitize any user-supplied HTML before rendering it, with an explicit allowlist of tags:

```typescript
import DOMPurify from 'isomorphic-dompurify'

function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'],
    ALLOWED_ATTR: [],
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

Set a Content-Security-Policy and start strict — `'unsafe-inline'` and `'unsafe-eval'`
neutralize much of what CSP is for, so treat either as temporary compatibility debt with a
removal plan, never a default:

```typescript
// next.config.js
const securityHeaders = [{
  key: 'Content-Security-Policy',
  value: `
    default-src 'self';
    base-uri 'self';
    object-src 'none';
    frame-ancestors 'none';
    script-src 'self';
    style-src 'self';
    img-src 'self' data: https:;
    font-src 'self';
    connect-src 'self' https://api.example.com;
  `.replace(/\s{2,}/g, ' ').trim(),
}]
```

- [ ] Any user-provided HTML sanitized through an allowlist, never rendered raw
- [ ] CSP configured and free of `unsafe-inline`/`unsafe-eval` unless there's a documented, temporary exception
- [ ] Relying on the framework's default escaping (e.g. React) rather than hand-rolled escaping

## CSRF protection

Require a CSRF token on state-changing requests, and set cookies `SameSite=Strict` as a second
layer:

```typescript
export async function POST(request: Request) {
  const token = request.headers.get('X-CSRF-Token')
  if (!csrf.verify(token)) {
    return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 })
  }
  // process request
}
```

```typescript
res.setHeader('Set-Cookie', `session=${sessionId}; HttpOnly; Secure; SameSite=Strict`)
```

- [ ] CSRF tokens required on all state-changing operations
- [ ] `SameSite=Strict` set on session cookies
- [ ] Double-submit cookie pattern used where token-based CSRF isn't practical

## Rate limiting

Rate limiting must live in a **shared store**, not in process memory. An in-process limiter
(e.g. a Node middleware counting requests in a local `Map`) resets every deploy, doesn't
coordinate across replicas or serverless invocations, and fails open under exactly the load
spike it exists to stop — so per-endpoint or per-user limits it "enforces" are trivially
bypassed by hitting a different replica.

Use Redis (or an equivalent shared store) as the counter backend, with stricter limits on
expensive operations (search, auth attempts, anything that hits an external API or does real
work) than on ordinary reads. See `zeno-redis-patterns` for the correct sliding-window /
token-bucket implementation and connection handling — this skill doesn't duplicate it here.

- [ ] Rate limiting backed by a shared store (Redis), not in-process memory
- [ ] Stricter limits on expensive/sensitive operations than on ordinary reads
- [ ] Limits keyed by both IP and authenticated user where applicable

## Sensitive data exposure

Never log credentials or full payment details, and never return internal error detail to the
client:

```typescript
// Wrong
console.log('User login:', { email, password })
catch (error) { return NextResponse.json({ error: error.message, stack: error.stack }, { status: 500 }) }

// Right
console.log('User login:', { email, userId })
catch (error) {
  console.error('Internal error:', error)
  return NextResponse.json({ error: 'An error occurred. Please try again.' }, { status: 500 })
}
```

- [ ] No passwords, tokens, or full payment details in logs
- [ ] Error responses to the client are generic; detail stays in server-side logs only
- [ ] No stack traces exposed to the client

## Dependency and supply-chain hygiene

OWASP 2025 promotes supply chain to a top-3 category (A03) covering the whole build/deploy
chain, not just dependency CVEs:

```bash
npm audit                # check for known vulnerabilities
npm audit fix             # apply safe automatic fixes
npm outdated              # see what's behind
npm ci                    # reproducible install from the lock file, use in CI
```

- [ ] Lock files committed and used (`npm ci` / `pip install --require-hashes` in CI, never a floating install)
- [ ] `npm audit`/`pip-audit`/`osv-scanner` clean, or findings triaged with a documented reason to defer
- [ ] Secret scanning (trufflehog/gitleaks) in CI, covering git history
- [ ] CI actions pinned to commit SHAs, not mutable tags (`@v4` is mutable; `@<sha>` is not)
- [ ] Build/deploy credentials via OIDC short-lived tokens, not long-lived stored secrets
- [ ] Automated dependency updates (Dependabot or equivalent) enabled

## Security tests worth writing

```typescript
test('requires authentication', async () => {
  const response = await fetch('/api/protected')
  expect(response.status).toBe(401)
})

test('requires admin role', async () => {
  const response = await fetch('/api/admin', { headers: { Authorization: `Bearer ${userToken}` } })
  expect(response.status).toBe(403)
})

test('rejects invalid input', async () => {
  const response = await fetch('/api/users', {
    method: 'POST',
    body: JSON.stringify({ email: 'not-an-email' }),
  })
  expect(response.status).toBe(400)
})

test('enforces rate limits', async () => {
  const requests = Array(101).fill(null).map(() => fetch('/api/endpoint'))
  const responses = await Promise.all(requests)
  expect(responses.filter(r => r.status === 429).length).toBeGreaterThan(0)
})
```

## Pre-deployment security checklist

Before any production deployment:

- [ ] Secrets: none hardcoded, all in env vars / secret store
- [ ] Input validation: every user input validated
- [ ] SQL injection: every query parameterized
- [ ] XSS: user content sanitized, CSP configured
- [ ] CSRF: protection enabled on state-changing requests
- [ ] Auth: tokens in `httpOnly` cookies, authorization checked before sensitive ops
- [ ] Rate limiting: backed by a shared store (Redis), not process memory
- [ ] HTTPS enforced in production
- [ ] Security headers configured (CSP, X-Frame-Options)
- [ ] Errors and logs free of sensitive data
- [ ] Dependencies up to date, `npm audit` clean
- [ ] Row Level Security enabled where applicable
- [ ] CORS scoped, not wildcard
- [ ] File uploads validated (size, type, extension)
- [ ] Object-level authz: every by-id load scoped to the requester (BOLA two-account test passes)
- [ ] JWT verification pins algorithm, issuer, and audience; refresh tokens rotate with reuse detection
- [ ] Any server-side fetch of user-influenced URLs passes the SSRF bypass checklist
- [ ] No unsafe deserialization sink reachable from untrusted data

This skill covers application-code security. For cloud platform deployment, IAM policy,
CI/CD pipeline, and infrastructure-as-code security specifically, see
`references/cloud-infrastructure-security.md`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Secret hardcoded in source | Read from env, throw if missing |
| SQL built via string interpolation | Parameterized query / parameterizing query builder |
| Session token in `localStorage` | `httpOnly`, `Secure`, `SameSite=Strict` cookie |
| Authorization checked after the mutation | Check and short-circuit before any sensitive operation |
| Raw user HTML rendered via `dangerouslySetInnerHTML` | Sanitize through an allowlist (DOMPurify) first |
| CSP with `unsafe-inline`/`unsafe-eval` as the default | Strict CSP; loosen only with a documented, temporary exception |
| In-process rate limiter (`express-rate-limit`-style, local `Map`) | Shared-store (Redis) limiter — see `zeno-redis-patterns` |
| Full error object / stack trace returned to the client | Generic client message; detail stays in server logs |
| `npm install` in CI | `npm ci` against the committed lock file |
| Handler loads a record by client-supplied id with no owner/tenant scoping | Ownership in the query itself; 404 on miss (BOLA) |
| `jwt.verify()` with no `algorithms`/`iss`/`aud` pinning, or `decode()` for authz | Pin all three; `decode` never substitutes for `verify` |
| Fetching a user-influenced URL after hostname-only validation | Resolve once, pin the IP, block metadata/private ranges and non-http(s) schemes |
| `pickle.load`/`yaml.load`/`unserialize` on untrusted data | Data-only formats + schema validation; remove the sink |
| CI actions on mutable tags, long-lived cloud keys in CI secrets | SHA-pinned actions; OIDC short-lived credentials |

## Pre-flight checklist — run before delivering any security review

- [ ] No hardcoded secrets found, or all flagged and routed to env config
- [ ] Every new endpoint validates input against an explicit schema
- [ ] Every new query is parameterized — none built by concatenation
- [ ] Authorization is checked before, not after, every sensitive operation
- [ ] Any rate limiting added is backed by Redis (or equivalent shared store), not in-process memory
- [ ] User-rendered HTML is sanitized; CSP has no undocumented `unsafe-*` exceptions
- [ ] Error responses to clients are generic; nothing sensitive is logged
- [ ] Every by-id object load was checked for owner/tenant scoping (BOLA), and privileged routes for function-level gates (BFLA)
- [ ] Token verification pins alg/iss/aud; OAuth flows use exact-match redirect URIs, state, and PKCE
- [ ] User-influenced URL fetches passed the SSRF bypass checklist; deserialization sinks grepped for
- [ ] Pre-deployment checklist above is run in full before sign-off
