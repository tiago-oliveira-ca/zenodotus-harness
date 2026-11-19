---
description: Prune tests that guard no behavior — classify, mutation-check, rewrite or delete.
argument-hint: "[optional path]"
---

# /prune-tests

Keeps only tests that can fail when intended behavior breaks. The doctrine lives in
`zeno-stack/zeno-test-prune`; load it and follow its procedure. Inside the zeno loop, this runs as a
Story whose card holds the verdict table and the mutation checks.

## Steps

0. **Open the zeno loop** — load `zeno` (an ad hoc Story unless the user names a bigger scope)
   and `zeno-stack/zeno-test-prune`.
1. **Scope** — `$ARGUMENTS` if given (a path), else the current diff's test files, else ask which
   module to start with. Never the whole suite in one pass.
2. **Baseline** — run the scoped tests; stop and route to `zeno-debug` if anything is red.
3. **Classify** — every test by what it depends on (behavior, the past, nothing, the implementation,
   a duplicate); write the verdict table on the card.
4. **Mutation check** — before each delete, break the claimed behavior, confirm the test stays green,
   revert.
5. **Rewrite, then delete** — re-cover any behavior that loses its only guard, using the stack's
   testing leaf (`zeno-python-testing`, `zeno-react-testing`, `zeno-e2e-testing`).
6. **Remove test-only production code** with no other caller.
7. **Re-run** the suite after each batch and report: kept / rewritten / deleted counts, the mutation
   checks, and any coverage-gate trade-off.
