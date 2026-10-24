---
name: zeno-performance-profiling
description: >
  Cross-layer, profiling-driven performance work — find out why something is measurably slow
  before touching it, fix it, and prove with a profiler that the fix moved the number. Covers
  page-load metrics, algorithmic complexity, bundle size, network/API patterns, and memory leaks;
  confirms (but doesn't deep-fix) database and React-render bottlenecks. Trigger on: "it's slow",
  "optimize performance", "reduce bundle size", "memory leak", "profile this", "Core Web Vitals",
  "bottleneck", "N+1 query".
---

# Cross-Layer Performance Profiling

Find out why something is slow before you touch it. Every fix here is paired with a way to
measure whether it actually helped — a change that "should" be faster but was never profiled
before and after isn't a performance fix, it's a guess.

## Start by measuring

```bash
npx source-map-explorer build/static/js/*.js   # bundle composition
npx lighthouse https://your-app.com --view      # page-load audit
node --prof your-app.js && node --prof-process isolate-*.log   # CPU profiling
# React DevTools -> Profiler tab, record an interaction
```

Never optimize from a hunch about which function is slow — profile first, fix what the profiler
points at, then profile again to confirm the fix moved the number.

## Page-load targets

| Metric | Target | If it's over |
|--------|--------|---------------|
| First Contentful Paint | < 1.8s | Shrink the critical rendering path, inline critical CSS |
| Largest Contentful Paint | < 2.5s | Lazy-load below-the-fold images, speed up server response |
| Time to Interactive | < 3.8s | Split code, ship less JavaScript up front |
| Cumulative Layout Shift | < 0.1 | Reserve space for images/embeds before they load |
| Bundle size (gzipped) | < 200KB | Tree-shake, lazy-load routes, drop unused dependencies |

## Algorithmic complexity

The highest-leverage review question: "what's the Big-O here, and does it need to be?"

| Smell | Cost | Fix |
|---|---|---|
| Searching one array inside a loop over another | O(n·m) | Build a `Map`/`Set` once, look up in O(1) |
| Sorting inside a loop | O(n² log n) | Sort once, outside the loop |
| String concatenation in a loop | O(n²) | Build an array and `.join()` |
| Unbounded recursion with overlapping subproblems | O(2^n) | Memoize |

## Bundle, network, and memory

Find what's actually in the bundle (`npx webpack-bundle-analyzer`) before guessing what to cut.
Parallelize independent network calls (`Promise.all`), cache responses that don't need refetching,
debounce input-driven calls. For memory leaks, the pattern behind nearly every one: something
registers a subscription/listener/timer and nothing tears it down — confirm with a heap-snapshot
diff (take one, repeat the suspect action, take another, diff) before assuming a leak exists.

## Database and React-render: confirm, don't deep-fix

Confirm — via slow-query logs, `EXPLAIN ANALYZE`, connection-pool metrics — that a suspected
bottleneck actually is the database; hand deep query rewriting, indexing, and schema fixes to the
Postgres leaf rather than reproducing that checklist here. Same split for React: a profiler-traced
render slowdown stays here; review-time lint-style checks (memoization discipline, `key={index}`,
Suspense placement) with no profiler trace behind them belong to `zeno-react-patterns` instead.

## Turning findings into a report

Lead with numbers, not adjectives: file:line, concrete cost (ms/KB/MB), the specific fix, ideally
a before/after snippet. Close with an estimated aggregate impact.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Optimizing from a hunch, no profiler run | Profile first, fix what it points at, profile again to confirm |
| Reproducing the Postgres or React-review checklist here | Confirm via profiling, then hand off — don't duplicate a sibling leaf |
| Reporting "should be faster" with no numbers | Lead with file:line and concrete cost; show before/after |
| Calling it done because the code "looks" optimized | Confirm the specific metric moved, via a fresh profiler run |

## Pre-flight checklist — run before delivering any performance fix

- [ ] A profiler run (not a hunch) identified the actual bottleneck before any fix was applied.
- [ ] The fix is re-profiled to confirm the targeted metric moved.
- [ ] Database/React-render bottlenecks were confirmed here and handed off, not deep-fixed here.
- [ ] Findings report file:line, concrete cost, and the specific fix.
- [ ] Core Web Vitals in range, bundle under budget, no new leak in a heap diff, tests still pass.
