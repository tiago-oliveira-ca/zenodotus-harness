# ATDD & Business Acceptance Criteria — Concepts Reference

## What ATDD is

Acceptance Test-Driven Development: business, development, and testing representatives
collaborate to write acceptance tests *before* implementation begins, and those tests drive the
build. Grew out of Kent Beck's TDD (*Test-Driven Development: By Example*, 2002) but operates at
the acceptance/system level instead of the unit level, and adds explicit whole-team collaboration.
Its question is "are we building the *right* thing?" — TDD's question is "are we building the
thing *right*?"

## How ATDD, TDD, and BDD relate

| | Level | Primary question | Loop |
|---|---|---|---|
| **TDD** | Unit/class | Is the code correct? | Red → Green → Refactor, minutes-scale |
| **ATDD** | Acceptance/story | Are we building the right thing? | Discuss → Distill → Develop → Demo |
| **BDD** | Acceptance/story | Shared understanding of behavior | Discovery → Formulation → Automation |

They nest: acceptance tests (ATDD/BDD) are derived from Three-Amigos discussion at the start of a
story; TDD is the inner unit-level loop developers run while making those acceptance tests pass.
The terms overlap heavily in practice (Specification by Example is a near-synonymous sibling) — the
useful distinction to keep is **level** and **primary intent**, not a rigid boundary.

## Acceptance Criteria vs. Definition of Done

The most common point of confusion — keep these separate:

- **Acceptance Criteria** — *story-specific*. The conditions of satisfaction one particular Story
  must meet. Prove you built the *right feature*.
- **Definition of Done** — *common to every work item*. The team-wide quality/process checklist
  (tests written, reviewed, docs updated, integrated). Proves you built it to the *right quality*.

Both must be satisfied at acceptance. Don't fold DoD items into a Story's AC, and don't treat
passing AC as license to skip DoD.

## Who writes them — the Three Amigos

Three perspectives, not a headcount cap — UX, ops, or others can join:

- **Business/Product** — what problem are we solving?
- **Development** — how might we build it?
- **Testing/QA** — what could go wrong, how do we verify it?

Criteria written by one role alone reintroduce the communication gap ATDD exists to close. Keep
the conversation lightweight — a short session per story, not a heavyweight sign-off ceremony.

## Two formats for writing criteria

- **Scenario-oriented (Given/When/Then)** — best when concrete cases and edge cases matter, and
  when scenarios will later be automated. One scenario = one behavior.
- **Rule/checklist** — a bulleted list of invariants ("must always be true"). Best when the story
  is essentially a set of business rules, or scenarios would be repetitive.

In practice, combine both: rules state the invariant, examples/scenarios illustrate it with
concrete cases. Neither alone fully specifies behavior.

**The litmus test for any criterion:** *would this wording need to change if the implementation
changed?* If yes, it has implementation detail leaking in — rewrite it in domain terms.

```
❌ Vague / not testable:
The search should be fast and user-friendly.

✅ Specific / testable:
Given a product catalog, when a user searches by product name,
then matching results are returned showing name, image, and price,
within a defined response-time threshold.
```

## Example Mapping

The technique that unifies rules and examples, using four card types:

- **Yellow** — the story being discussed.
- **Blue** — the rules it must satisfy.
- **Green** — concrete examples illustrating each rule.
- **Red** — open questions that came up and couldn't be answered on the spot.

Timebox it — a well-understood, well-sized story maps in well under an hour. Too many red
(question) cards means the story isn't ready; too many blue (rule) cards means it should be split.
The output is a shared understanding, a set of examples, and a list of follow-ups — before any code
is written.

## The Discuss → Distill → Develop → Demo cycle

The most commonly cited ATDD workflow (not a rigid standard — teams adapt it):

1. **Discuss** — Three Amigos clarify the story using real examples; output is a shared
   understanding and acceptance tests in plain language.
2. **Distill** — plain-language examples are refined into a structured, tool-consumable format
   (e.g. Given/When/Then).
3. **Develop** — developers implement test-first, using TDD as the inner loop, until acceptance
   tests pass.
4. **Demo** — the completed feature is shown to stakeholders to confirm it matches what was
   discussed.

One artifact evolves through all four: a **story** becomes **examples** (Discuss), examples become
**tests** (Distill), tests become **working software** (Develop), working software demonstrates
**business value** (Demo). No phase happens in isolation by a single role.

## Common anti-patterns

| Anti-pattern | Why it defeats the point |
|---|---|
| Writing criteria/scenarios after the code | Tests then confirm what was built, not specify what should be — the "driven" part is gone |
| UI-coupled, imperative criteria | Brittle; breaks on cosmetic changes unrelated to behavior |
| Criteria written in isolation by one role | Reintroduces the communication gap ATDD exists to close |
| QA-only ownership of acceptance tests | Developers disengage; shared-understanding benefit evaporates |
| Testing multiple rules in one criterion/scenario | Reduces clarity, increases brittleness |
| Folding Definition-of-Done into story-specific AC | Conflates a team-wide bar with story-specific conditions |
| Moving forward with unresolved Example-Mapping questions | The story isn't actually ready — slice it or get answers first |

## Adopting it — the practical sequence

1. **Start with collaboration, not tooling.** Introduce the Three Amigos habit before introducing
   any automation framework.
2. **Run Example Mapping** on a small, near-term story first — story, rules, examples, questions.
3. **Write the criteria** — rule/checklist for invariants, Given/When/Then for illustrative cases;
   apply the litmus test.
4. **Automate deliberately, later.** ATDD can be practiced on paper first; automation (Cucumber,
   Reqnroll, behave, JBehave, FitNesse, Robot Framework, or whatever fits the stack) is a means, not
   the goal — reserve automated scenarios for behaviors stakeholders actually care about.
5. **Watch for the anti-patterns above in retros** — specifically after-the-fact writing, UI
   coupling, isolation, and QA-only ownership.

## Signals it's working

Fewer defects escaping to production; less rework from "that's not what I meant"; smoother demos
with few rejections at acceptance; stories arriving at planning with clear, agreed criteria;
stakeholders who can read (and help write) the criteria themselves.
