---
name: json-standards
description: >
  Standards for designing JSON Schemas (Draft 2020-12) and JSON payloads: dialect and $id
  declaration, modular $defs/$ref structure, composition (allOf/oneOf/anyOf,
  unevaluatedProperties, discriminator), versioning and backward compatibility, naming, and
  validator performance (Ajv compile-once). Use whenever writing, reviewing, or refactoring a
  JSON Schema, JSON API payload, or validation code. Trigger on: "JSON Schema", "$schema",
  "$ref", "$defs", "additionalProperties", "unevaluatedProperties", "oneOf", "validate JSON",
  "Ajv", "schema versioning", "API payload shape", "OpenAPI 3.1 schema", "discriminator", or any
  task producing or reviewing a .schema.json file or JSON contract between services.
---

# JSON Schema & JSON Payload Standards

Adhere strictly to these standards when generating, reviewing, or refactoring JSON Schemas
and JSON payloads. They target **Draft 2020-12**.

---

## 1. Foundations — every schema, no exceptions

Every schema document you produce MUST start with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/user/v1",
  "title": "User",
  "description": "A registered user of the platform.",
  "type": "object"
}
```

**Rules:**

- **Always declare `$schema`** with the 2020-12 dialect URI. Omitting it lets each
  validator pick its own default (Ajv 6 → Draft-07, Ajv 8 `2020` build → 2020-12), which
  makes validation non-deterministic and silently ignores newer keywords like
  `prefixItems` under an older dialect.
- **Always give each schema file an absolute, fragment-free `$id`.** In 2020-12, `$id`
  must not contain a fragment. `$id` is an identifier, not a URL to fetch — validators
  resolve references from their internal schema registry, not the network.
- **Always add `title` (short) and `description` (longer)** at the root and on any
  non-obvious property. Add `examples` (array — the 2020-12 keyword, not singular
  `example`) illustrating valid instances.
- `default` is documentation only — it does **not** fill in missing values during
  validation. Never rely on it for behavior.
- Use `readOnly`/`writeOnly` for API semantics (a `readOnly` field must not be accepted
  in a PUT/POST body) and `deprecated: true` for fields slated for removal.

---

## 2. Structure and modularity

Treat schemas like code: factor reusable units instead of duplicating.

**Rules:**

- **Rule of two:** if a subschema is used once, inline it. The moment it is used twice,
  move it to `$defs` and reference it with `$ref`. Split into separate files (each with
  its own `$id`) when a file becomes hard to read or a type is shared across schemas.
- **Keep nesting shallow** — 2–3 object levels. Flatten deeper structures.
- **Use `$defs`**, not the legacy `definitions` keyword, for local reusable subschemas.
- **Prefer arrays of homogeneous items over dynamically-keyed objects.** Objects whose
  key names vary between responses are an anti-pattern — unparseable in strictly-typed
  consumers.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/order/v1",
  "type": "object",
  "properties": {
    "billingAddress": { "$ref": "#/$defs/Address" },
    "shippingAddress": { "$ref": "#/$defs/Address" }
  },
  "$defs": {
    "Address": {
      "type": "object",
      "properties": {
        "street": { "type": "string" },
        "city": { "type": "string" }
      },
      "required": ["street", "city"]
    }
  }
}
```

- **`$anchor`** defines a plain-name fragment safe to add without changing resolution
  scope. Referencing another *file's* `$anchor` is an anti-pattern — promote shared
  subschemas to standalone resources with their own `$id` instead.
- **Bundle at build time, never resolve remote `$ref`s at runtime.** Use the 2020-12
  Compound Schema Document pattern (embedded resources keep their own `$id` and
  `$schema`, reference URIs unchanged) via tools like `@hyperjump/json-schema-bundle`
  or the `jsonschema` CLI `bundle` command.
- **Avoid `$dynamicRef`/`$dynamicAnchor`** unless you fully understand their behavior —
  the spec authors themselves advise against casual use.
- Circular `$ref`s are valid for genuinely recursive types (trees); be aware they can
  exponentially increase validation time (§9).

---

## 3. Validation keywords

- **`type` is the foundation of every subschema.** Express nullability as a type array:
  `"type": ["string", "null"]` — never OpenAPI 3.0's removed `nullable: true`.
- **`enum` / `const`** for closed value sets. Do **not** combine `enum` with `type` —
  the enum values already imply their types; the combination is redundant and an
  anti-pattern.
- **`pattern`** uses ECMA-262 regex. Always anchor patterns (`^...$`) and avoid
  constructs prone to catastrophic backtracking (ReDoS) on untrusted input; bound input
  with `maxLength`.
- **`format` is an annotation, NOT an assertion, by default in 2020-12.** A schema with
  `"format": "email"` alone validates `"not-an-email"` successfully on a compliant
  validator. When enforcement matters: pair `format` with a `pattern`, or enable the
  validator's opt-in format assertion (e.g. `ajv-formats`), or validate in the
  application layer. Never invent custom `format` values — introduce a distinct keyword
  or use `pattern`.
- **Numeric:** `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum` take numbers in
  2020-12 (not the old boolean form); `multipleOf` for granularity. JSON Schema treats
  `1` and `1.0` as equal.
- **String:** `minLength`/`maxLength` — set `maxLength` on any user-supplied string.
- **Array:** `prefixItems` for tuple positions + `items` for the rest (this replaced the
  old array-form `items`/`additionalItems`); `minItems`/`maxItems`, `uniqueItems`,
  `contains`/`minContains`/`maxContains`.
- **Object:** `properties`, `patternProperties`, `propertyNames`,
  `minProperties`/`maxProperties`, and the extension-control keywords covered in §5.

---

## 4. Required vs optional, null vs absent

- **All properties are optional by default**; `required` is a separate array of names.
  Mark only genuinely mandatory fields — over-constraining kills evolvability (§6).
- **`null` and absent are semantically different.** Missing key = "does not apply";
  `"field": null` = "exists, has no value". Make a field both optional *and* nullable
  only when the API genuinely distinguishes them (e.g. PATCH where `null` means "clear"
  and omission means "leave unchanged"). If you cannot describe a scenario where `{}`
  and `{"field": null}` behave differently, the field is optional but **not** nullable.
- **`dependentRequired`** expresses "if A is present, B is required":

```json
{ "dependentRequired": { "creditCard": ["billingAddress"] } }
```

  Dependencies are one-directional — declare both directions if both are needed.
- **`if`/`then`/`else`** for conditional subschemas; **`dependentSchemas`** to apply a
  whole subschema when a property is present.

---

## 5. Composition — the rules that prevent broken schemas

- **`allOf`** = intersection (all subschemas must pass). It is **not** OO inheritance:
  each subschema validates independently, so `additionalProperties` in one branch cannot
  see properties defined in another.
- **`oneOf`** = exactly one branch. Correct for union types, but every branch must be
  evaluated to prove exactly-one — use a discriminator for tagged unions (§9).
- **`anyOf`** = at least one. Faster to validate than `oneOf` (short-circuits), but has
  no established code-generation convention — avoid unless the semantics genuinely
  require "one or more".
- **`not`** — use sparingly; code generators cannot interpret it.
- Watch for logically impossible combinations (e.g. `"type": "string"` with an `anyOf`
  of numeric `const`s) — they never validate and fail silently.

**The `additionalProperties: false` trap — never use it in composed schemas.** It cannot
"see inside" `$ref`, `allOf`, or `oneOf` subschemas, so it rejects the very properties
those branches define, and it makes the schema impossible to extend. This is
spec-mandated behavior in every compliant validator, not a bug. The fixes:

- **Extension:** `allOf` + **`unevaluatedProperties: false`** at the top level — it
  *can* see through `$ref` and inside `allOf`/`anyOf`/`oneOf`/`if`/`then`/`else`:

```json
{
  "$id": "https://example.com/schemas/employee/v1",
  "allOf": [{ "$ref": "https://example.com/schemas/person/v1" }],
  "properties": { "employeeId": { "type": "string" } },
  "required": ["employeeId"],
  "unevaluatedProperties": false
}
```

- **Tagged unions:** `oneOf` + a discriminator property that is `required` with a
  `const` in each branch (validators like Ajv with `discriminator: true` then validate
  only the matching branch):

```json
{
  "oneOf": [
    { "properties": { "kind": { "const": "card" }, "cardNumber": { "type": "string" } },
      "required": ["kind", "cardNumber"] },
    { "properties": { "kind": { "const": "sepa" }, "iban": { "type": "string" } },
      "required": ["kind", "iban"] }
  ]
}
```

- **Or simply leave the model open** and have consumers ignore unknown properties —
  the spec-committee-recommended default for anything that will be extended.

---

## 6. Versioning and compatibility

Two independent axes — never conflate them:

1. **Dialect version** — the `$schema` keyword (2020-12).
2. **Content version** — your document's own version, carried in the data.

**Rules:**

- Embed a `schemaVersion` field in instance data; validate against the schema for that
  exact version, then migrate to a single latest in-memory representation.
- Version the `$id` (and `title`): `https://example.com/schemas/user/v2`.
- **Additive changes only within a major version.** Adding optional fields or relaxing
  constraints is backward-compatible. Removing, renaming, or **retyping** a field is
  breaking — once a field ships, its name and type are frozen until the next major
  version, and a removed name must never be reused within one.
- **Breaking changes use three-phase deprecation:** (1) add the new field alongside the
  old and dual-write, (2) migrate consumers, (3) remove the old field. Mark the old
  field `"deprecated": true` in the interim rather than deleting it.
- Maintain a monotonic migration registry with `up` (N→N+1) and `down` (N+1→N)
  transforms; never delete old entries. Test every transition with fixture files and
  round-trip/idempotency checks.
- **Producer-closed / consumer-open split** when a strict schema registry (e.g.
  Confluent) checks compatibility: producers validate against a closed content model,
  consumers against an open one (ignore unknown fields). This keeps adding/removing
  optional fields fully compatible — registries treat even additions to an open model
  as incompatible otherwise.
- If consumers may lag several versions, require transitive compatibility and keep the
  full migration chain.

---

## 7. Naming conventions

Consistency within an API is paramount — mixing conventions in one payload is the worst
outcome.

| Concern | Rule | Example |
|---|---|---|
| Key case | `camelCase` for JS-centric/public APIs; `snake_case` for Python/DB-aligned APIs. Pick one per API, enforce with a linter | `firstName` / `first_name` |
| First character | Letter, `_`, or `$` (Google JSON Style Guide) | — |
| Kebab-case | Never — forces bracket notation in most languages | ~~`first-name`~~ |
| Reserved words | Avoid language keywords as keys | ~~`class`~~, ~~`type`~~ (caution) |
| Arrays | Plural nouns | `orders`, `lineItems` |
| Booleans | Positive framing | `isActive`, not `isNotDeleted` |
| Timestamps | ISO 8601 UTC | `"2026-06-07T10:30:00Z"` |
| Domain fields | One canonical name per concept, everywhere | always `userId`, never `uid`/`user_id` mixed |

- **Consistent types across responses and versions** — never `42` in one response and
  `"42"` in another.
- **Never leak database internals**: sequential IDs as identity, table/column names,
  soft-delete flags.
- Enforce naming and structure with a linter (Spectral, vacuum) in CI.

---

## 8. Testing and tooling

- **Every schema gets tests against both valid AND invalid fixtures** in CI. A schema
  only tested with valid data hides accept-everything bugs (e.g. an unasserted
  `format`, a misplaced `required`).
- **Validators:** Ajv (JS/TS — use the `ajv/dist/2020` build for 2020-12, add
  `ajv-formats` for format enforcement), `@hyperjump/json-schema` (JS, bundling),
  Python `jsonschema`, `json-everything` (.NET). One shared validator instance per
  process.
- **Linting/governance:** Spectral, vacuum, `jsonschema` CLI (format/lint/test/bundle).
- **Conversion:** AlterSchema (between drafts), `openapi-schema-to-json-schema`.
- **Codegen:** quicktype, openapi-generator, TypeBox. TypeScript types are compile-time
  only — pair them with runtime validation (JSON Schema or Zod); use both, not either.
- **OpenAPI 3.1 is a superset of JSON Schema 2020-12** — schemas are portable. When
  migrating from 3.0: `nullable: true` → `"type": [..., "null"]`, boolean
  `exclusiveMinimum/Maximum` → numeric, single-value `enum` → `const`, singular
  `example` → `examples`.

---

## 9. Performance

- **Compile once, validate many.** Ajv compiles each schema into an optimized JS
  function; calling `ajv.compile()` per request is the single most common performance
  mistake. Compile at startup (or precompile to standalone code for hot paths) and
  reuse the compiled function:

```javascript
// startup
import Ajv2020 from "ajv/dist/2020";
const ajv = new Ajv2020();
const validateUser = ajv.compile(userSchema);   // once

// request path
if (!validateUser(payload)) handle(validateUser.errors);  // reuse
```

- **Recursive schemas and deep `allOf`/`oneOf`/`anyOf` chains can exponentially
  increase processing time.** Flatten where possible.
- **Replace `oneOf` with a discriminator** on hot paths — only the matching branch is
  validated, and error messages improve.
- `unevaluatedProperties` is a dynamic keyword processed after all static keywords — it
  fixes composition (§5) but is not free; don't sprinkle it where a plain open model
  suffices.
- Ajv knobs: `loopRequired`/`loopEnum` default to 200 (above that, slower loop-based
  validation); `ajv-formats` is opt-in because bundling all format regexes is costly.
- Guard against **ReDoS** in `pattern`: anchor, keep regexes simple, bound length.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Omitting `$schema` | Always declare the 2020-12 dialect URI |
| `$id` with a fragment, or no `$id` | Absolute, fragment-free `$id` per file |
| `additionalProperties: false` in/under composition | `unevaluatedProperties: false`, discriminator, or open model |
| Relying on `format` for validation | Pair with `pattern`, enable format assertion, or validate in app layer |
| `enum` combined with `type` | `enum` alone |
| Custom `format` values | New keyword or `pattern` |
| `nullable: true` | `"type": ["...", "null"]` |
| Everything `required` / overly strict v1 | Only truly mandatory fields; leave room to evolve |
| Retyping or renaming a shipped field | Additive change + three-phase deprecation |
| Dynamically-keyed objects for lists | Arrays of homogeneous items |
| Referencing another file's `$anchor` | Standalone resource with own `$id` |
| Runtime remote `$ref` resolution | Build-time bundling |
| `ajv.compile()` per request | Compile once at startup, reuse |
| Only-valid-data tests | Valid and invalid fixtures in CI |
| Mixed key casing / mixed types across responses | One convention, one type, linted |

---

## Pre-flight checklist — run before delivering any schema

Before presenting a schema you wrote or approving one you reviewed, verify each item.
If any check fails, fix it before delivery.

1. `$schema` declares Draft 2020-12; `$id` is absolute and fragment-free.
2. Root has `title` and `description`; non-obvious properties documented; `examples`
   present.
3. `required` lists only genuinely mandatory fields; every nullable field has a
   justified `null`-vs-absent distinction.
4. No `additionalProperties: false` anywhere near `$ref`/`allOf`/`oneOf`/`anyOf` — used
   `unevaluatedProperties: false`, a discriminator, or an open model instead.
5. No `format` relied on for enforcement without a paired `pattern` or explicit
   format-assertion setup; all `pattern`s anchored; user-supplied strings bounded with
   `maxLength`.
6. No `enum`+`type` combos, no `nullable: true`, no custom `format` values.
7. Subschemas used more than once live in `$defs`; nesting ≤ 3 levels; no
   dynamically-keyed objects.
8. Naming: one case convention throughout, plural arrays, positive booleans, ISO 8601
   UTC timestamps, canonical domain field names.
9. Versioned `$id` when the schema is a published contract; changes since the previous
   version are additive (or follow three-phase deprecation).
10. Validator guidance included where relevant: compile-once pattern, `ajv-formats` if
    format enforcement is expected, valid + invalid test fixtures.
