# TDD — Concepts Reference

This is general, stack-agnostic theory. For the Python + FastAPI + Kafka-specific application of
these same ideas (Canon TDD, Khorikov's mocking rules, contract/event-driven testing), see
`code-standards/python/references/ddd-tdd-bdd-workflow.md`.

## What TDD actually is

A discipline where you write a small, failing test **before** the production code that satisfies
it. Kent Beck formalized it in *Test-Driven Development: By Example* (2002), framing the goal —
borrowing from Ron Jeffries — as **"clean code that works."**

The inversion: instead of designing the whole solution up front and verifying it after, a sequence
of small tests *drives* the design, one behavior at a time. It's not "testing" in the QA sense —
it's a **design and feedback technique** that produces a test suite as a side effect. What it buys:

- **Self-testing code** — one command tells you, with high confidence, whether the system works.
- **Interface-first design** — writing the test first forces you to think about *how the code will
  be used* before *how it will be built*, separating interface from implementation.

## Uncle Bob's Three Laws (the tighter version)

Robert C. Martin's stricter, finer-grained framing of the cycle:

1. You may not write production code until you have written a failing unit test.
2. You may not write more of a test than is sufficient to fail (not compiling counts as failing).
3. You may not write more production code than is sufficient to pass the currently failing test.

Followed strictly, this produces a rhythm measured in seconds to minutes, and guarantees that
essentially all production code exists *because* a test demanded it.

## Techniques for reaching GREEN

Three recognized ways to get from a failing test to the minimum passing code:

- **Fake it** — return a hard-coded value first, generalize once more tests force it.
- **Obvious implementation** — if the correct code is genuinely obvious, write it directly.
- **Triangulation** — when unsure of the right abstraction, add a second and third test case until
  a hard-coded value can no longer pass, forcing the real logic to emerge.

The discipline is restraint — writing more than the current test requires is the most common way
people quietly drift out of TDD.

## Simple design checkpoint (Beck)

Applied during REFACTOR, in priority order:

1. Passes all the tests
2. Reveals intention clearly (good names, clear structure)
3. Contains no duplication
4. Has the fewest elements possible

## Structuring an individual test: Arrange-Act-Assert

Most tests, any language, follow the same three-part shape (Bill Wake):

- **Arrange** — set up inputs, objects, any test doubles needed.
- **Act** — perform the one behavior under test.
- **Assert** — check the outcome matches what's expected.

Keeping these visually distinct, and testing one behavior per test, is what keeps tests readable
and diagnostic when they fail. The same shape appears in BDD as Given-When-Then.

## Test doubles — what to fake, and how

Vocabulary from Gerard Meszaros, popularized by Martin Fowler:

| Double | What it does | Fails the test if... |
|---|---|---|
| **Dummy** | Passed in but never actually used | never |
| **Stub** | Returns a fixed, canned answer | never |
| **Fake** | A real but simplified working implementation (e.g. in-memory list standing in for a DB) | never |
| **Spy** | A stub that also records how it was called | never (on its own) |
| **Mock** | Pre-programmed with expectations about how it should be called | if those expectations aren't met |

The important distinction: **state verification** (stubs/fakes — check the *result*) vs.
**behavior verification** (mocks — check specific *calls* were made). Behavior verification is
powerful but risky — it couples the test to *how* the code does something, not just *what* it
produces. Overusing mocks is one of the fastest ways to get brittle tests that break on every
refactor even when behavior hasn't changed.

## Two schools of thought

- **Classicist / "Detroit"** (Kent Beck) — prefer real objects wherever practical; use test doubles
  sparingly, mainly for genuinely external things (a mail server, a payment gateway). Tests verify
  state/output. Survives refactoring well — not tied to internal collaboration details.
- **Mockist / "London"** (Steve Freeman, Nat Pryce) — work outside-in from top-level behavior,
  using mocks to discover and design collaborator interfaces as you go. Tests verify interactions.

Neither is "correct" — a common pragmatic approach uses mockist thinking to *discover* boundaries,
then writes classicist, state-based tests for the settled core logic.

## The Test Pyramid

Mike Cohn's shape, later expanded by Martin Fowler, for a whole system's test suite:

```
        /\
       /  \      Few — End-to-end (slow, brittle, expensive, but catch real integration issues)
      /----\
     /      \    Some — Integration (check pieces work together)
    /--------\
   /          \  Many — Unit (fast, isolated, cheap to write and run)
  /------------\
```

Most tests should be fast, narrow, isolated unit tests; fewer mid-level integration tests; very
few full end-to-end tests, because those are slow and fragile and tend to fail for reasons
unrelated to what's actually being checked. The inverted "ice-cream cone" — too many slow
end-to-end tests, too few fast unit tests — makes a whole suite slow and unreliable.

## Best practices

- **Test behavior, not implementation.** Behavior stays stable over time; implementation details
  change constantly. Behavior-tests survive refactoring; implementation-tests break on every one.
- **One behavior per test** — makes failures immediately diagnostic.
- **Keep tests fast and independent** — no shared state, no dependence on execution order.
- **Only fake genuinely external dependencies.** Heavy mocking of your own internals is usually a
  design smell (too many responsibilities, too tight coupling).
- **Refactor test code too** — tests are code; let them rot and the safety net degrades.
- **Chase confidence, not a coverage percentage** — high coverage is a side effect of doing TDD
  well, not the goal to optimize for directly.

## Named anti-patterns

| Anti-pattern | What it is |
|---|---|
| **The Liar** | Passes but doesn't actually exercise the claimed behavior (common with async/timing issues) |
| **The Giant / excessive setup** | Huge Arrange blocks — usually means the code under test has too many responsibilities |
| **The Slow Poke** | Tests slow enough that people stop running them, quietly killing the practice |
| **The Nitpicker** | Asserts on an entire large output when only one small part matters — breaks on irrelevant changes |
| **The Secret Catcher** | No explicit assertion, relying only on "it didn't throw" |
| **The Inspector / over-mocking** | Verifies every internal call in detail — locks the test to today's implementation |
| **Skipping refactor** | Treating "tests pass" as the finish line; produces working-but-messy code |
| **Writing all tests up front** | Not TDD — TDD is one small failing test at a time, driving one small piece of code |

## When TDD fits, and when it doesn't

Tends to pay off most on: long-lived code that's maintained and changed repeatedly, complex
business/domain logic with real edge cases, code where a regression would be costly.

Tends to fit poorly on: throwaway prototypes and exploratory spikes where the design itself isn't
known yet, highly experimental work expected to be mostly discarded.

Best understood as a design and confidence tool, not a silver bullet applied uniformly to
everything — it trades a modest increase in initial effort for a substantial reduction in defects.

## Worked example (generic)

**Requirement:** apply a 10% discount once quantity reaches 100 units.

**RED:**
```
test "no discount below threshold":
    total = calculate_total(unit_price: 10, quantity: 50)
    assert total == 500
    // fails: calculate_total doesn't exist yet
```

**GREEN:**
```
function calculate_total(unit_price, quantity):
    return unit_price * quantity
```

Add a second test to force the discount logic:
```
test "discount applies at threshold":
    total = calculate_total(unit_price: 10, quantity: 100)
    assert total == 900
```
```
function calculate_total(unit_price, quantity):
    subtotal = unit_price * quantity
    if quantity >= 100:
        return subtotal * 0.9
    return subtotal
```

**REFACTOR** (still green after):
```
DISCOUNT_THRESHOLD = 100
DISCOUNT_RATE = 0.10

function calculate_total(unit_price, quantity):
    subtotal = unit_price * quantity
    if quantity >= DISCOUNT_THRESHOLD:
        return subtotal * (1 - DISCOUNT_RATE)
    return subtotal
```
