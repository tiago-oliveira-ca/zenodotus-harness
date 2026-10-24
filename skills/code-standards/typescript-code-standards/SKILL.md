---
name: typescript-code-standards
description: >
  Production-grade TypeScript/JavaScript LANGUAGE standards: `unknown`-not-`any`, discriminated
  unions, utility types, branded IDs, strict null handling, async/Promise correctness, typed
  errors, ESM/CommonJS interop, strict tsconfig. Angular framework standards nest under
  `frameworks/angular.md`. Use whenever writing, reviewing, or refactoring any TypeScript or
  JavaScript. Trigger on: "TypeScript", "type safety", "generics", "discriminated union",
  "tsconfig", "unknown vs any", "strictNullChecks", "ESM vs CommonJS", "branded type", "Angular
  component", "NgRx", "SignalStore", "standalone component", "signals", "zoneless",
  "micro-frontend", "single-spa", "module federation", "Angular Elements", "combine Angular and
  React", or any TypeScript/JavaScript or Angular development, review, or refactoring task.
---

# TypeScript & JavaScript Code Standards

When generating, reviewing, or refactoring TypeScript or JavaScript, adhere to these
standards. TypeScript is a **structural, gradually-typed** superset of JavaScript: its type
system is erased at runtime and is deliberately unsound in a few places. Idiomatic TS leans on
the type system to make illegal states unrepresentable at compile time, while never forgetting
that types are gone by the time the code runs — runtime validation at trust boundaries is not
optional. Authoritative sources: the TypeScript Handbook (typescriptlang.org), the TC39
proposals, and the `@typescript-eslint` docs.

This file covers the **language**. Framework standards live under `frameworks/` — currently
only `frameworks/angular.md`. When a task is Angular-specific, read this file first, then
`frameworks/angular.md`.

## The one rule everything else hangs off

> **The type system describes what is already true at runtime — it does not enforce it.**

Every rule below is downstream of that. `any` lies to the compiler; an unvalidated `as`
assertion lies to the compiler; a `JSON.parse` typed as `User` lies to the compiler. The
compiler believes all three and then the lie surfaces as a runtime `TypeError` far from its
cause. Narrow from `unknown`, validate at boundaries, and let the types carry the truth
inward.

## Epistemic calibration — verify before asserting

TypeScript ships a new minor roughly quarterly and the tooling churns faster than the
language. Treat these as different tiers of confidence:

- **Settled, safe to assert directly:** `strict` mode, `unknown` over `any`, discriminated
  unions, `as const`, structural typing, `readonly`, optional chaining/nullish coalescing,
  `async`/`await` over raw `.then()` chains, `useUnknownInCatchVariables` (default under
  `strict` since TS 4.4). These are stable language facts.
- **Version-gated — check the installed TS version before relying on syntax:**
  `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`,
  `const` type parameters (TS 5.0+), `using`/`await using` explicit resource management
  (TS 5.2+), the `satisfies` operator (TS 4.9+), stable decorators (TS 5.0, the TC39
  version — not the legacy `experimentalDecorators` ones), and `isolatedDeclarations`
  (TS 5.5+). Confirm against the project's `typescript` dependency before quoting exact
  behavior.
- **Ecosystem-churny — verify current status, don't assert from memory:** Biome vs.
  `@typescript-eslint` maturity and rule coverage, whether a given runtime (Node, Deno, Bun)
  needs a loader/flag for `.ts` or ESM, and the exact `exports`-map resolution behavior of
  bundlers. These move fast; check before recommending a specific flag or version.

---

## 1. Type-system idiom

### `unknown`, never `any`

`any` disables type-checking for every value it touches and silently spreads outward. `unknown`
is the type-safe top type: it accepts anything but permits nothing until you narrow it. Reach
for `unknown` at every boundary where the shape is not yet proven (parsed JSON, `catch`
clauses, `postMessage` payloads, third-party untyped modules).

```typescript
// ❌ Wrong: any turns off the compiler for everything downstream
function handle(data: any) {
  return data.user.name.toUpperCase(); // no error; explodes at runtime if wrong
}

// ✅ Correct: unknown forces you to prove the shape before use
function handle(data: unknown): string {
  if (
    typeof data === "object" && data !== null &&
    "user" in data && typeof (data as { user: unknown }).user === "object"
  ) {
    // ...narrow fully, or validate with a schema library (zod/valibot) at the boundary
  }
  throw new TypeError("unexpected payload shape");
}
```

- Ban `any` with `@typescript-eslint/no-explicit-any` **and** `no-unsafe-*` rules — the latter
  catch `any` that leaks in from untyped dependencies, which `no-explicit-any` alone misses.
- The rare legitimate `any` (e.g. a genuinely variadic internal cache) gets an inline
  `// eslint-disable-next-line` with a one-line justification — never a blanket disable.
- For real boundary validation prefer a schema validator (zod, valibot, typebox) that produces
  both a runtime check and a static type from one declaration, rather than hand-written type
  guards you have to keep in sync.

### Discriminated unions are the idiom for sum types

TS has no native enum-with-payload. The idiomatic sum type is a **discriminated (tagged)
union**: an object union sharing a literal `kind`/`type` field. The compiler narrows
exhaustively on that field and — with a `never` default — tells you at compile time when a new
case is unhandled.

```typescript
type Result<T> =
  | { kind: "ok"; value: T }
  | { kind: "err"; error: string };

function render(r: Result<number>): string {
  switch (r.kind) {
    case "ok":  return `= ${r.value}`;
    case "err": return `! ${r.error}`;
    default:    return assertNever(r); // compile error if a case is added and unhandled
  }
}
function assertNever(x: never): never {
  throw new Error(`unhandled case: ${JSON.stringify(x)}`);
}
```

- Prefer a discriminated union over a "bag of optionals" (`{ value?: T; error?: string }`),
  which makes illegal states — both present, both absent — representable.
- Prefer it over TS `enum` for domain state. String-literal unions are erased, tree-shakeable,
  and don't create a runtime object; `enum` (especially numeric `enum`) has surprising runtime
  semantics and reverse-mapping. If you need a runtime object, use `as const`.

### Literal types + `as const`

`as const` freezes a value to its narrowest literal type and makes it deeply `readonly` —
the modern replacement for `enum` and for hand-written literal unions.

```typescript
// ✅ Correct: one declaration yields both a runtime value and a literal union type
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number]; // "admin" | "editor" | "viewer"
```

Use `satisfies` (TS 4.9+) when you want a value checked against a type **without widening** it —
you keep the precise literal types while still getting the constraint checked:

```typescript
const config = { port: 8080, host: "0.0.0.0" } satisfies Record<string, unknown>;
config.port.toFixed(); // still known to be `number`, not widened to `unknown`
```

### Utility types over hand-rolled mapped types

Reach for the built-ins — `Partial`, `Required`, `Readonly`, `Pick`, `Omit`, `Record`,
`Exclude`, `Extract`, `ReturnType`, `Parameters`, `Awaited`, `NonNullable` — before writing a
bespoke mapped type. They are readable at a glance and maintained by the compiler. Derive types
from a single source of truth rather than duplicating shapes:

```typescript
// ✅ Correct: derive, don't duplicate
type User = { id: UserId; name: string; email: string; passwordHash: string };
type PublicUser = Omit<User, "passwordHash">;
type UserPatch = Partial<Pick<User, "name" | "email">>;
```

Write a custom mapped/conditional type only when the built-ins genuinely can't express the
transform — and when you do, keep it small and named. Deep conditional-type metaprogramming is
a maintenance and compile-time-performance cost; a little duplication often beats an
unreadable type-level program.

### Generics: variance and structural subtyping

Bound type parameters to exactly what the body uses; don't over-constrain. TS infers variance
structurally — you don't annotate `in`/`out` except on the rare optional variance-annotation
(TS 4.7+) used to document or speed up checking. Two consequences worth stating plainly:

- **TS has no nominal typing by default.** Two types with the same structure are
  interchangeable regardless of their names or `class` identity. `class Meters` and
  `class Seconds` with the same fields are assignable to each other. This is a real bug source
  — see branded types below.
- **Function parameters are bivariant for methods but contravariant for standalone function
  types** under `strictFunctionTypes`. If a callback of yours accepts a wider type than
  expected, that's the check working, not a bug to `as`-away.

Prefer `unknown` to `any` as a generic default/constraint, and prefer `readonly T[]` /
`ReadonlyArray<T>` in parameter positions so callers know you won't mutate.

### Branded / nominal typing for IDs

Because typing is structural, a `string` user-id and a `string` order-id are interchangeable.
Brand them to make a mix-up a compile error — the TS analogue of Rust's newtype and Swift's
`Tagged`:

```typescript
type Brand<T, B extends string> = T & { readonly __brand: B };
type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

const asUserId = (raw: string): UserId => raw as UserId; // single validated constructor
function loadUser(id: UserId) { /* ... */ }
// loadUser(someOrderId); // ❌ compile error — brands don't match
```

The brand exists only at compile time (zero runtime cost); confine the `as`-cast to one
validating constructor per brand rather than sprinkling casts at call sites.

### Template literal types

Use them to type string patterns precisely — route params, event names, CSS units, i18n keys:

```typescript
type Route = `/users/${string}` | `/orders/${OrderId}`;
type EventName = `on${Capitalize<"click" | "hover">}`; // "onClick" | "onHover"
```

Powerful, but don't build a parser in the type system for its own sake — reach for them when
they prevent a real class of stringly-typed bug, not to show off.

---

## 2. Structural typing — consequences

Structural (duck) typing is the default and mostly a convenience, but it has sharp edges:

- **Excess-property checks fire only on fresh object literals.** `fn({ a: 1, b: 2 })` errors on
  the unexpected `b`, but assigning that literal to a variable first and passing the variable
  does not — the check is a lint on literals, not a guarantee. Don't rely on it for safety.
- **A wider object is assignable where a narrower one is expected**, extra properties and all.
  This is why a function receiving "just the fields it needs" happily accepts a much larger
  object — fine, but it means the type is a *lower bound*, not an exact shape.
- **`interface` vs `type` matters less than folklore claims.** Both describe object shapes and
  are near-interchangeable. The real differences: `interface` supports **declaration merging**
  (multiple declarations combine — essential for augmenting third-party or global types,
  a footgun everywhere else) and can feel marginally better in editor errors; `type` can
  express unions, tuples, mapped and conditional types that `interface` cannot. Practical rule:
  `type` for unions/tuples/utility compositions and public API shapes you don't want silently
  merged; `interface` when you specifically want extensibility or must augment an existing
  declaration. Pick one convention per codebase and enforce it with a lint rule rather than
  litigating it per-file.

---

## 3. Null & undefined handling

Enable `strictNullChecks` (part of `strict`) — without it `null`/`undefined` inhabit every
type and the whole discipline collapses. With it on:

- **`?.` optional chaining** short-circuits to `undefined` on a nullish link instead of
  throwing. **`??` nullish coalescing** supplies a default *only* for `null`/`undefined`.
- **`??` vs `||` is a real bug distinction.** `||` falls back on every falsy value — `0`, `""`,
  `false`, `NaN` — which is almost always wrong for numbers, booleans, and strings that may
  legitimately be empty or zero. Use `??` unless you specifically intend all-falsy fallback.

```typescript
// ❌ Wrong: 0 and "" are valid but || overrides them
const port = input.port || 8080;      // input.port === 0 → 8080 (bug)
const label = input.label || "N/A";   // input.label === "" → "N/A" (maybe a bug)

// ✅ Correct: fall back only on null/undefined
const port = input.port ?? 8080;      // 0 stays 0
const label = input.label ?? "N/A";   // "" stays ""
```

- Prefer modeling genuinely-absent values with `T | undefined` (or a discriminated union) over
  `null`; pick one of `null`/`undefined` as your "absent" convention and stay consistent
  (TS/JS APIs lean `undefined`; JSON and many DBs emit `null` — normalize at the boundary).
- `!` non-null assertion is a lie to the compiler; use it only where an invariant is provable
  and a narrowing guard genuinely can't express it, with a comment. `arr[i]!` is a common
  offender — turn on `noUncheckedIndexedAccess` and narrow instead.

---

## 4. Immutability

- **`readonly` on properties** and **`ReadonlyArray<T>` / `readonly T[]`** on parameters express
  intent and block accidental mutation at compile time (erased at runtime — no runtime cost).
- **`as const`** makes an entire literal deeply `readonly` and is the go-to for constant data.
- **`Object.freeze` is runtime and shallow.** It freezes only the top level — nested objects
  and arrays remain mutable. Don't assume `freeze` gives deep immutability; it doesn't, and it
  costs a runtime check. For deep runtime immutability you need a recursive freeze or a
  persistent-data-structure library — usually the compile-time `readonly` discipline plus
  immutable update patterns (spread, `.map`, structural sharing) is the right answer, not
  freezing everything.

```typescript
// ❌ shallow: nested still mutable
const cfg = Object.freeze({ server: { port: 80 } });
cfg.server.port = 9000; // silently succeeds

// ✅ compile-time deep readonly, zero runtime cost
const cfg = { server: { port: 80 } } as const;
// cfg.server.port = 9000; // compile error
```

---

## 5. Async & Promises

- **`async`/`await` over raw `.then()` chains** for readability and correct error propagation.
  Reserve `.then()`/`.catch()` for the rare spot where you deliberately don't want to await.
- **Never float an unawaited promise.** A promise you neither `await` nor `.catch()` swallows
  its rejection (an unhandled rejection that can crash Node) and destroys ordering guarantees.
  Enforce `@typescript-eslint/no-floating-promises`. If you truly mean fire-and-forget, mark it
  explicitly with `void` **and** an attached error handler.

```typescript
// ❌ floating — rejection is lost, ordering unguaranteed
sendAnalytics(event);

// ✅ awaited, or explicitly voided with handling
await sendAnalytics(event);
void sendAnalytics(event).catch(reportError); // deliberate fire-and-forget
```

- **Pick the right combinator.** `Promise.all` — fail fast, need all results (rejects on first
  rejection, and the others keep running). `Promise.allSettled` — need every outcome regardless
  of individual failures. `Promise.race` — first to settle wins. `Promise.any` — first to
  *fulfill* wins. Sequential `await` in a loop is correct only when each step depends on the
  previous; independent work should run concurrently under `Promise.all`.
- **Don't mix `await` inside `Array.prototype.forEach`** — `forEach` ignores the returned
  promises. Use `for...of` for sequential, or `await Promise.all(items.map(async ...))` for
  concurrent.
- **`AbortController` is the standard cancellation mechanism** — thread an `AbortSignal` into
  `fetch`, timers, and event listeners so in-flight work can be cancelled (route change,
  component unmount, timeout). Prefer it over ad hoc "isCancelled" booleans.
- **Errors in async code propagate as rejections**; a `try/catch` around `await` catches them,
  a missing `await` does not. Never leave an `async` function's rejection unhandled.

---

## 6. Error handling

- **`catch` binds `unknown`** under `strict` (`useUnknownInCatchVariables`, TS 4.4+). Anything
  can be thrown in JS — a string, `undefined`, a non-`Error` object — so narrow before use:

```typescript
try {
  await work();
} catch (err) {
  if (err instanceof AppError) return handleKnown(err);
  const message = err instanceof Error ? err.message : String(err);
  logger.error({ message }, "unexpected failure");
  throw err; // re-throw what you can't handle; don't swallow
}
```

- **Extend `Error` correctly, and mind the `instanceof` gotcha.** When targeting older JS
  (`target` below ES2015) or through some bundler/transpiler configurations, subclassing the
  built-in `Error` can break `instanceof` because the prototype chain is lost. The portable
  fix is to restore the prototype in the constructor; also set `name`:

```typescript
class AppError extends Error {
  constructor(message: string, readonly code: string) {
    super(message);
    this.name = "AppError";
    Object.setPrototypeOf(this, AppError.prototype); // guard instanceof across targets/realms
  }
}
```

  `instanceof` is also unreliable **across realms** (iframes, worker threads, vm contexts) where
  the two `Error` constructors differ — for cross-realm or serialized errors, discriminate on a
  stable own-property (`code`/`kind`) instead of `instanceof`.
- **Typed error unions vs. exceptions — a genuine judgment call.** Exceptions are the JS-native
  path and interoperate with the whole ecosystem; a `Result<T, E>` discriminated union (or a
  library like neverthrow) makes the failure explicit in the type and forces the caller to
  handle it, at the cost of ceremony and friction with throwing APIs. Reach for `Result` in a
  bounded core with well-defined failure modes (parsing, validation, domain rules); use
  `throw` at I/O and framework boundaries. Don't force one style across an entire codebase —
  and don't invent a half-typed hybrid that throws *and* returns errors for the same operation.
- **Never swallow.** An empty `catch {}` or a `catch` that only logs and continues hides
  failures. Handle, re-throw, or convert to a typed failure — always one of the three.

---

## 7. Module system

- **ESM is the target for new code** (`import`/`export`). CommonJS (`require`/`module.exports`)
  remains everywhere in the Node ecosystem, so interop still bites:
  - **`esModuleInterop`** (keep it on) smooths `import x from "cjs-module"` default-import
    mismatches; without it you need `import * as x` for many CJS packages. It must agree across
    a project and its consumers.
  - **`package.json` `"type"`** decides how `.js` is parsed: `"type": "module"` = ESM,
    `"commonjs"` (or absent) = CJS. Get this wrong and you get `ERR_REQUIRE_ESM` /
    "cannot use import statement" at runtime.
  - **The `"exports"` map** is the modern way to declare a package's public entry points and
    per-condition (`import`/`require`/`types`) resolution. It also *encapsulates* — deep imports
    into paths not listed in `exports` stop working. Prefer it over the legacy `"main"` for new
    packages, and list a `types` condition so consumers get declarations.
  - **`.mts` / `.cts`** force a single file's module system regardless of the package `"type"` —
    reach for them only when you must mix (e.g. one CJS config file in an ESM package).
- **No default exports as a default.** Named exports are refactor-safe, tree-shake predictably,
  and keep import names consistent across a codebase; default exports invite rename drift and
  interop friction. Reserve default export for where a framework requires it.
- Keep imports at the top; use dynamic `import()` only for genuine code-splitting/lazy-loading.
  Set `moduleResolution` to `bundler` (or `nodenext` for a published Node package) — not the
  legacy `node`/`classic`.

---

## 8. Naming conventions

Community-standard JS/TS naming (distinct from any framework's own rules):

| Entity | Convention | Example |
|---|---|---|
| Variables, functions, methods, properties | `camelCase` | `userCount`, `getById()` |
| Classes, interfaces, type aliases, enums | `PascalCase` | `UserRepository`, `OrderId` |
| Type parameters | single cap or descriptive `PascalCase` | `T`, `TValue`, `TKey` |
| Constants (true module-level immutables) | `UPPER_SNAKE_CASE` or `camelCase` | `MAX_RETRIES` |
| Enum members | `PascalCase` | `Status.Active` |
| Files | `kebab-case` or `camelCase` (pick one) | `user-repository.ts` |
| Boolean values | affirmative predicate | `isActive`, `hasAccess`, `canEdit` |

- **No Hungarian/affix noise:** don't prefix interfaces with `I` (`IUser`) or suffix types with
  `T` — that's a C#/legacy habit the TS style guides reject. Name the concept.
- Boolean-returning functions and boolean props read as assertions (`isEmpty`, not `empty`).
- Enforce mechanically with `@typescript-eslint/naming-convention` rather than by review.

---

## 9. Tooling & configuration

### `tsconfig.json` — the strict baseline

Start every project from `"strict": true` and add the checks it doesn't yet bundle. Each
non-obvious flag, with *why*:

```jsonc
{
  "compilerOptions": {
    "strict": true,                       // the umbrella: noImplicitAny, strictNullChecks,
                                          //   strictFunctionTypes, useUnknownInCatchVariables, …
    "noUncheckedIndexedAccess": true,     // arr[i] / obj[key] is T | undefined — kills the
                                          //   single most common "it was there, I swear" crash
    "exactOptionalPropertyTypes": true,   // `x?: T` means absent, not `T | undefined` present —
                                          //   distinguishes "missing key" from "key set to undefined"
    "noImplicitOverride": true,           // require `override` keyword — catches a renamed base
                                          //   method silently orphaning a subclass method
    "noFallthroughCasesInSwitch": true,   // guards discriminated-union switches
    "noImplicitReturns": true,
    "verbatimModuleSyntax": true,         // makes type-only imports/exports explicit; avoids
                                          //   CJS/ESM elision surprises
    "moduleResolution": "bundler",        // or "nodenext" for a published Node package
    "isolatedModules": true,              // safe single-file transpile (esbuild/swc/babel)
    "skipLibCheck": true                  // pragmatic: skip checking .d.ts of deps (build speed)
  }
}
```

`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, and `noImplicitOverride` are the three
most valuable checks that `strict` does **not** turn on for you — enable them deliberately.
They're version-gated (see the calibration note); confirm the installed TS supports them.

### Linters & formatters

- **`@typescript-eslint`** is the mature, most-rule-complete linter; enable its type-aware
  rules (`no-floating-promises`, `no-misused-promises`, `no-unsafe-*`, `await-thenable`,
  `no-explicit-any`, `naming-convention`) — these require `parserOptions.project` and are worth
  the extra type-check pass. **Biome** is a fast Rust-based alternative bundling lint+format;
  it's rapidly maturing but does not yet match type-aware ESLint coverage — verify current rule
  parity before choosing it for a codebase that leans on type-aware lint rules.
- **Prettier** owns formatting; keep it separate from lint (or use Biome's formatter). Don't
  encode formatting as lint errors.
- Run `tsc --noEmit` in CI as the source of truth — a linter is not a type-checker, and some
  builders (esbuild/swc) transpile without type-checking at all.

---

## 10. Testing baseline (framework-agnostic)

Deep test *methodology* (TDD red/green, coverage strategy) belongs to the zeno workflow, not
here. Language-level conventions only:

- **Vitest** for new projects (ESM-native, fast, TS out of the box); **Jest** remains
  widespread and fine. Both share the same describe/it/expect surface.
- Co-locate `*.test.ts` / `*.spec.ts` beside the unit under test, or under `__tests__/`.
- Name tests by behavior, not method: `describe("parseConfig", () => it("rejects a negative
  port", …))`.
- Type your test doubles — `vi.fn<[Args], Return>()` / `jest.fn()` typed to the real signature
  — so a mock drifting from the real contract is a compile error, not a silent green test.
- Keep tests independent; no shared mutable state between cases.

---

## 11. Framework selection

**This file is the language.** Framework standards live under `frameworks/`:

| Framework | File |
|---|---|
| Angular (TS style, patterns, DI, templates) | `frameworks/angular.md` |
| Angular framework API selection, version features, CLI/build tooling | `zeno-stack/zeno-angular-developer` (reciprocal split — style wins here, framework API wins there) |

Read this SKILL.md first for any TS/JS work; then, for Angular work, read `frameworks/angular.md`
(component architecture, signals, DI, routing, testing) and — for Angular styling — the nested
`ui-style/SKILL.md`.

React/Next.js, Node/Express, NestJS, and other framework references **do not exist in this
library yet**. Add a `frameworks/<name>.md` only when a real task needs it — don't author
framework docs speculatively. (Note: the harness's `zeno-stack` dispatcher already owns some
React/Node execution concerns; check there before duplicating.)

## Documentation & doc comments (TSDoc)

Public TypeScript surface is documented with TSDoc/JSDoc; TypeDoc renders the reference.
- `/** … */` on every exported class, interface, type, function, and public method.
- Use TSDoc tags: `@param`, `@returns`, `@remarks`, `@example`, `@throws`, `@deprecated`.
- Document the contract and edge cases, not the obvious — let the types carry the shape; a
  `@param` that just restates the parameter name is noise.

Cross-cutting doc discipline (drift, when to update, generators): see `documenting-code`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `any` (explicit, or leaked in from untyped deps) | `unknown` + narrowing, or a schema validator at the boundary |
| Unvalidated `as` cast / `JSON.parse(...) as User` | Validate at the boundary (zod/valibot); cast only inside a proven guard |
| `enum` (esp. numeric) for domain state | String-literal union, or `as const` object for a runtime value |
| "Bag of optionals" (`{ ok?; error? }`) | Discriminated union with a literal `kind` tag + `assertNever` default |
| Hand-rolled mapped type duplicating a shape | Derive with `Pick`/`Omit`/`Partial`/`ReturnType`/… |
| Raw `string` for `UserId` vs `OrderId` | Branded types with a single validating constructor |
| `x || default` for numbers/booleans/strings | `x ?? default` (fall back only on null/undefined) |
| `!` non-null assertion to silence the compiler | Narrow with a guard; `noUncheckedIndexedAccess` for index access |
| `Object.freeze` assumed deep/immutable | `as const` (compile-time deep readonly) or a recursive freeze |
| Floating unawaited promise | `await`, or `void p.catch(handle)` for deliberate fire-and-forget |
| `await` inside `Array.forEach` | `for...of` (sequential) or `Promise.all(map(async …))` (concurrent) |
| `Promise.all` when you need every outcome | `Promise.allSettled` |
| Empty `catch {}` / log-and-continue | Handle, re-throw, or convert to a typed failure |
| Subclassing `Error` without prototype/`name` fix | `Object.setPrototypeOf` + `this.name`; discriminate cross-realm on `code` |
| Default exports everywhere | Named exports (refactor-safe, tree-shakeable) |
| `interface`-vs-`type` litigated per file | One convention, lint-enforced; `type` for unions, `interface` to augment |
| `I`-prefixed interfaces / `T`-suffixed types | Name the concept; enforce with `naming-convention` |

## Pre-flight checklist — run before delivering any TypeScript/JavaScript code

- [ ] **No `any`** — explicit or leaked; boundaries narrow from `unknown` or validate with a schema
- [ ] **No unvalidated `as` cast** across a trust boundary (parsed input, network, `postMessage`)
- [ ] **Sum types are discriminated unions** with a literal tag and an exhaustive `assertNever` default — not bags of optionals or numeric enums
- [ ] **IDs and unit-like primitives are branded**, with a single validating constructor per brand
- [ ] **`??` (not `||`)** used for defaults on values that may be `0`/`""`/`false`
- [ ] **`strictNullChecks` on**; no gratuitous `!`; index access guarded (`noUncheckedIndexedAccess`)
- [ ] **No floating promises**; independent async work runs concurrently; the right `Promise` combinator is chosen; cancellation via `AbortController` where relevant
- [ ] **`catch` binds `unknown`** and narrows before use; nothing swallowed; custom `Error` subclasses restore the prototype and set `name`
- [ ] **Named exports** by default; module system consistent (`"type"`, `exports` map, `esModuleInterop` agree)
- [ ] **`tsconfig` strict** plus `noUncheckedIndexedAccess` / `exactOptionalPropertyTypes` / `noImplicitOverride` where the TS version supports them
- [ ] **`tsc --noEmit` clean** and type-aware lint rules pass — the build's transpiler may not type-check at all
- [ ] **Any quoted TS version / flag / tooling behavior** verified against the installed version, not asserted from memory
- [ ] **Framework work** also loaded the matching `frameworks/*.md` (Angular → `frameworks/angular.md`)
