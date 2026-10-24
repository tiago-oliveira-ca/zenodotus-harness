---
name: zeno-frontend-design
description: >
  Operational design rules for web UI that reads as deliberately designed — typography scales
  and pairing tables, OKLCH palette construction, spacing/density systems, motion tokens, dark
  mode derivation, and an AI-slop detection table — applied the same way in React, Angular, Vue,
  Svelte, or plain HTML/CSS. Load before styling anything user-facing. Trigger on: "design a
  UI", "build a landing page", "style this component", "improve how this looks", "polish this
  page", "dashboard layout", "dark mode", "design tokens", "typography scale", "this looks
  generic", or any front-end task where a visual decision gets made.
---

# Frontend Design

UI work here means two inseparable deliverables: code that actually runs, and a visual
identity that belongs to this product specifically — not to whatever product the same
patterns would produce anywhere else. Every rule below is operational — numbers, ratios,
and decision tables, not adjectives.

**Design-token arbitration**: visual *direction* is owned here; token *architecture* by `zeno-stack/zeno-design-system`; handoff *packaging* by `documentation/developer-handoff-standards`; Angular SCSS token values by `code-standards/typescript-code-standards/ui-style` (CLAUDE.md lane row).

## Design workflow

Work out the direction before touching code:

1. Pin the subject: who uses this screen, for what job, and what feeling it should leave
   behind.
2. Derive the **signature element** — the single thing this page will be remembered by, drawn
   from the most characteristic thing in the subject's world: one type treatment, one layout
   move, one motion moment, or one image treatment.
3. **Spend boldness in exactly one place.** The signature element gets the risk; everything
   around it stays quiet and disciplined. Before shipping, remove one decoration.
4. Define 2-3 distinctive visual rules (a rule-line style, a numbering treatment, a hue) and
   repeat them consistently — identity comes from a signature *system*, not one-off flourishes.
5. Keep ambition inside the execution budget — a modest concept delivered precisely
   outperforms a grand one delivered half-done.

Structure must encode truth: numbered sequences, eyebrows, and dividers only when the content
actually is a sequence or category — decorative structure is an AI tell.

## Typography

**Pairing decision table:**

| Situation | Rule |
|---|---|
| Safest pairing | A superfamily (shared metrics/x-height): Source Serif+Sans, IBM Plex Serif+Sans |
| Serif display + sans body (or inverse) | Only if x-heights match closely — compare lowercase "x" at the same size; mismatch reads as different visual weights |
| Two fonts of the same classification | Never — too similar to contrast, too different to match. Contrast must be structural (serif vs sans, weight, width) |
| Family count | Max 2 for product UI; 3 only for a genuine utility face (captions/data/mono). Fixed roles: one voice (display), one workhorse (body) |
| Single-family strategy | One variable font differentiated by weight/width/optical-size axes is a legitimate pairing substitute — often the most coherent option |

**Scale:** generate sizes from a ratio, never ad hoc. Base = body size (16–18px). Ratio by
context: **1.125–1.2** data-dense apps and mobile · **1.25** general product UI (default) ·
**1.333** editorial/content · **1.414–1.618** marketing heroes only. Use a fluid `clamp()`
scale (Utopia-style) for content/marketing sites; fixed steps are fine for dense app UI.

**Thresholds:** measure 45–75 characters per line, ideal ≈66 — enforce with
`max-width: 60-75ch` on prose. Body 16px minimum (never 14px for long-form), line-height
1.4–1.6 (1.5 default). Headings: line-height 1.1–1.25 — bigger type, tighter leading.
Tracking: headings ≥32px get −0.01 to −0.02em; ALL-CAPS labels get +0.05 to +0.1em; never
negative-track body text. Users must be able to override to line-height 1.5 / letter-spacing
0.12em without breakage (WCAG 1.4.12).

**System stacks are right** for internal tools and admin dashboards (native feel, 0ms load);
**wrong** when brand identity is the point — then a web font is a requirement: WOFF2 only,
subset, preload the 1-2 critical files, `font-display: swap`, prefer one variable font over
3+ static weights, and set `font-optical-sizing: auto`. The tell isn't Inter itself — it's
Inter *unchosen*. If it's right for the job, choose it on purpose and pair it with a display
face that carries the voice.

## Color

**Construction:** build in **OKLCH** (equal lightness steps look equal in every hue — HSL
does not). Per-hue ramp: hold hue, step lightness across ~11 stops (0.97 → 0.13), chroma on a
bell curve peaking at the 500–600 midtones and reduced at both ends. Stop roles: 50–100
backgrounds · 400–600 primary actions · 700–950 emphasis, text, dark-mode surfaces. Tint
neutrals with 2-5% of the brand hue instead of pure gray. One accent hue + one semantic
status set beats a rainbow.

**Proportion (60-30-10):** ~60% dominant neutral, ~30% secondary surfaces/structure, ~10%
accent. If the accent is everywhere, it is not an accent.

**Tokens:** expose the palette as CSS variables in two tiers — primitives (`--blue-600`) and
semantic roles (`--surface-default/-muted/-elevated`, `--text-primary/-muted`,
`--border-default/-strong`, `--accent`, status roles). Components reference roles, never
primitives. Full token architecture: `zeno-design-system`.

**Contrast:** WCAG 2 floors for compliance — **4.5:1** body text, **3:1** large text (≥24px
or ≥18.66px bold) and non-text UI/focus indicators. Tune with **APCA** for perceptual truth:
Lc 75+ body, Lc 60 minimum content text, Lc 45 headlines/large, Lc 30 absolute floor for
placeholders/disabled. The two standards only agree on light backgrounds — **in dark mode
WCAG 2 math cannot be trusted; APCA-check every pair.**

**Dark mode is derived, never inverted:** base background L ≈ 8–12% (never pure `#000`);
elevation = lightness, each layer up +4–8% L, minimum four surface levels (base → card →
nested/hover → overlay); desaturate accents (blues −20–30%, reds −10–15%, greens reduced and
shifted 3–5° toward teal); primary text ~90% white, never `#fff`; fully saturated color on
dark surfaces vibrates — forbidden.

## Layout

**Spacing:** 8px base with a 4px sub-grid — scale `4, 8, 12, 16, 24, 32, 48, 64, 96`, exposed
as tokens; no arbitrary pixel values in component code. 4px steps *inside* small components,
8px multiples *between* components. **Internal ≤ external:** padding inside an element never
exceeds the margin separating it from siblings, or grouping reads wrong.

**Density decision table:**

| Context | Base rhythm | Table row height |
|---|---|---|
| Marketing / content / consumer | generous 8px multiples, 32–96 between sections | 48–52px |
| General SaaS product (default) | 8px + 4px sub-grid | 36–40px |
| Analyst / ops / trading tools | 4px-dominant | 28–32px |

Density matches the user's working mode, not a style preference — for data products ship it
as a toggle (comfortable default, compact option).

**Grid:** 12-column fluid scaffold; 3–5 breakpoints max, mobile-first `min-width`, standard
tiers 480/768/1024/1280 — break where the content breaks, not per device. Prefer container
queries for reusable components. Constrain prose to `ch`-based widths inside the grid. Design
desktop and mobile in the first pass, not as a retrofit.

**Optical alignment:** mathematical centering is the default; override when the shape is
asymmetric — play/arrow icons shift 1–2px opposite their visual weight, icons beside text
usually need a 1–2px downward nudge, pointed shapes need slight negative margin to look
flush. Button text often mis-centers from font metrics; fix with a 1px padding bias. If it
measures centered but looks off, the eye wins over the ruler.

## Motion

**Duration tokens** (Carbon-derived): 70ms micro-interactions (button, toggle) · 110ms small
fades · 150ms default transition · 240ms expansion, toasts · 400ms large expansion · 700ms
background dim, page transitions. Duration scales with distance and element size. Nothing
interactive above ~500ms; nothing user-triggered below ~70ms.

**Easing:** entrances decelerate (ease-out, e.g. `cubic-bezier(0, 0, 0.38, 0.9)`); exits
accelerate (ease-in, `cubic-bezier(0.2, 0, 1, 0.9)`) and run **faster** than entrances
(entrances 30–50% longer) — arriving elements deserve attention, dismissed ones shouldn't
block. Never `linear` for UI movement; never symmetric ease-in-out on an enter/exit pair.

**Productive vs expressive:** task-flow UI (forms, tables, navigation) gets the subtle
productive curves; brand moments (onboarding, empty states, hero) may use expressive ones.
One orchestrated moment beats scattered effects — extra animation *increases* the
AI-generated feel. Deeper motion patterns: `zeno-motion-ui`.

**Reduced motion:** any animation ≥200ms and any large-element scale/pan/parallax needs a
`prefers-reduced-motion` path. Reduce ≠ remove: keep opacity fades, drop scale/slide; stop
ambient loops entirely; honor the query in JS-driven animation too (`matchMedia`), not just
CSS.

## Adapting to the stack

The rules above hold regardless of framework; only the implementation mechanics shift:

| Stack | Styling & motion mechanics |
|---|---|
| React / Next.js | CSS Modules, a utility framework, or a CSS-in-JS library for scoping; Motion (formerly Framer Motion) for the duration/easing tokens above — see `zeno-motion-ui` |
| Angular | Component-scoped styles on standalone components; Angular's animation APIs for the same token values |
| Vue / Nuxt | `<style scoped>` in single-file components; native CSS transitions, or GSAP for orchestrated sequences |
| Svelte / SvelteKit | Component-local `<style>` blocks; the framework's built-in transition directives |
| Plain HTML/CSS | Custom properties for every token tier, modern layout primitives (Grid, cascade layers), no build step required |

**Respect what's already there before adding anything new.** A repo with an established
token set (Tailwind config, CSS custom properties, a shared component library) already encodes
prior design decisions — extend those tokens rather than laying a second, competing system on
top. Only originate a system from scratch when none exists (see `zeno-design-system`). On
Angular specifically, load `code-standards/typescript-code-standards` (`frameworks/angular.md`
for component architecture) alongside its `ui-style` sub-skill, which defines the default
Angular visual language, unless the project has already established a different one.

## Rules that hold regardless of stack

- Every deliverable must actually run — a static mockup that can't be dropped into the app is
  not a finished output.
- Extend the codebase's established visual system instead of introducing a parallel one.
- Accessibility floors are design constraints, not QA afterthoughts: contrast per the Color
  section, focus indicators at 3:1, reduced-motion paths (deeper: `zeno-accessibility`).
- **Theme-parallel edits** — light and dark token blocks typically reuse the exact same
  property names with different values, so a text replacement can match cleanly and still
  land in the wrong block. After any such edit, search for the changed property together
  with a few nearby lines, so the block boundary is visible and the right one can be
  confirmed, then render the page under both themes before calling the change finished.

## AI-slop tells — detect and fix

| Tell | Fix |
|---|---|
| Inter/system default with no decision made | Choose a face for a stated reason; pair a characterful display face with a workhorse body |
| Blue→purple / indigo gradient | Build the palette from something true about the product (OKLCH ramp + 60-30-10); if a gradient, not indigo→purple |
| Three rounded feature cards in a row, soft shadow, thin-line icon each | Asymmetry, a different rhythm, or content that refuses the triptych |
| "Build faster. Ship smarter." weightless copy | Copy that states what only this product does |
| Emoji as icons; ✨ everywhere | A real icon set, or none |
| Uniform border-radius + soft shadow on everything | Pick a radius stance (0, small, or large) and commit |
| Motion sprinkled on every element | One orchestrated moment |

Second-order warning: the *replacement* clichés are now also tells — warm-cream +
high-contrast serif + terracotta; near-black + acid-green; hairline-rule broadsheet with zero
radius. Avoid these three "tasteful default" looks too unless the brief justifies them.
Fixing even one main tell pulls a page noticeably out of slop; audit against all before
delivering.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| The same indigo-on-white look every generated page defaults to | One deliberate direction; palette built by the OKLCH ramp + 60-30-10 rules |
| Fonts chosen without reason, or >2 families | Pairing decision table; fixed display/body roles; superfamily when unsure |
| Ad hoc font sizes and spacing values | Ratio-generated type scale; 4/8px token scale, no arbitrary pixels |
| Dark mode by inverting the light palette | Derive it: L 8–12% base, +4–8% L per elevation, desaturated accents, APCA-checked |
| Contrast checked only against WCAG 2 in dark mode | APCA-check every dark-mode pair — WCAG 2 math fails on dark backgrounds |
| Every dashboard defaulting to the same evenly-spaced card grid | Density picked from the decision table; deliberate rhythm or asymmetry where it fits |
| Animation added because a page felt static, not because it says something | Duration/easing tokens, enter/exit asymmetry, one orchestrated moment |
| No reduced-motion path | Opacity-only fallback for ≥200ms animations; ambient loops stop |
| An ambitious concept executed half-done | Keep ambition inside the execution budget (workflow step 5) |
| A second, competing token system next to an existing one | Extend the repo's established tokens instead |

## Pre-flight checklist — run before delivering any UI design

- [ ] The design commits to one clear direction with a named signature element, and boldness is spent in exactly one place
- [ ] Type sizes come from a stated ratio; body text is ≥16px, 45–75ch measure, line-height 1.4–1.6
- [ ] Font pairing follows the decision table (superfamily / matched x-heights / structural contrast), max 2 families + optional utility face
- [ ] Palette is OKLCH-constructed, 60-30-10 proportioned, exposed as primitive + semantic tokens
- [ ] Contrast passes WCAG 2 floors everywhere and APCA in dark mode; focus indicators hit 3:1
- [ ] Dark mode (if present) is derived, not inverted: 8–12% L base, lightness elevation, desaturated accents
- [ ] Spacing uses the 4/8px token scale; internal padding ≤ external margins; density matches the context table
- [ ] Motion uses the duration/easing tokens with enter/exit asymmetry and a reduced-motion path
- [ ] The output runs and holds up across breakpoints, with desktop and mobile designed in the same pass
- [ ] The output was audited against the AI-slop tells table (including the second-order "tasteful default" looks)
- [ ] Existing product patterns are respected where they exist
- [ ] Any theme-parallel edit was verified against both the light and dark block, and rendered in both
