# BDD & Gherkin — Concepts Reference

This is general, stack-agnostic theory. For the Python + FastAPI + Kafka-specific application of
these same ideas (EventStorming, pytest-bdd/behave, Kafka contract/event-driven testing), see
`code-standards/python/references/ddd-tdd-bdd-workflow.md`.

## What BDD is

Introduced by Dan North (~2003–2006) as a refinement of TDD. North noticed "test" caused
confusion — developers treated TDD as a testing chore, and business people were excluded from a
conversation conducted entirely in code. BDD reframes everything around **behavior**, in **plain
language**, so three perspectives can collaborate on the same artifact (the "Three Amigos"):

- **Business/Product** — knows *what* the system should do and *why*.
- **Development** — knows *how* it can be built.
- **Testing/QA** — knows *what could go wrong* and how to verify it.

**The single most important thing to understand about BDD:** it's a collaboration and
specification technique first, test automation second. Writing Gherkin without the three-way
conversation gets the overhead (verbose test code) without the benefit (shared understanding).

## BDD vs. TDD vs. ATDD

| | Focus | Audience | Level |
|---|---|---|---|
| **TDD** | Code design, correctness | Developers | Unit/class |
| **ATDD** | Agreeing on acceptance criteria | Business + Dev + QA | Feature/story |
| **BDD** | Shared understanding of behavior, as executable spec | Business + Dev + QA | Feature/story, wraps TDD |

Two nested loops: the **outer loop** (BDD/ATDD) starts from a business-facing scenario that fails
because the feature doesn't exist yet; the **inner loop** (TDD) writes unit tests and code to make
that scenario pass. The BDD scenario is the acceptance criterion; TDD is how you engineer your way
to satisfying it.

## The three phases

1. **Discovery** — a structured conversation (example mapping) exploring a feature through
   concrete examples, surfacing edge cases and open questions *before* committing to a design.
2. **Formulation** — examples are written down in Gherkin (Given/When/Then) so they're unambiguous
   and automatable.
3. **Automation** — Gherkin scenarios are wired to executable code (Cucumber, behave, pytest-bdd,
   SpecFlow/Reqnroll, …), becoming both living documentation and a regression suite.

A common failure mode is skipping straight to phase 3 — writing Gherkin as an afterthought to
describe tests already written. That's syntactically valid, practically useless BDD.

## The Gherkin language

A `.feature` file contains exactly one Feature, grouping related scenarios:

```gherkin
Feature: <short title>
  <optional free-text description>

  Background:
    <steps that run before every scenario in this feature>

  Rule: <one business rule, optional grouping>

    Scenario: <a specific example of the rule>
      Given <a starting context>
      When <an event or action occurs>
      Then <an expected, observable outcome>

    Scenario Outline: <a templated example>
      Given <a starting context with a <placeholder>>
      When <an action>
      Then <an outcome with a <placeholder>>

      Examples:
        | placeholder | ... |
        | value1      | ... |
```

### Keywords

- **`Feature`** — the umbrella, one per file. A capability, not an implementation.
- **`Rule`** (optional) — groups scenarios that illustrate one specific business rule.
- **`Scenario`** / **`Example`** — one concrete illustration of behavior. Short (~3-5 steps), tests
  one thing.
- **`Given`** — the starting context. Something already true when the scenario begins — describe
  *state*, not a UI interaction currently in progress.
- **`When`** — the single action/event under test. More than one `When` means the scenario is
  really describing two behaviors — split it.
- **`Then`** — the expected, **observable** result — something a user or external system could
  actually see (a value, a status, a message, an emitted event), not an internal implementation
  detail like a raw database row.
- **`And` / `But`** — continuations; inherit the meaning of the preceding keyword, exist for
  readability.
- **`Background`** — steps (almost always `Given`) that run before every scenario in the file or
  `Rule` block. Keep it short — a bloated Background hides context from the reader.
- **`Scenario Outline` + `Examples`** — a templated scenario run once per row of the `Examples`
  table. Avoids copy-pasting near-identical scenarios that only differ by input values.

### Secondary constructs

- **Doc Strings** (`"""`) — a multi-line text block attached to a single step.
- **Data Tables** (`| col1 | col2 |`) — tabular data attached to a single step (unlike `Examples`,
  which parameterizes the whole scenario).
- **Tags** (`@tagname`) — metadata for filtering which scenarios run (`@smoke`, `@slow`, `@wip`)
  and targeting setup/teardown hooks.

## Writing good scenarios

1. **Be declarative, not imperative.** Describe *what* happens, not *how* a user clicks through it.
   ```
   ❌ When I click "Login" and type "dave" in the username field and type "pass123" in the
      password field and click "Submit"
   ✅ When I log in as "dave"
   ```
   Declarative scenarios describe stable business rules; imperative ones describe UI mechanics
   that change constantly, so they break on every redesign even when behavior hasn't changed.
2. **One behavior per scenario.** `When... Then... When... Then...` in one scenario means split it.
3. **Avoid "and" inside a single step.** `Given I am logged in and have items in my cart` is really
   two Givens.
4. **Domain language, not implementation.** `Given the orders table has a row for customer 42`
   leaks schema into a business spec. Say `Given customer 42 has a pending order`.
5. **Keep scenarios independent** — no scenario depends on another having run first, or on leftover
   data from a previous run.
6. **Don't misuse `Scenario Outline` as a data dump.** If `Examples` is really just blasting a
   dozen unrelated input permutations through the same steps, that's a parameterized unit test
   wearing a Gherkin costume. Reserve it for cases where the examples themselves are meaningfully
   different illustrations of the same rule.
7. **Keep scenarios short.** An enormous feature file probably covers more than one feature.

## How the automation layer works (Cucumber and relatives)

Gherkin alone is just structured text. A BDD framework does two things: **parses** `.feature`
files, and **matches** each step's text against a library of **step definitions** — real code —
executing them in order.

Matching mechanisms:
- **Cucumber Expressions** (modern, readable): `{int}`, `{string}`, `{float}`, `{word}` placeholders
  mark where a value is extracted, e.g. `Given I have {int} books currently checked out`.
- **Regular expressions** (older, more powerful, less readable): capture groups extract values.

Consequences of this design:
- **Keywords are ignored for matching purposes** — only the text after the keyword matters. The
  same step text after `Given` or after `Then` is the same step definition, so word steps to read
  naturally regardless of which keyword precedes them.
- An unmatched step fails immediately, usually with a generated code snippet to start from.
- Two step definitions matching the same text is an error ("ambiguous step").

Project shape (consistent across languages/tools):

```
feature files/         → the specifications, in Gherkin, non-technical
step definitions/      → code that implements each Given/When/Then
hooks / support code/  → setup and teardown (e.g. reset the database before each scenario)
```

**Before/After hooks** run around each scenario (or tagged subsets), for setup/teardown. Tag
expressions (`@smoke and not @flaky`) target which scenarios run and which hooks apply.

## Applying BDD — step by step

1. **Pick a genuinely uncertain or high-value feature**, not a trivial one — BDD's value comes from
   surfacing ambiguity.
2. **Run a Discovery conversation (Example Mapping)** with the Three Amigos: Yellow (story), Blue
   (rules), Green (examples), Red (open questions).
3. **Formulate:** convert each Green card into a `Scenario`, grouped under `Rule` blocks matching
   the Blue cards. Resist writing implementation-flavored steps — write them the way a domain
   expert would say them out loud.
4. **Automate:** for each new step, run the suite (it reports the step undefined, often with a
   stub snippet), implement the step definition against the real system, implement just enough
   production code via TDD to pass, then refactor.
5. **Make assertions observable, not implementation-coupled** — check something the system exposes,
   not internal storage.
6. **Fold into the regular workflow** — feature files live in version control next to the code;
   run a fast tagged subset on every change, the full suite on a schedule/before release; treat an
   undefined, ambiguous, or red scenario as a build failure; prune stale scenarios as behavior
   legitimately changes.
7. **Review scenarios as living documentation periodically** — could someone unfamiliar with the
   code read this feature file and understand what the system does and why? If not, it's drifted
   toward implementation detail and needs a rewrite.

## Common pitfalls

1. **Treating BDD as "just Cucumber."** Skipping Discovery and writing Gherkin solo, after the
   fact, discards most of the actual benefit.
2. **Imperative, UI-glued scenarios** — the most common technical mistake.
3. **Implementation leaking into scenario language** — tables, endpoints, internal flags instead of
   domain concepts.
4. **`Scenario Outline` misused as a data dump** for exhaustive input-permutation testing.
5. **Scenario sprawl** — very long scenarios or dozens per feature file signal it covers more than
   one feature.
6. **No one outside engineering ever reads the scenarios** — a signal the "living documentation"
   benefit isn't materializing.
7. **Flaky, order-dependent scenarios** — usually shared mutable state across scenarios rather than
   fully independent setup per scenario.
