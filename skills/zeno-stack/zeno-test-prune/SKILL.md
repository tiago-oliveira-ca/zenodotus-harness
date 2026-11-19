---
name: zeno-test-prune
description: >
  Prune tests that guard no behavior. Classify every test in a scope by what it depends on —
  intended behavior, the past, nothing, the implementation, or a duplicate — prove each delete
  with a mutation check, rewrite implementation-coupled tests against behavior, and remove
  production code that only existed for the removed tests. Trigger on: "prune tests",
  "/prune-tests", "remove useless tests", "tests that can't fail", "brittle tests", "tests coupled
  to implementation", "too many mocks", "clean up the test suite", "test suite bloat", or a
  review finding that tests restate the code.
---

# Test Pruning — keep only tests that guard behavior

When asked to clean up a test suite, or when a review finds tests that restate the code, judge
each test by what would have to change for it to fail. Keep it only when the answer is "intended
behavior". Everything else costs run time and blocks refactors while guarding nothing.

**Iron Law: KEEP A TEST ONLY IF IT CAN FAIL WHEN INTENDED BEHAVIOR BREAKS.** (Invariant — the
reason this skill exists. Everything below is a default for applying it.)

## Boundary — what this skill owns

- **Owns:** deciding which existing tests to keep, rewrite or delete, and removing production code
  that existed only for deleted tests.
- **Writing the replacement tests** follows the stack's testing leaf: `zeno-python-testing`,
  `zeno-react-testing` or `zeno-e2e-testing`. Load the matching one before rewriting.
- **Finding untested behavior** (coverage gaps) is `/test-coverage`, not this skill.
- **Dead production code in general** is `zeno-refactor-cleanup`; this skill removes only code whose
  sole callers were the tests it deleted.
- **Test specification documents** belong to the `testing` dispatcher.

## 1. What does the test depend on?

Ask what change would turn the test red. The answer puts it in one class:

| The test depends on | Typical signs | Verdict |
|---|---|---|
| **Intended behavior** | Asserts an observable result a caller or user relies on: a return value, an emitted event, a rendered state, a persisted row | **Keep** |
| **The past** | Asserts that a removed feature, field or call stays removed | **Delete** — history lives in git, not in the suite |
| **Nothing** | Mocks the unit under test; asserts a value it just set; re-checks what the type system or compiler already guarantees; tests the framework or a library rather than this code | **Delete** after the mutation check |
| **The implementation** | Asserts private state, internal call order or call counts on collaborators that are not a real boundary; computes the expected value with the same algorithm as the code; snapshots internals | **Rewrite** against the public behavior; delete only if that behavior is guarded elsewhere |
| **A duplicate** | Another kept test fails for the same break | **Delete** the weaker one; keep the clearest name and failure message |

Mocks at a real boundary (network, clock, filesystem, a paid API) are fine — the test still depends
on this code's behavior at that boundary. A mock of the thing being tested is not.

## 2. Procedure

1. **Fix the scope.** A path argument, the current diff, or one module at a time — never "the whole
   suite" in one pass. Inside the zeno loop this is a Story; record the scope on its card. Its
   mutation checks are the Task's RED/GREEN evidence, and a delete made this way is pruning, not the
   weakening `zeno-workflow/zeno-tdd` forbids.
2. **Get a green baseline.** Run the scoped tests and note the result. A red baseline means a
   bug or a broken test — route it to `zeno-debug` first; pruning does not start on red.
3. **Classify every test** in the scope using the table, and write a verdict table on the card:
   test id, class, one-line reason, verdict.
4. **Run the mutation check before any delete.** Make the smallest edit that breaks the behavior the
   test claims to guard (invert a condition, drop a line, return a constant). Run the test:
   - Still green → it guards nothing. Revert the break; delete the test.
   - Red → it guards something. Revert the break; reclassify (usually *the implementation*, so
     rewrite rather than delete).
   Record each check (the break and the result) in the card's Proof.
5. **Rewrite before you delete.** When a pruned test was the only one touching a behavior, first
   write a behavior-level test with the stack's testing leaf, prove it fails under the same break,
   then delete the old one.
6. **Remove test-only production code.** Accessors, flags, hooks or constructor parameters that only
   the deleted tests used: confirm no other caller (grep, then the stack's dead-code tool, per
   `zeno-refactor-cleanup`'s verification discipline) and remove them.
7. **Re-run the suite after each batch** — one class at a time, small enough to revert cleanly.

**Coverage will usually drop.** Coverage measures which lines ran, not which behavior is guarded.
Do not add tests back to restore the number. If a coverage gate in CI fails, report the trade-off to
the human rather than gaming it.

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "It's obviously useless, the mutation check is overkill" | Obvious-looking tests sometimes guard an edge case; the check takes a minute and the delete is permanent |
| "Better keep it, a test can't hurt" | A test that can't fail costs run time and blocks refactors; it hurts every change it touches |
| "I'll delete the brittle test and move on" | If it was the only guard on that behavior, you just removed coverage; rewrite first |
| "Coverage dropped, I should add something back" | Coverage is not the goal; guarded behavior is |
| "The helper is only used in tests, but it might be useful later" | Code that exists only for deleted tests is dead code; remove it |

## Red flags — stop, you're bypassing the discipline

- You're about to delete a test without having broken the behavior it claims to guard.
- You're rewriting a test and haven't loaded the stack's testing leaf.
- The scope is "the whole suite" with no per-module batches.
- The baseline was red and you started pruning anyway.
- The verdict table isn't on the card.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Deleting by judgment alone | Mutation check first: break the claimed behavior, observe the test stay green, revert |
| Keeping every test "just in case" | Keep only tests that depend on intended behavior |
| Deleting the only guard on a behavior | Write a behavior-level replacement first, prove it fails under the same break |
| Asserting private state or internal call order | Assert the observable result through the public interface |
| Computing the expected value with the code's own algorithm | Use a literal, independently derived expected value |
| Leaving test-only accessors and flags in production code | Remove them once no other caller remains |
| Restoring coverage numbers with filler tests | Report the trade-off; coverage is not guarded behavior |

## Pre-flight checklist — run before delivering any test-pruning batch

- [ ] Scope fixed (path, diff or module) and recorded; baseline run green.
- [ ] Every test in scope classified with a one-line reason in the card's verdict table.
- [ ] Every delete preceded by a recorded mutation check that left the test green.
- [ ] Every behavior whose only guard was removed has a behavior-level replacement that fails under the same break.
- [ ] Rewrites followed the stack's testing leaf.
- [ ] Test-only production code removed after confirming no other caller.
- [ ] Suite green after each batch; any coverage-gate trade-off reported to the human.
