---
name: ui-style
description: >
  The Angular visual design system for this stack: macOS-inspired glassmorphism, `--mac-*`
  design tokens, canonical panel/list/form/badge component classes (catalog in
  references/scss-patterns.md), 8px-grid spacing utilities, fixed status colors, host-class
  rescope pattern for theming imported feature libraries, and theme-parallel edit verification.
  Use whenever writing or reviewing SCSS/styles in this Angular stack. Trigger on: "style this
  component", "SCSS", "design tokens", "glassmorphism", "panel styling", "dark mode styles",
  "theme this page", "--mac-", "restyle", "make it match the design system", or any Angular
  component styling task.
---

# Angular UI Design System

This is the default style reference for Angular projects in this environment. Before writing any
SCSS, read this document fully. All generated styles must conform to these patterns
unless the project already defines its own design system, in which case that
project's system takes precedence over this default.

> **Scope.** This skill owns Angular-specific styling (SCSS, Material theming, this design
> system). For general/cross-framework visual-design *direction* — aesthetic concept,
> typography, layout, non-Angular UI, or component-implementation concerns beyond SCSS/visual
> tokens — see `zeno-stack/zeno-frontend-design`, which defers Angular and SCSS specifics back
> here.

---

## Stack

- **Angular** + **Angular Material** (M3 token-based theming; aligns with the parent skill's Angular 22 target)
- **SCSS** per-component + two global files:
  - `src/styles.scss` — CSS tokens (`:root`), body background, Material overrides
  - `src/app/styles.scss` — Material theme, typography scale, utility classes
- Material palette: `$apple-blue` (primary `#007aff`, accent `#0071e3`)

---

## CSS Custom Properties (Design Tokens)

These are declared in `src/styles.scss` under `:root`. **Always prefer these tokens
in component SCSS rather than hardcoding values.** This is the single source of
truth for the visual language.

```scss
// Backgrounds
--mac-bg:            #e8edf8
--mac-bg-elev:       #f7f9ff
--mac-panel:         rgba(255, 255, 255, 0.7)
--mac-panel-strong:  rgba(255, 255, 255, 0.9)

// Borders & dividers
--mac-border:        rgba(60, 60, 67, 0.16)
--mac-divider:       rgba(60, 60, 67, 0.12)

// Text
--mac-text:          #1d1d1f
--mac-muted:         #6e6e73

// Brand blue
--mac-blue:          #0a84ff
--mac-blue-strong:   #0071e3

// Shadows (elevation scale)
--mac-shadow-xs:     0 1px 3px rgba(0, 0, 0, 0.08)
--mac-shadow-sm:     0 6px 18px rgba(14, 22, 40, 0.12)
--mac-shadow-md:     0 18px 44px rgba(14, 22, 40, 0.18)
--mac-shadow-lg:     0 28px 68px rgba(14, 22, 40, 0.24)

// Border radii
--mac-radius-xl:     22px   // login card
--mac-radius-lg:     16px   // panels, cards
--mac-radius-md:     12px   // menu panels, list rows
--mac-radius-sm:     10px   // buttons, inputs, form fields
```

---

## Typography

**Font stack** (apply to `font-family` on `body`):
```scss
-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
"Helvetica Neue", Arial, sans-serif
```

- `-webkit-font-smoothing: antialiased` on `body`
- Headings: `font-weight: 600`, `letter-spacing: -0.02em` (global) or `-0.01em` (component)
- Type scale: h1=2.5rem, h2=2rem, h3=1.5rem, h4=1.25rem, h5=1.125rem, h6=1rem

---

## Semantic Color Palette

Use these values only — never introduce new colors.

| Role | Value |
|---|---|
| Primary blue (iOS) | `#007aff` / `#0a84ff` |
| Strong blue (hover) | `#0071e3` / `#0066d6` |
| Dark text | `#1d1d1f` |
| Muted text | `#6e6e73` |
| Secondary text | `#515154` |
| Deep navy (data ink) | `#2e3961` / `#2a365e` / `#34426d` |
| Blue-gray (meta) | `#57658f` |
| Success | `#34c759` |
| Warning | `#ff9500` |
| Error | `#ff3b30` |
| Error dark | `#b42318` |
| Gray mid | `#8e8e93` |
| Gray light | `#d2d2d7` |
| Gray border | `#b0b0b5` |

---

## The Glassmorphism Visual Language

Every surface in this UI uses frosted glass. This is the defining visual pattern.
Apply it consistently to all panels, cards, dialogs, toolbars, and drawers.

```scss
// Canonical frosted-glass surface
background:      rgba(255, 255, 255, 0.6);   // 0.7 elevated, 0.84 login, 0.9 strong
border:          1px solid rgba(255, 255, 255, 0.55);
backdrop-filter: blur(16px) saturate(160%);  // toolbar/drawer: blur(18px), login: blur(24px) saturate(180%)
box-shadow:      var(--mac-shadow-sm);
border-radius:   var(--mac-radius-lg);       // 22px for login card only
```

> **Why this works**: The blurred backdrop makes surfaces feel like macOS panels
> floating above the ambient background image. The semi-transparent white tints
> maintain legibility while preserving the atmospheric depth.

---

## Component SCSS Patterns

The full canonical SCSS catalog lives in `references/scss-patterns.md` — load it before
styling any new component, and reuse its blocks verbatim rather than inventing variations.
It covers: Panel (primary glass card), List Row, Embedded Form, Inline Search Bar, Avatar,
Empty State, Status Badge, Alert Banner, Glass Container (generic utility), and Detail
Strip. The "Quick Reference: Which class to use" table below is the index into that
catalog.

---

## Material Angular Global Overrides

> **Relationship to the parent Angular standard (`../frameworks/angular.md`).** That standard forbids
> targeting internal `.mat-mdc-*` classes and `--mat-*`/`--mdc-*` tokens directly, mandating
> the Overrides API (`mat.<component>-overrides(...)`). That rule wins for anything the
> Overrides API can express — colors, shape/radius tokens, typography, density. The table
> below is a **deliberate, narrowly-scoped exception**: it covers heavy visual effects
> (glassmorphism `backdrop-filter`, multi-stop gradients, saturation blurs) that the token
> Overrides API cannot express. Apply this exception **only** in the two global stylesheets
> named below, never in component SCSS, and prefer the Overrides API first for any override
> that can be expressed as a token.

These live in `src/styles.scss` and `src/app/styles.scss`. **Do not redeclare them
in component SCSS** — they are already applied globally.

| Selector | Override |
|---|---|
| `.mat-mdc-card` | Glass panel, radius 16px, `var(--mac-shadow-sm)`, `backdrop-filter` |
| `.mat-toolbar` | `var(--mac-panel)` bg, `blur(18px) saturate(160%)`, `var(--mac-divider)` border-bottom |
| `.mat-drawer` | `var(--mac-panel)` bg, `blur(18px) saturate(160%)`, `var(--mac-divider)` border-right |
| `.mat-mdc-raised-button.mat-primary` | Gradient `#2e9cff → #0a84ff`, shadow `0 8px 20px rgba(10,132,255,0.3)` |
| `.mat-mdc-menu-panel` | Radius 12px, `var(--mac-shadow-md)`, `backdrop-filter` |
| `.mat-mdc-chip` | `border-radius: 999px`, `font-weight: 500` |
| `.mat-mdc-dialog-container` | `--mdc-dialog-container-shape: 18px` |
| `.mat-mdc-table .mat-mdc-row:hover` | `background: rgba(0, 122, 255, 0.05)` |
| All buttons | `border-radius: var(--mac-radius-sm)`, no `text-transform`, `font-weight: 600` |

---

## Animations & Transitions

```scss
// Entrance animation (cards, modals)
@keyframes slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

// Ambient decoration
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%       { transform: translateY(-16px) rotate(180deg); }
}
```

- **Row/chip interactions**: `0.15s ease`
- **Button/card hover**: `0.2s ease` or `0.2s cubic-bezier(0.4, 0, 0.2, 1)`
- **Card hover lift**: `0.3s cubic-bezier(0.4, 0, 0.2, 1)`
- **Hover lift amount**: `translateY(-1px)` (rows), `translateY(-2px)` (cards)

---

## Spacing — 8px Grid

Utility classes from `app/styles.scss`. Use these for quick margin/padding needs
rather than custom values.

`.mt-1`=8px `.mt-2`=16px `.mt-3`=24px `.mt-4`=32px
`.mb-1`=8px `.mb-2`=16px `.mb-3`=24px `.mb-4`=32px
`.p-1`=8px  `.p-2`=16px  `.p-3`=24px  `.p-4`=32px

---

## Scrollbar (macOS style)

Already global. Do not re-declare in components.

```scss
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: padding-box;
  &:hover { background: rgba(0, 0, 0, 0.3); background-clip: padding-box; }
}
```

---

## Rules to Follow When Generating SCSS

1. **Use tokens, not literals** — Reference `var(--mac-*)` in component files instead of repeating the raw values. This keeps the theme changeable from one place.

2. **Panel structure is canonical** — New glass cards use `.panel` + `.panel-header` + `.panel-title`. Don't invent a parallel pattern.

3. **All interactive surfaces get frosted glass** — `backdrop-filter: blur()` is non-negotiable on surfaces that float above content (panels, dialogs, drawers, login card).

4. **Shadows from the token scale** — Use `var(--mac-shadow-xs/sm/md/lg)` or the established inline values. Don't introduce new shadow values.

5. **Status colors are fixed** — Success=`#34c759`, Warning=`#ff9500`, Error=`#ff3b30`. No deviations.

6. **Buttons never shout** — `text-transform: none`, `font-weight: 600`, `border-radius: var(--mac-radius-sm)`. Primary buttons get the blue gradient from the global override — don't re-apply it locally.

7. **Deep navy for data ink** — Text inside data-dense tables and lists uses `#2e3961` / `#2a365e`, not `var(--mac-text)` which is reserved for headings and body copy.

8. **`::ng-deep` is acceptable only for Angular Material internals** where component ViewEncapsulation prevents direct targeting (e.g., `.mat-form-field-outline`, `.mat-checkbox-background`). Don't use it to pierce into sibling components.

9. **Error pages are intentionally plain** — `forbidden` and `not-found` use simple centered layouts without glassmorphism. This is by design — they should feel different from the app shell.

10. **Don't duplicate global overrides** — Material component overrides are already applied globally. Component SCSS should only style the component's own structural elements.

11. **Verify theme-parallel edits landed in the right block** — When editing a stylesheet that contains theme-parallel blocks (light/dark token blocks with the same property names but different values), a successful edit only proves the mechanical match was unique. After editing, re-grep the edited property names with surrounding context to confirm which block the change landed in, and verify rendering in ALL theme variants — not just the one being designed against.

12. **Theme imported feature libraries via a host-class rescope, not per-page rewrites** — When an imported library's templates carry a foreign design system's class vocabulary, theme it once at a scoped layout host: `ViewEncapsulation.None` plus a host class on the layout component, one stylesheet nested entirely under that class, and the library's legacy semantic tokens remapped onto this design system's tokens (never raw source values), with fallbacks mirroring the shell stylesheet. Reuse canonical shell classes rather than redefining them, and document deliberate mappings in a comment block (e.g. "palette has no red → danger maps to alert amber"). Don't rewrite the library's templates page by page, and don't let the foreign raw values survive.

---

## Quick Reference: Which class to use

| I need to style… | Class to use |
|---|---|
| A floating data section | `.panel` |
| A row in a list | `.list-row` (+ `.user-row` / `.org-row` grid column modifier) |
| An inline create form | `.embedded-form` + `.embedded-form-grid` |
| A search field | `.inline-search` |
| A user avatar | `.avatar` |
| An empty list placeholder | `.empty` |
| A status indicator | `.status-badge` + `.active/.inactive/.pending/.error` |
| An error/warning message | `.alert` + `.alert-danger` |
| Metadata label above a value | `.label` |
| A generic glass surface | `.glass-container` |
| Multiple info cards in a row | `.detail-strip` + `.detail-card` |

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Hardcoded colors/shadows/radii in component SCSS | `var(--mac-*)` tokens — the single source of truth |
| Inventing a parallel card/panel pattern | Canonical `.panel` + `.panel-header` + `.panel-title` |
| Floating surface without `backdrop-filter` | Frosted glass is non-negotiable on panels, dialogs, drawers |
| New shadow values | `var(--mac-shadow-xs/sm/md/lg)` or established inline values |
| New status colors | Fixed: success `#34c759`, warning `#ff9500`, error `#ff3b30` |
| `text-transform: uppercase` or re-applied gradients on buttons | Global button overrides; `font-weight: 600`, radius `var(--mac-radius-sm)` |
| `var(--mac-text)` for data-dense table/list text | Deep navy data ink `#2e3961` / `#2a365e` |
| `::ng-deep` to pierce sibling components | Only for Angular Material internals blocked by ViewEncapsulation |
| Glassmorphism on error pages | `forbidden`/`not-found` stay intentionally plain |
| Re-declaring Material overrides or scrollbar styles in components | They are global; style only the component's own elements |
| Custom margin/padding values for simple spacing | 8px-grid utilities (`.mt-*`, `.mb-*`, `.p-*`) |
| Rewriting an imported library's templates page-by-page to retheme it | Host-class rescope: `ViewEncapsulation.None` + host class, tokens remapped once at the layout host |

## Pre-flight checklist — run before delivering any Angular SCSS/styling

1. All colors, shadows, and radii reference `var(--mac-*)` tokens or the documented
   canonical values — no new literals introduced.
2. New surfaces reuse the canonical patterns (`.panel`, `.list-row`, `.embedded-form`,
   `.inline-search`, `.glass-container`, …) — no parallel pattern invented.
3. Every floating surface has the frosted-glass treatment (`backdrop-filter: blur()`).
4. Status colors and semantic palette values are unchanged from the fixed set.
5. Buttons: no `text-transform`, `font-weight: 600`, token radius; no locally
   re-applied primary gradient.
6. Data-dense text uses deep navy ink; `var(--mac-text)` reserved for headings/body.
7. No `::ng-deep` outside Angular Material internals; no duplicated global overrides
   or scrollbar declarations in component SCSS.
8. Spacing uses the 8px-grid utilities where applicable.
9. Theme-parallel edits verified: edited property names re-grepped with surrounding
   context to confirm the correct block, and rendering checked in ALL theme variants,
   not just the one being designed against.
10. If the project has its own established design system, it took precedence over this
    default — confirmed before applying any of the above.
