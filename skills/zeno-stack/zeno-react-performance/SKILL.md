---
name: zeno-react-performance
description: >
  React and Next.js performance optimization rules organized into eight priority tiers —
  eliminating async waterfalls, bundle size, server-side performance, client-side data
  fetching, re-render optimization, rendering performance, JS micro-perf, and advanced
  patterns. Use when writing, reviewing, or refactoring React/Next.js code for speed, or
  diagnosing slow loads, high CPU, bundle bloat, or Core Web Vitals regressions. Trigger on:
  "why is this slow", "optimize this component", "reduce bundle size", "fix the waterfall",
  "too many re-renders", "improve LCP/INP/CLS", "performance review", "Next.js performance".
---

# React Performance

Performance rules for React 18/19 and Next.js, organized by priority so a review or refactor
tackles the highest-leverage fix first. Covers the same technical ground as several well-known
React performance guides — restructured and reworded as original zeno-owned content.

## Priority index

| Priority | Category | When it matters |
|---|---|---|
| 1 — CRITICAL | Eliminating waterfalls | Any `await` followed by an independent `await` |
| 2 — CRITICAL | Bundle size | First-load JS, route-level imports, third-party libs |
| 3 — HIGH | Server-side performance | RSC, Server Actions, API routes, SSR |
| 4 — MEDIUM-HIGH | Client-side data fetching | SWR / TanStack Query / raw `fetch` in hooks |
| 5 — MEDIUM | Re-render optimization | High-frequency state updates, parent-child fan-out |
| 6 — MEDIUM | Rendering performance | Long lists, animations, hydration |
| 7 — LOW-MEDIUM | JavaScript micro-perf | Hot loops, frequent allocations |
| 8 — LOW | Advanced patterns | Effect-event integration, stable refs |

## 1. Eliminating waterfalls (CRITICAL)

Every sequential `await` adds a full network round trip. Fix in this order:

```ts
// Check cheap sync conditions before awaiting remote data
async function Page({ id }: { id: string }) {
  if (!id) return null;                 // sync guard first
  const flag = await getFlag("show-page");
  if (!flag) return null;
  const data = await getData(id);
}

// Defer an await until the branch that actually uses it
if (mode === "guest") return renderGuest();
const user = await getUser(id);         // only reached when needed
return renderUser(user);

// Parallelize independent work
const [user, posts, followers] = await Promise.all([
  getUser(id), getPosts(id), getFollowers(id),
]);

// Partial dependencies: start early, await late
const userP = getUser(id);
const postsP = getPosts(id);
const profile = await getProfile(id);
if (profile.private) return null;
const [user, posts] = await Promise.all([userP, postsP]);
```

Push `<Suspense>` boundaries close to the data so the page paints what it can while slower
sub-trees stream in — but reserve layout space (skeleton / `min-height`) to avoid shift. In
Server Components, sibling `await`s inside one component run sequentially; splitting them into
sibling child components lets React run them in parallel.

## 2. Bundle size (CRITICAL)

- **Direct imports, not barrels.** `import { Button } from "@/components/Button"`, not
  `from "@/components"` — barrel files force the bundler to walk the whole module graph. Saves
  200-800ms of first-load JS in many real apps. Next.js 13.5+'s Optimize Package Imports
  automates this for listed packages; still import directly for anything unlisted.
- **Statically analyzable dynamic import paths** — `name === "home" ? import("./pages/home") :
  import("./pages/about")`, never `import(`./pages/${name}`)`.
- **Dynamic-import heavy components**: `dynamic(() => import("./HeavyChart"), { loading: () =>
  <Skeleton />, ssr: false })` for client-only widgets.
- **Defer third-party scripts** (analytics, support widgets) until after hydration via
  `next/script` with `strategy="afterInteractive"` or `"lazyOnload"`.
- **Conditional module loading** for role-gated code (`if (user.role === "admin") { const {
  AdminPanel } = await import("./admin/AdminPanel"); }`).
- **Preload on hover/focus** so the bundle is warm by the time the user clicks.

## 3. Server-side performance (HIGH)

```ts
// Every "use server" function is a public endpoint — authenticate and authorize inside it
"use server";
export async function deleteUser(formData: FormData) {
  const session = await getSession();
  if (!session?.user) throw new Error("Unauthorized");
  const targetId = String(formData.get("id"));
  if (session.user.role !== "admin" && session.user.id !== targetId) {
    throw new Error("Forbidden");
  }
  await db.user.delete({ where: { id: targetId } });
}

// React.cache() dedupes fetches within one request — three RSCs calling
// getUser("1") produce one DB query
import { cache } from "react";
export const getUser = cache(async (id: string) => db.user.findUnique({ where: { id } }));
```

Other rules: cache cross-request-stable data (config, lookup tables) outside React with an LRU
cache or `unstable_cache`; when the same data feeds multiple Client Components, lift the
Client Component up and pass `children` rather than re-serializing per consumer; hoist static
I/O (`readFileSync`) to module scope so it runs once; never hold mutable module-level state in
RSC/SSR — it's shared across every request, a race condition between users; minimize what's
serialized to the client by projecting columns at the DB layer; parallelize nested per-item
fetches with `Promise.all(users.map(...))`; use Next.js 15's `after()` for non-blocking
post-response work (logging, cache warming).

## 4. Client-side data fetching (MEDIUM-HIGH)

Use SWR or TanStack Query so multiple components calling the same hook share one request and
cache entry — never roll a bespoke `useEffect` + `fetch` for shared data. Deduplicate global
event listeners behind a singleton hook rather than one `addEventListener` per component. Mark
scroll listeners `{ passive: true }`. Version `localStorage` payloads and keep them small — the
API is synchronous and blocks the main thread.

## 5. Re-render optimization (MEDIUM)

```tsx
// Bad — subscribing to state used only inside a callback re-renders on every change
const count = useStore((s) => s.count);
const handler = () => doSomething(count);

// Good — read once, at call time
const handler = () => doSomething(useStore.getState().count);

// Bad — new array identity every render breaks memoization
<List items={items ?? []} />
// Good
const EMPTY: Item[] = [];
<List items={items ?? EMPTY} />

// Subscribe to a derived boolean, not the raw collection
const hasItems = useStore((s) => s.cart.length > 0);
```

Other rules: memoize expensive children with `memo`; use primitive effect dependencies, never
inline object/array literals; derive values during render, never via `useEffect`; wrap
callbacks passed down in `useCallback` with a functional `setState`; lazily initialize
expensive state (`useState(() => parseTree(largeInput))`); skip `useMemo` on cheap primitive
arithmetic — it's pure overhead there; split hooks with independent dependency sources instead
of bundling unrelated selectors; move interaction logic into event handlers instead of
`useEffect` so it runs only on the actual user action; wrap non-urgent updates in
`startTransition`; use `useDeferredValue` for expensive derived renders; use `useRef` for
frequently changing values that shouldn't trigger a re-render; never define a component inside
another component's render body — it creates a new type every render and unmounts children.

## 6. Rendering performance (MEDIUM)

- Animate a wrapper `<div>` around an SVG, not the SVG itself — the wrapper is
  GPU-accelerated, the SVG triggers paint.
- `content-visibility: auto; contain-intrinsic-size: auto 80px;` on list rows skips offscreen
  rendering — a major win past a few hundred rows.
- Hoist static JSX to a module-level constant when it never changes between renders.
- Reduce SVG path coordinate precision (`M10.123456,20.654321` -> `M10.12,20.65`) — sub-pixel
  difference, real byte savings.
- For values needed before hydration (theme, locale), inline a `<script>` that sets
  `document.documentElement.dataset.*` before React mounts, to avoid flicker.
- `suppressHydrationWarning` only on known-divergent leaf nodes (`<time>` with `Date.now()`),
  never on a subtree with other children.
- React 19's `<Activity mode="visible|hidden">` keeps state and effects mounted while hidden —
  cheaper than unmount/remount for tabs and accordions.
- Use a ternary for conditional render, not `&&` — `{count && <Badge>{count}</Badge>}` renders
  a literal `0` when `count` is `0`.
- Pair `startTransition` with `isPending` to keep the previous UI visible while the next
  state computes.
- Use React DOM's `preload`/`preconnect` resource hints; use `defer`/`async` on `<script>`
  tags appropriately (`defer` for ordered post-DOMContentLoaded execution, `async` for
  fire-and-forget).

## 7. JavaScript micro-perf (LOW-MEDIUM)

Batch DOM/CSS changes via class swap instead of property-by-property; use `Map` for repeated
lookups (`O(1)` vs. `O(n)`); cache array length and property access inside loops; memoize pure
functions with a module-level cache; cache `localStorage` reads (synchronous API); combine
`filter().map()` into one pass; check array length before expensive comparisons; return early;
hoist `RegExp` out of loops; loop for min/max instead of `sort()` (`O(n)` vs. `O(n log n)`);
use `Set`/`Map` for membership tests instead of `Array.includes`; prefer `toSorted()` over
mutation when immutability matters; use `flatMap` to map and filter in one pass; push
non-critical work to `requestIdleCallback`.

## 8. Advanced patterns (LOW)

Values from `useEffectEvent` are stable — don't add them to effect dependency arrays. For a
stable callback passed to a memoized child, keep the latest handler in a ref:

```tsx
const handlerRef = useRef(handler);
useEffect(() => { handlerRef.current = handler; });
const stable = useCallback((arg) => handlerRef.current(arg), []);
```

Guard module-level singletons (telemetry, logger) with a module-scope flag, not `useEffect`,
for init-once-per-app-load semantics.

## Automated tools

Several of these rules are now automated: Next.js 13.5+'s Optimize Package Imports handles
barrel-import bloat; the React Compiler is stable (1.0, October 2025) and auto-memoizes — in a
repo with it enabled (check `babel-plugin-react-compiler` / the framework's compiler flag before
advising), the tier-5 manual `useMemo`/`useCallback` rules are review-only noise, so verify the
compiler isn't already covering a memoization before recommending it by hand; Turbopack improves
tree-shaking; `@next/bundle-analyzer` visualizes first-load JS.

## Web Vitals mapping

| Metric | Most relevant tiers |
|---|---|
| LCP (Largest Contentful Paint) | Waterfalls, Bundle Size, Resource Hints |
| INP (Interaction to Next Paint) | Re-render, Rendering, JavaScript |
| CLS (Cumulative Layout Shift) | Rendering — Suspense placement, image dimensions |
| TBT (Total Blocking Time) | Bundle Size, JavaScript, Deferred Third-Party |

For the underlying component patterns these rules optimize, see `zeno-react-patterns`; for
verifying a fix under real user interaction, see `zeno-react-testing`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Sequential independent `await`s | `Promise.all` or start-early/await-late |
| Barrel imports (`from "@/components"`) | Direct imports per component |
| Dynamic `import()` with a template-literal path | Statically analyzable per-branch imports |
| Mutable module-level state in RSC/SSR | Request-scoped storage (`headers()`, `cookies()`) |
| `useEffect` + `fetch` for shared data | SWR or TanStack Query |
| `&&` for conditional render of a possibly-zero value | Ternary: `count > 0 ? <Badge/> : null` |
| Component defined inside another component's render | Hoist it to module scope |
| Manual `useMemo`/`useCallback` under React Compiler | Let the compiler handle it; keep only measured hot paths |

## Pre-flight checklist — run before delivering any React/Next.js performance change

- [ ] Independent `await`s are parallelized or reordered to start as early as possible
- [ ] No barrel imports and no template-literal dynamic import paths were introduced
- [ ] Every `"use server"` action authenticates and authorizes itself, independent of the caller
- [ ] Client Components receive only the data they need, not a wholesale server object
- [ ] Re-render-sensitive selectors read derived booleans/primitives, not whole objects
- [ ] Long lists are virtualized or use `content-visibility: auto`
- [ ] The change is justified by a profiler/Lighthouse measurement, not a guess
