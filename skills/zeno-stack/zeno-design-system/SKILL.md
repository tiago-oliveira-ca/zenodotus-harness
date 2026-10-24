---
name: zeno-design-system
description: >
  Generate a design system from an existing codebase, audit an existing UI's visual
  consistency across 10 scored dimensions, or detect generic "AI slop" design patterns. Use
  when starting a project that needs a design system, auditing visual consistency before a
  redesign, reviewing a PR that touches styling, or when a UI "looks off" but the cause isn't
  obvious. Trigger on: "generate a design system", "audit our design consistency", "does this
  look AI-generated", "design system tokens", "visual consistency review", "why does this UI
  look off".
---

# Design System

Three modes for working with a product's visual language: generating a design system from
what already exists, scoring an existing UI's consistency, and flagging generic AI-slop
patterns before they ship.

**Design-token arbitration** (CLAUDE.md lane row): token *architecture* (tiers, DTCG, naming systems) is owned here; handoff *packaging* by `documentation/developer-handoff-standards`; visual *direction* by `zeno-stack/zeno-frontend-design`; Angular SCSS/`--mac-*` token values by `code-standards/typescript-code-standards/ui-style`.

## Mode 1: Generate a design system

Output: `DESIGN.md` + `design-tokens.json` (DTCG format) + `design-preview.html`
(self-contained, dependency-free).

### 1a. Inventory → cluster → normalize (from an existing codebase)

1. **Inventory** every literal from CSS, Tailwind config/classes, styled-components, and
   inline styles: colors, sizes, font-size/weight/line-height, radii, shadows, z-indexes,
   durations.
2. **Cluster near-duplicates** — 13 grays within a small ΔE of each other are 1 intended
   gray; `15px`/`16px`/`1rem` are one step. Frequency-rank the clusters; the top ones are the
   de-facto system.
3. **Normalize** clusters onto constructed scales; every unmatched outlier is either snapped
   to the nearest step or logged in `DESIGN.md` as a deliberate exception with rationale.
4. Re-express the result as primitives + semantic aliases derived from observed *usage
   roles* (what backgrounds/text/borders actually use which cluster).

From a brand seed instead (one or two brand colors, a font): build color ramps in **OKLCH**
(fix hue/chroma from the seed, step lightness evenly, chroma bell-curved and clamped where a
step exits sRGB, 10–12 steps per ramp, text steps anchored to contrast targets); type scale
base 16px × ratio 1.2–1.25 rounded to the 4px grid, 5–7 sizes; spacing on a 4px base
(`0,2,4,8,12,16,20,24,32,40,48,64`); radius 3–4 steps + `full`; 3–5 shadow levels as
composite tokens; 2–3 durations + 2–3 easings.

### 1b. Tier architecture (how the tokens are organized)

Build one-way dependency tiers: **primitive → semantic → component**. A tier only references
the tier below — never sideways, never upward. Primitives are named by what they *look like*
(`blue-500`, `space-400`); semantic tokens by what they're *for* (`color-bg-surface`,
`color-text-danger`) and their `$value` is always an alias, never a raw value. Components
consume semantic tokens only — that discipline is what makes retheming a remap instead of a
component rewrite.

| Situation | Tiers |
|---|---|
| Single product/brand (incl. light/dark) | 2 — primitive + semantic; theming remaps aliases |
| Multi-brand / white-label, or state matrices (`button-primary-bg-hover`) | 3 — add component tokens, sparingly and lazily |
| "Every component gets its own tokens" | Anti-pattern — component-token explosion; collapse to semantic roles |

Naming grammar (kebab-case in CSS, namespace-prefixed):
`[namespace]-[category]-[concept]-[property]-[variant]-[state]`, state always last. Scale
steps: numeric hundreds for primitives (`space-100` — insertable midpoints), t-shirt sizes
only for bounded semantic scales (type, radius).

### 1c. Emission

- **JSON in DTCG stable 2025.10**: `$value`/`$type`/`$description`, `$type` set once at group
  level, curly-brace aliases (`"$value": "{color.blue.500}"`), color as the object form
  (`colorSpace`/`components`/`hex`), dimension as `{"value": 16, "unit": "px"}`. Do not emit
  draft-only features (`$ref`, `$extends`, `$root`).
- **CSS custom properties** for the semantic (and component) tiers so theme/brand/density
  compose in the cascade; primitives that never theme may inline at build time. Theming
  selector pattern: `:root` = light, `@media (prefers-color-scheme: dark)` for the OS signal,
  plus `[data-theme="dark"|"light"]` attribute overrides that win in both directions.
- **Dark mode**: same semantic names, remapped to a dedicated dark ramp — never inverted
  primitives; re-check contrast per remap. `forced-colors: active` maps to CSS system colors;
  `prefers-contrast: more` gets its own semantic remap.

### 1d. Minimum viable token set (what ~80% of products need)

- [ ] Color primitives: 1 neutral ramp, 1 brand ramp, 4 status hues — 10–12 steps each
- [ ] Color semantic: `bg-{canvas,surface,surface-hover,surface-raised}`, `text-{primary,secondary,disabled,on-brand,link}`, `border-{default,strong,focus}`, `{accent,success,warning,danger,info}-{bg,text,border}`
- [ ] Spacing: ~10–12 primitive steps on a 4px base · Typography: 2 stacks, 5–7 sizes, 3–4 weights · Radius 3–4 + full · Shadows 3–5 · Breakpoints 3–5 · Z-index 5–6 named layers · Motion durations + easings
- [ ] Dark-mode remap of the **full** semantic color set, not a partial pass
- [ ] Focus-ring tokens (color + width + offset) — the most commonly forgotten set

### 1e. Governance (write into `DESIGN.md`)

Name a single decision-maker with authority to say no to new tokens. A new-token proposal
states its justification, expected usage (≥3 call sites or it's a one-off value), and which
existing token was considered and why it fails. Deprecate with `$deprecated` + replacement,
migrate, then remove — never delete live. Semantic-tier renames are breaking changes;
primitive value tweaks that keep contrast contracts are not.

## Mode 2: Visual audit

Score the UI across ten dimensions, 0-10 each. Every score needs a specific example and a fix
with an exact `file:line` — a bare number with no evidence is not an audit.

| # | Dimension | What "good" looks like |
|---|---|---|
| 1 | Color consistency | Uses the defined palette; no ad hoc hex values scattered through the codebase |
| 2 | Typography hierarchy | Clear, consistent h1 > h2 > h3 > body > caption progression |
| 3 | Spacing rhythm | A consistent scale (e.g. 4px/8px/16px steps), not arbitrary pixel values |
| 4 | Component consistency | Visually similar elements share the same styling patterns |
| 5 | Responsive behavior | Layout is fluid or gracefully adapts at breakpoints, not broken |
| 6 | Dark mode | Complete coverage, not a half-finished pass that misses some surfaces |
| 7 | Animation | Purposeful motion, not gratuitous decoration |
| 8 | Accessibility | Contrast ratios, focus states, and touch targets meet WCAG — see `zeno-accessibility` |
| 9 | Information density | Clean, not cluttered — appropriate whitespace for the content type |
| 10 | Polish | Hover states, transitions, loading states, and empty states all exist and feel intentional |

## Mode 3: AI slop detection

Generic AI-generated design tends to converge on the same tells. Flag these specifically
rather than vaguely calling something "generic":

- Gratuitous gradients applied to everything regardless of purpose
- Purple-to-blue as the default color choice with no rationale
- "Glass morphism" cards used decoratively, with no functional reason for the blur/transparency
- Rounded corners applied to elements that have no reason to be rounded
- Excessive scroll-triggered animation on every element
- A generic hero: centered text over a stock gradient background
- A sans-serif font stack with no distinguishing character

## Applying this in a PR review

When a PR touches styling, run the relevant audit dimensions against the diff specifically —
don't re-audit the whole app for a five-line change. Cross-reference `zeno-frontend-design` for
the aesthetic-direction reasoning behind a rejected pattern, and `zeno-motion-ui` for whether
flagged animation is purposeful or decorative.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| A dimension score with no example or fix location | Every score cites a specific `file:line` and a concrete fix |
| Re-auditing the whole app for a small styling PR | Score only the dimensions the diff actually touches |
| Calling something "generic" without naming the pattern | Name the specific AI-slop tell (gradient overuse, purple-to-blue default, unearned glassmorphism, etc.) |
| Generating tokens without scanning existing usage first | Inventory → cluster → normalize the codebase's implicit system before proposing new tokens |
| A design system with no rationale, just values | `DESIGN.md` explains why each token was chosen, not just what it is |
| Dark mode audited as pass/fail | Score coverage explicitly — "complete" vs. "half-done" is the actual failure mode |
| A semantic token holding a raw hex, or a component referencing a primitive | One-way tiers: component → semantic → primitive, aliases only above the primitive tier |
| A "semantic" tier that 1:1 mirrors the primitive tier | That's a rename, not semantics — semantic names describe purpose, and several may share one primitive |
| Dark mode generated by inverting light primitives | Dedicated dark ramp remapped through the same semantic names, contrast re-checked |
| Emitting draft-only DTCG features | Stable 2025.10 syntax only — no `$ref`, `$extends`, `$root` |

## Pre-flight checklist — run before delivering any design system output

- [ ] Existing codebase patterns were scanned before proposing new tokens
- [ ] Every audit score has a specific example and an exact fix location
- [ ] AI-slop findings name the specific pattern, not just "looks generic"
- [ ] Accessibility dimension cross-checked against `zeno-accessibility`, not eyeballed
- [ ] Dark mode scored for completeness, not just presence
- [ ] The preview/output artifact is self-contained with no external dependencies
- [ ] Generated tokens form one-way tiers (primitive → semantic → component), semantic values are aliases, components consume semantic only
- [ ] Emitted JSON is valid DTCG stable 2025.10; CSS custom properties cover the theming selector pattern (`:root` + media query + `data-theme` override)
- [ ] The minimum-viable-token-set checklist is satisfied or gaps are named, including focus-ring tokens and a full dark-mode semantic remap
