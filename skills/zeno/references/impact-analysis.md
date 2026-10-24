# Impact analysis — know the blast radius before you change a symbol

Before changing a **public/shared symbol** (a function, type, endpoint, config others depend on),
know what it touches: who calls it, what imports it, what breaks if its behavior changes. An LLM that
greps blindly burns tokens and still misses callers; a structural answer is cheaper and more complete.

This is a **graph-assisted** habit, not a graph-*required* one. It uses a graph **if one already
exists** — it never asks you to stand up or maintain graph infrastructure. No graph → fall back, and
lose nothing.

## Tool ladder (cheapest-first, always available)

1. **`graphify-out/graph.json` exists** → query the graph (read-only, ~10× cheaper than re-grepping):
   - `graphify query "who calls X / what depends on X"` — callers and dependents.
   - `graphify path "X" "Y"` — how two symbols connect; trace a data path.
   - The `graphify` skill's fast path already answers NL codebase questions from the graph without a rebuild.
2. **else `docs/CODEMAPS/` exists** → read the relevant codemap: the `route → controller → service →
   repo` chains and per-module Exports/Dependencies tables give the blast radius in prose.
3. **else** → structural grep: the symbol's definition, everything that imports it, and its call sites.

## Record it

Put the impacted surface where Execution and Review will see it: update `.zeno/project.md`'s **State**
section, and add a **Decisions** line on the active card (the Feature card if this surfaced during
DDD, the Story card if it surfaced during Execution) when the blast radius is non-obvious ("changing
`AuthConfig` touches `login`, `refresh`, and the 3 middleware callers"). This is the memory the
later gates rely on.

## Graph-driven test selection (Execution-time speed-up only)

From the impacted callers/modules, select the tests that exercise them and **run those first** during
the RED/GREEN cycle for fast feedback. This is about *ordering*, not *coverage*:

- **The full suite still gates "done" at Review.** Never use the impact set to skip the full run — a
  narrowed run is for speed during Execution, not a substitute for goal-backward verification.

## Honesty — it's a guide, not a guarantee

- graphify tags edges `EXTRACTED` / `INFERRED` / `AMBIGUOUS`. When the edges you're relying on are
  inferred or ambiguous, **widen the net** — impact analysis narrows *where to look first*, it doesn't
  prove completeness.
- A `graphify-out/` graph or a codemap can **lag the code**. Treat the answer as a starting map; the
  Review-gate full suite is the backstop. `graphify --update` / `--watch` refresh a graph if you want,
  but the loop never mandates it.

## When to skip it

A purely local change (a private helper, a one-file edit with no external callers) doesn't need this —
don't manufacture analysis. Reach for it when the change touches a shared or public surface.
