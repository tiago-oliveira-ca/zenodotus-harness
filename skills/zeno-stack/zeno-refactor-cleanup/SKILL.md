---
name: zeno-refactor-cleanup
description: >
  Remove genuinely unused code, exports, and dependencies, and consolidate duplicate
  implementations — via detection tooling plus individual verification, in small reversible
  batches, never a bulk sweep. Trigger on: "remove dead code", "clean up unused exports",
  "consolidate duplicates", "run knip", "unused dependencies", "refactor cleanup".
---

# Dead-Code Cleanup & Consolidation

Dead code doesn't announce itself — a tool flags something as "unused," but tools don't know about
dynamic imports, reflection, or a public API surface someone outside this repo depends on. This is
detection-tool output plus verification before deletion, done in small, reversible batches, never
a bulk sweep.

## Detection tools

```bash
npx knip                                            # unused files, exports, and dependencies
npx depcheck                                        # unused npm dependencies specifically
npx ts-prune                                         # unused TypeScript exports specifically
npx eslint . --report-unused-disable-directives      # stale eslint-disable comments
```

Those cover JS/TS. **Detect the stack first** and use the matching analyzers elsewhere — this
library routes Python, Rust, Go and Swift heavily (R has no dead-code analyzer
this skill endorses — use the grep fallback below for R):

```bash
vulture src/                        # Python: unused code
deptry .                            # Python: unused/missing dependencies
cargo +nightly udeps                # Rust: unused dependencies
staticcheck ./...                   # Go: unused symbols (U1000)
periphery scan                      # Swift: unused code
```

No analyzer for the stack? Fall back to grep-driven reference counting — never skip detection
and delete by eye.

Treat their output as a starting hypothesis, not a deletion list — every candidate still needs
individual verification.

## Working loop

1. **Survey** — bucket every candidate by removal risk: *safe* (unused, no dynamic reference),
   *needs care* (only reachable via dynamic import or string-based lookup), *risky* (part of a
   public API another consumer might depend on).
2. **Verify each candidate individually** — grep for every reference, including string-based
   dynamic imports static tools miss; check public-API exposure; skim git history for context.
3. **Remove in small batches, safest first** — dependencies, then exports, then files, then
   duplicate consolidation. Run the test suite after each batch, not just at the end.
4. **Consolidate duplicates deliberately** — pick the most complete and best-tested
   implementation (not just the newest), repoint every caller, delete the others, confirm tests
   still pass.

## Before deleting anything

The detection tooling flags it as unused; a grep sweep (including dynamic/string-based
references) turns up nothing; it isn't part of a public API; tests still pass once it's gone.

## When not to run this

In the middle of active feature work; immediately before a deploy; on code with no test coverage
to catch a bad removal; on code you can't yet explain the purpose of.

## Discipline

Work one category at a time, verify after every batch. When a candidate's usage is ambiguous,
leave it — a false negative costs far less than a bad removal. Every batch gets its own
descriptive commit; "cleanup" is not a commit message that helps future debugging.

**Agent counterpart:** `agents/zeno-refactor-cleaner.md` (entry point: `/refactor-clean`) — the spawned standalone dead-code pass over this same doctrine (this skill is its Codex fold home).

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Deleting everything a tool flags in one pass | Bucket by risk, verify individually, remove safest-first in small batches |
| Trusting static analysis alone for dynamic/string-based usage | Grep for those references explicitly before deleting |
| One giant "cleanup" commit | One descriptive commit per batch, tests run after each |
| Removing an ambiguous candidate "to be safe" | Leave it — a false negative costs less than a bad removal |
| Running this mid-feature-work or pre-deploy | Don't — see "When not to run this" |

## Pre-flight checklist — run before delivering any cleanup batch

- [ ] Every candidate individually verified (grep sweep including dynamic references, public-API check).
- [ ] Removed in small batches, safest category first, tests + build run after each.
- [ ] Ambiguous candidates left in place, not removed.
- [ ] Each batch has its own descriptive commit stating what was removed and why it's safe.
- [ ] Not run during active feature work, immediately pre-deploy, or on untested/not-yet-understood code.
