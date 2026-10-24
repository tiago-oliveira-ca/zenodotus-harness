---
name: zeno-ddd
description: >
  The DDD stage of zeno's Gate 1 (Scope), dispatched via the zeno-workflow dispatcher: once per
  Feature, name the Bounded Context, classify the subdomain (Core/Supporting/Generic), identify
  Entities/Value Objects and the Aggregate(s)/root(s) for this slice, and note the Context Map
  relationship to neighboring contexts if relevant — written onto the Feature card, before Gate 1
  closes. Gate 2's zeno-fdd runs next, once Gate 1 hands off. Trigger on: "domain model", "bounded
  context", "DDD", "define the domain", "what's the aggregate", "domain framing", "architecture
  for this feature", "subdomain".
---

# Zeno DDD — frame the domain and architecture before planning

This is the DDD stage of zeno's Gate 1 (Scope) — the fixed DDD → FDD → ATDD → BDD → TDD pipeline's
first stage, and the last thing that happens before Gate 1 closes on Feature-tier work. Its job:
give the Feature a named domain shape before Gate 2's `zeno-fdd` decomposes it into Stories — an
unframed Feature produces a Story list that's really just a task list with no underlying model.

**Iron Law: NO FEATURE PLANNING WITHOUT A FRAMED DOMAIN FIRST.** `zeno-fdd` does not start listing
Stories until this stage's five fields are filled in on the Feature card.

## The gate (do these in order)

0. **Read the council's output first.** `zeno-council` has already run at Scope; its card log carries
   the architecture direction, constraints and assumptions. Frame the domain inside them — do not
   re-open decisions the council recorded.
1. **Name the Bounded Context.** Either this Feature sits inside a Bounded Context already named
   at the Epic level, or — for a standalone Feature — name the boundary within which its model and
   vocabulary hold true.
2. **Classify the subdomain.** Core (the actual differentiator — invest deepest here), Supporting
   (necessary but not a differentiator — keep it simple), or Generic (a solved problem elsewhere —
   buy/integrate, wrap with an ACL rather than modeling it from scratch). This calibrates how much
   rigor the rest of this stage — and `zeno-fdd`'s Story list — actually deserves.
3. **Identify Entities vs. Value Objects.** For the concepts this Feature introduces or touches:
   which need a persistent identity across state changes (Entities), and which are fully defined
   by their attributes and should be immutable (Value Objects)?
4. **Identify the Aggregate(s) and root(s).** Where does transactional consistency actually need
   to sit? Reference other aggregates by ID only — never a direct object reference.
5. **Note the Context Map relationship, if relevant.** If this Feature's context talks to a
   neighboring one, name the pattern (Shared Kernel, Customer/Supplier, Conformist, Anti-Corruption
   Layer, Open Host Service, Partnership) rather than leaving the relationship implicit.
6. **Write it onto the Feature card's `## Domain & Architecture (DDD)` section.** All five fields:
   Bounded Context, subdomain classification, Entities vs. Value Objects, Aggregate(s)/root(s), and
   the Context Map relationship (or explicitly none). If the card still reads `Status: backlog`,
   flip it to `development` — this is the first pipeline stage touching it. Gate 1 closes here;
   `zeno-fdd` picks up next, in Gate 2.

For full definitions, patterns, and worked examples (Ubiquitous Language, the full Context Mapping
table, Building Blocks, Aggregate rules, Domain Events, Repositories, Domain Services, the
Anti-Corruption Layer, and the Common DDD Mistakes table), see
`code-standards/software-architecture/references/ddd.md` — this stage applies that skill's
definitions at Feature scope; it doesn't redefine them.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Listing Stories before the domain is framed | DDD always closes before `zeno-fdd` opens |
| Treating every subdomain with Core-level rigor | Classify first — Generic gets bought/wrapped, not modeled deeply |
| Forcing one shared model across bounded contexts | Each context gets its own model; translate via events/ACL |
| An Entity/Value-Object split made by guessing | Ask: does this need identity across state changes, or is it fully defined by its attributes? |
| A Feature card with Story list but no Domain & Architecture section | This stage's five fields exist before `zeno-fdd` writes a single Story line |
| Skipping the Context Map note when contexts do interact | Name the relationship pattern explicitly, don't leave it implicit |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "This Feature is small, DDD is overkill" | The subdomain classification step is exactly how you decide that — do it, then keep it light if it says to |
| "I'll figure out the aggregate boundary as I code" | Boundaries decided mid-Execution are usually wrong and expensive to unwind — decide first |
| "Everything in this domain is equally important" | It isn't — Core/Supporting/Generic exists because effort should scale with differentiation |

## Red flags — stop and frame the domain

- A Story list exists with no Domain & Architecture section above it on the Feature card.
- An Aggregate holds a direct object reference to another aggregate instead of an ID.
- A Generic Subdomain (auth, payments, email) is being modeled as deeply as the Core Domain.
- Two Bounded Contexts share one model with no translation layer between them.

## Pre-flight checklist — run before delivering any Domain & Architecture framing

- [ ] Bounded Context is named (or confirmed as the Epic-level one this Feature sits inside).
- [ ] Subdomain classified as Core / Supporting / Generic.
- [ ] Entities vs. Value Objects identified for this slice.
- [ ] Aggregate(s) and root(s) identified; cross-aggregate references are by ID only.
- [ ] Context Map relationship noted, if this Feature's context talks to a neighboring one.
- [ ] All five are written onto the Feature card's `## Domain & Architecture (DDD)` section.
