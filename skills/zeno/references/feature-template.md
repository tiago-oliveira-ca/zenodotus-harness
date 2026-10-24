# Feature: <slug>

**Parent epic:** EPIC-<slug> | none (ad hoc)
**Tier evidence:** <required — name the two or more independently-verifiable Stories that make
this Feature tier rather than a single Story with a Task list. If you can't name them, this
belongs on a Story card (zeno's sizing ladder, burden of proof).>
**Implements:** PRD-<NNN>   <!-- optional — only when a requirements doc chain exists; see documentation/references/lifecycle.md -->
**Goal:** <one sentence — the feature's success condition>
**Status:** backlog | development | testing | closed
<!-- DDD runs in Gate 1 (Scope); FDD, then every Story's ATDD/BDD/Task breakdown, run in Gate 2
     (Route) — see zeno/SKILL.md. Which stage is active is read off this card's own section
     content (empty Domain & Architecture section → DDD; that filled but Story list empty → FDD),
     not a separate field. -->
**Updated:** <YYYY-MM-DD>

## Scope
- **Problem:** <what's wrong / needed, at feature scope>
- **Approach:** <how we're solving it>
- **Done looks like:** <observable proof the feature is delivered>

## Domain & Architecture (DDD)
<!-- Skip this section entirely for small/ad-hoc work with no parent epic — there's nothing to
     hang domain notes on. Required whenever a Feature file exists. All five fields below are
     zeno-ddd's pre-flight checklist, verbatim — filled in before zeno-fdd writes a Story line. -->
- **Bounded context:** <what this feature owns, and its boundary with neighboring contexts>
- **Subdomain classification:** Core | Supporting | Generic
- **Entities vs. Value Objects:** <which domain nouns need persistent identity vs. are fully defined by their attributes>
- **Aggregate(s) and root(s):** <where transactional consistency sits; cross-aggregate refs by ID only>
- **Context Map relationship:** <pattern to a neighboring context, if this one talks to another — omit if none>

## Story list (FDD)
<!-- Ordered, each step sized to one Story (one ATDD -> BDD pass, then broken into its own Task
     list for TDD) — written by FDD, then every Story on this list gets its own full ATDD/BDD/Task
     breakdown in Gate 2, before Gate 3 opens (zeno/SKILL.md's Gate 2 step 6). "verified by" is a
     feasibility hint, not a final spec — zeno-atdd turns it into real Acceptance Criteria. -->
- [ ] STORY-<slug> — <one-line goal> — file(s): <path> — verified by: <how, roughly> → `../stories/STORY-<slug>.md`
- [ ] STORY-<slug> — <one-line goal> — file(s): <path> — verified by: <how, roughly> → `../stories/STORY-<slug>.md`
<!-- [ ] not started · [~] in progress · [x] done — WIP limit: 1 [~] at a time -->
<!-- These markers track Gate 3 implementation progress, not Gate 2 planning progress — every
     Story above is already fully planned by the time Gate 3 starts implementing any of them. -->

## Decisions
- <YYYY-MM-DD> <decision + one-line why>   (append-only; newest last)

## Outcome
<!-- Optional — written when Status flips to closed. -->
<what shipped, and any follow-ups left open>
