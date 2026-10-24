# Skill Authoring Template & Process

**This file is the single source of truth for how skills in `~/.claude/skills/` are
structured.** It is a reference/template, NOT a skill — it has no `SKILL.md`, is never
auto-loaded, and is exempt from the leaf-skill enforcement-shape rules below (a future
consistency audit should skip it). Copy the relevant skeleton, fill it in, then verify
against the pre-flight at the bottom.

Related: `~/.claude/skill-observations/cross-cutting-principles.md` (not beside this template)
holds the enforcement principle this template implements; `CLAUDE.md` points here from its
"Creating new skills" section.

---

## 1. Which shape? Dispatcher vs. leaf vs. spine

- **Dispatcher** — routes to nested sub-skills by technology/artifact type. Only
  `code-standards/`, `documentation/`, `testing/`, `zeno-workflow/`, `zeno-stack/`. A dispatcher
  holds routing + instructions and **no content, no enforcement sections**. (A nested dispatcher
  earns its keep only when it routes more than the parent can name directly.)
- **Leaf** — a self-contained content skill (standalone like `puml-diagrams/`, or nested like
  `code-standards/rust/`, `zeno-workflow/zeno-tdd/`, or `zeno-stack/zeno-redis-patterns/`).
  A leaf holds the actual standards **and both enforcement sections**.
- **Spine** — a leaf-with-routing that *both* carries content + both enforcement sections *and*
  routes to companion method skills. Only `zeno` (routes to `zeno-council` / `zeno-insight` / `zeno-workflow` /
  `zeno-debug` / `zeno-verify` — `zeno-workflow` is itself a dispatcher to its five nested pipeline
  stages). Treated as a leaf for enforcement-section purposes; the routing is a "method skills"
  section, not a dispatcher table. This shape is sanctioned so a consistency audit does not flag
  `zeno` as a malformed dispatcher.

A nested parent (e.g. `python/`) may be **hybrid**: content + a routing table
to its own children. Treat it as a leaf for enforcement-section purposes.

Nest a new technology/framework/artifact skill under the matching dispatcher (`code-standards` for
how code is written, `zeno-stack` for stack/domain coverage). Only create a new top-level skill
when the domain fits no dispatcher. Run `zeno-stack/zeno-find-skills` first to check overlap.

---

## 2. Frontmatter (every skill)

```yaml
---
name: <exact-directory-name>            # must match the folder
description: >
  <1-2 sentences on what the skill does and when to use it>. Trigger on: "<phrase>",
  "<phrase>", "<technology>", "<artifact type>", or <one catch-all clause>.
---
```

Rules:
- `name` matches the directory name exactly.
- `description` MUST contain an explicit **`Trigger on:`** list of quoted phrases —
  concrete technology names, artifact types, and things a user would actually say. This is
  what drives auto-matching.
- Keep the whole description **under ~1000 characters.** Past the harness display limit it is
  silently truncated mid-listing and the tail triggers never reach the matcher. Front-load the
  most distinctive triggers so any truncation costs the least.

---

## 3. Leaf skill body (in this order)

```markdown
# <Skill Title>

<Imperative-directive intro: "When writing/reviewing X, follow these standards.">
<Optional: one line of authoritative references. NO multi-line "sourced from vendor" apparatus.>

## <Content sections>
<The actual standards. Sections MAY be numbered (## 1., ## 2., …) or unnumbered — the skill's
choice, applied consistently within the file. Keep examples and anti-patterns; they are
load-bearing.>

## Anti-pattern quick reference
<A table distilled from the skill's own rules. Two-column `| Anti-pattern | Instead |` OR
three-column `| Anti-pattern | Problem | Fix |` — both allowed (principle #2).>

## Pre-flight checklist — run before delivering any <artifact>
<A checklist the agent runs against its own output before presenting it. MUST be the closing
section of the file.>
```

**Hard rules for the two enforcement sections:**
- Their headings are ALWAYS the exact, **unnumbered** strings `## Anti-pattern quick reference`
  and `## Pre-flight checklist — run before delivering any <artifact>` — even in a skill whose
  content sections are numbered. (Numbering these breaks greppability; if content sections
  cross-reference the anti-pattern section, refer to it by name, not by a section number.)
- The pre-flight checklist is the **last** section in the file. Nothing follows it — move repo
  layouts, reference-file lists, or closing prose above it.
- No marketing/summary paragraph after the checklist ("By applying these standards…").

**Hardening a discipline skill (optional, for process/method skills like the `zeno-*` family).**
Skills whose job is to hold the line under pressure (TDD, verification, debugging, the loop itself)
carry three extra elements, borrowed from the discipline-skill lineage:
- **One Iron Law** — a single uppercase, non-negotiable sentence near the top (e.g. "NO PRODUCTION
  CODE BEFORE A FAILING TEST"). One per skill; it is the thing the skill exists to enforce.
- **A rationalization table** — two columns, `| Excuse | Reality-check |`, listing the first-person
  excuses the agent is likely to invent to skip the discipline, each with its rebuttal.
- **A red-flags list** — first-person tells ("I'm reaching for the editor and can't state the
  cause") that mean you're about to bypass the skill, so you can self-interrupt.
These are for *behavioral* skills, not content/standards skills — don't bolt an Iron Law onto a
Python-standards leaf.

---

## 3b. Authoring rule — pressure-test a new skill before shipping it

A skill is only as good as its ability to fire under pressure. Before considering a new or
substantially-edited discipline skill done, **dogfood it against a subagent** (the skill is TDD'd,
not just written):
1. **RED** — give a subagent a realistic pressure scenario in the skill's domain *without* the
   skill, and record the rationalizations it invents to cut the corner.
2. **GREEN** — write (or revise) the skill so its rationalization table and rules counter exactly
   those observed excuses — not imagined ones.
3. **REFACTOR** — re-run under combined pressure (time, sunk cost, "just this once") until the
   subagent holds the line.
This is an authoring-time method, not runtime machinery — no hooks, no ledgers. Skip it only for
trivial content leaves; apply it to anything in the `zeno-*` discipline family.

---

## 4. Dispatcher body (in this order)

```markdown
# <X> Dispatcher

<One line: when a task of this family is requested, identify the type and load the sub-skill.>

## Routing Table
| Document/Task Type | When to Use | Sub-skill to load |
|---|---|---|
| ... | ... | `<name>/SKILL.md` |

## Instructions
1. Identify the primary type from the request or codebase.
2. Load and apply the matching sub-skill.
3. <Explicit which-wins precedence rules for overlaps — see §5.>
...
```

A dispatcher has **no** `## Anti-pattern quick reference` and **no** `## Pre-flight checklist`.

---

## 5. Interlock rules (how skills connect)

- **Dual registration.** Every sub-skill must appear BOTH in its parent dispatcher's routing
  table AND be matchable from the parent's frontmatter description (its trigger words present).
  For a nested child that is itself a full skill (e.g. `typescript-code-standards/ui-style`),
  register it in its **immediate** parent (`typescript-code-standards`), not only the top-level
  dispatcher. Framework-specific content that is a plain `frameworks/*.md` or `references/*.md`
  reference file (not its own skill — e.g. `python/frameworks/fastapi.md`,
  `database-data-modeling/oracle-plsql/frameworks/oracle-26ai.md`) doesn't need dual
  registration; it only needs a pointer from its parent SKILL.md's own routing/instructions.
- **Bidirectional boundary pointers.** Where two skills cover adjacent territory, BOTH state
  the which-wins/load-order relationship. Current adjacencies to keep in sync:
  `software-architecture` ↔ `software-architecture-progression` (code structure vs system
  topology); a language's own DDD reference (e.g. `python/references/ddd-clean-architecture.md`,
  `database-data-modeling/oracle-plsql/references/clean-architecture.md`,
  `typescript-code-standards/references/angular-clean-architecture.md`) ↔ the generic
  `software-architecture` (language/platform-specific guidance wins where it exists);
  `zeno-stack/zeno-frontend-design` ↔ `typescript-code-standards/ui-style`; the `documentation` →
  `code-standards` → `testing` → `github-circleci-standards` (CircleCI) / `zeno-stack/zeno-deployment-patterns` (GitHub Actions, strategy) lifecycle handoff.
- **Reference files.** Deep material lives in `references/*.md` beside the `SKILL.md` and is
  cited from the body (e.g. "see `references/lifecycle.md`"). Don't ship an empty `references/`.

---

## 6. No vendored skills — everything is zeno-owned

The library is single-source (Zenodotus): every skill, agent (24) and command (23) is original
zeno-owned content, and no vendored content of any kind remains in this repo (provenance and what
was rewritten: `CHANGELOG.md`). Agent shape rules live in `agents/_agent-template.md` (a separate,
agent-specific template; this file's rules are skills-only).
`graphify` remains a self-contained standalone skill and is not held to the enforcement-shape
rules. Plugins are the only remaining third-party
surface — do not normalize or hand-edit those; resolve trigger collisions via the precedence rule
in `CLAUDE.md`.

---

## 7. Pre-flight checklist — run before delivering a new or edited skill

- [ ] `name` matches the directory; `description` has a `Trigger on:` quoted list and is under ~1000 chars.
- [ ] Correct shape: leaf has BOTH enforcement sections; dispatcher has NEITHER.
- [ ] Anti-pattern heading is exactly `## Anti-pattern quick reference` (unnumbered).
- [ ] Pre-flight heading is exactly `## Pre-flight checklist — run before delivering any <artifact>` and is the LAST section.
- [ ] Intro is an imperative directive; no multi-line source-attribution apparatus; no closing marketing paragraph.
- [ ] Dual registration done (parent table + parent description) for any new sub-skill.
- [ ] Any adjacency has a which-wins pointer on BOTH sides.
- [ ] Embedded shell snippets are POSIX/BSD-portable (no `grep -oP \K`, no bare `sed -i`).
- [ ] Complies with every active principle in `~/.claude/skill-observations/cross-cutting-principles.md`.
