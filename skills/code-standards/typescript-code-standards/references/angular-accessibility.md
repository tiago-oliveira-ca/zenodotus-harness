# Accessibility, Design Tokens, Signal Forms UX & Performance

## Contents
1. [API status snapshot — verify before relying](#1-api-status-snapshot--verify-before-relying)
2. [WCAG 2.2 AA + legal context](#2-wcag-22-aa--legal-context)
3. [Angular Material 3 theming](#3-angular-material-3-theming)
4. [Angular CDK — headless behavior](#4-angular-cdk--headless-behavior)
5. [Signal Forms: API and validation UX](#5-signal-forms-api-and-validation-ux)
6. [Storybook](#6-storybook)
7. [Performance as UX / Core Web Vitals](#7-performance-as-ux--core-web-vitals)
8. [Data-dense enterprise UI patterns](#8-data-dense-enterprise-ui-patterns)
9. [Component library decision table](#9-component-library-decision-table)

---

## 1. API status snapshot — verify before relying

- **Stable:** Signal Forms, Resource API (`resource`/`rxResource`/`httpResource`), zoneless
  change detection, `linkedSignal`, incremental hydration, OnPush-by-default, `FetchBackend`
  as the default HTTP backend, Vitest as the default test runner.
- **Developer preview, not stable — don't assert otherwise:** router view transitions
  (`withViewTransitions`, dev preview since v19); **Angular Aria** (`@angular/aria`) — the
  official roadmap lists it as dev preview with promotion to stable still "planned," which
  conflicts with some third-party blogs claiming it's production-ready. Flag that conflict to
  the user rather than silently picking a side.
- **Experimental:** the `debounced()` signal utility; WebMCP APIs
  (`declareExperimentalWebMcpTool`, `provideExperimentalWebMcpForms`, behind a Chrome flag).
- **Unconfirmed against official docs:** "selectorless components" — widely discussed in
  community coverage, sometimes listed as shipped by vendor blogs, but not confirmed against
  angular.dev. Verify before using the syntax in an example.

## 2. WCAG 2.2 AA + legal context

WCAG 2.2 (W3C Recommendation) adds criteria on top of 2.0/2.1. The ones that most often bite
enterprise/data-dense apps at **Level AA**:

- **2.4.11 Focus Not Obscured (Minimum)** — a focused element must not be entirely hidden by
  sticky headers/footers.
- **2.4.7 Focus Visible (AA, from 2.1)** — note that **2.4.13 Focus Appearance is AAA, not
  AA** — a common mislabeling in secondary sources; double-check criterion levels against the
  W3C "What's New in WCAG 2.2" page before asserting one.
- **2.5.7 Dragging Movements (AA)** — every drag interaction needs a single-pointer
  alternative (buttons for reorder, prev/next for carousels). Directly relevant to any CDK
  drag-drop usage.
- **2.5.8 Target Size (Minimum) (AA)** — interactive targets ≥ 24×24 CSS px (or adequate
  spacing). Affects dense tables/toolbars specifically.
- **3.2.6 Consistent Help (A), 3.3.7 Redundant Entry (A), 3.3.8 Accessible Authentication
  (Minimum) (AA)** — don't re-ask for data already provided; allow paste in OTP/password
  fields; no cognitive puzzles for authentication.

Automated tools (axe-core and similar) catch a meaningful share of issues by volume but a
minority of the actual WCAG success criteria — treat automated scanning as a first pass, not
a substitute for manual keyboard + screen-reader testing (NVDA/JAWS/VoiceOver) against the
ARIA Authoring Practices Guide patterns.

**Legal baseline, build to the superset:** the EU Accessibility Act (EAA) has been enforceable
since June 28, 2025 (technical basis references WCAG 2.1 AA via EN 301 549, with a 2.2-aligned
revision expected); Ontario's AODA mandates WCAG 2.0 AA; the federal Accessible Canada Act
references WCAG 2.1 AA for federally regulated sectors. **Building to WCAG 2.2 AA satisfies
all three simultaneously** since it's a superset — that's the practical reason to target 2.2
rather than the minimum any single regulation requires.

## 3. Angular Material 3 theming

Material 3 (M3) is fully token-based — theming emits CSS custom properties. **System tokens**
are prefixed `--mat-sys-*` (e.g. `--mat-sys-primary`, `--mat-sys-on-primary`,
`--mat-sys-surface`, `--mat-sys-error`) in a reference → system → component token hierarchy.

**Upgrade-safe rules:**
1. Define the theme with the `mat.theme()` mixin (colors, typography, density).
2. Consume `--mat-sys-*` tokens in your own components — always pair `X` with `on-X` for
   contrast.
3. **Treat `--mat-*` as read-only in raw CSS.** To change values Material consumes, use the
   **Overrides API** (`mat.<component>-overrides(...)`, `mat.theme-overrides(...)`) — it
   validates token names and survives version upgrades. This is the *only* supported
   customization surface.
4. **Never target Material's internal CSS classes.** Angular explicitly does not support
   overriding component CSS outside the theming APIs — it will break on the next version
   bump.
5. **`use-system-variables: true`** lets the theming API consume externally-provided CSS
   variables (from a design-token pipeline) instead of hardcoded values — this is the bridge
   between an existing design system and Material.

**If the design system diverges significantly from Material Design, don't fight Material with
CSS overrides** — pick a headless foundation (CDK + Angular Aria, once it stabilizes, or a
headless library) instead. Material is the right base only when broadly Material-aligned.

## 4. Angular CDK — headless behavior

CDK gives behavioral primitives with no visual opinion — the right foundation when the team
owns its own design system:

- **Overlay** — positioned floating panels (menus, tooltips, dialogs, autocomplete) with
  scroll/viewport handling.
- **a11y module** — `cdkTrapFocus` (focus trap for modals), `LiveAnnouncer` (aria-live
  announcements), `FocusMonitor`, `ListKeyManager` (roving keyboard nav for menu/listbox
  patterns).
- **`cdk-virtual-scroll-viewport`** — renders only visible items for large datasets. Fixed-size
  strategy is most performant; an autosize strategy remains experimental — verify before
  relying on it in production.
- **Drag-drop** — supports mixed-orientation (2D). ⚠️ **Known caveat:** combining CDK drag-drop
  with virtual scroll produces index-misalignment/layout bugs (multiple long-standing upstream
  issues) — if both are needed, budget for workarounds and test heavily, or avoid combining
  them.
- **`BreakpointObserver`** — responsive logic in TypeScript; wrap in `toSignal()` for a
  signal-friendly responsive state.

## 5. Signal Forms: API and validation UX

Signal Forms (`@angular/forms/signals`) is stable and the recommended path for new
signal-first forms; it interoperates with Reactive Forms for incremental migration.

```ts
import { Component, signal } from '@angular/core';
import { email, form, FormField, required, submit } from '@angular/forms/signals';

loginModel = signal<LoginData>({ email: '', password: '' });
loginForm = form(this.loginModel, (schemaPath) => {
  required(schemaPath.email, { message: 'Email is required' });
  email(schemaPath.email, { message: 'Enter a valid email address' });
  required(schemaPath.password, { message: 'Password is required' });
});
```

- **`form(modelSignal, (schemaPath) => {...}, options?)`** creates a form from a `signal()`
  model. **`FormField`** directive binds a field to an input (`<input [formField]="loginForm.email" />`); `FormRoot` (`[formRoot]`) wires `<form>` submit + `novalidate`.
- **Built-in validators:** `required`, `email`, `min`, `max`, `minLength`, `maxLength`,
  `pattern`, `minDate`, `maxDate`.
- **Custom/cross-field validation:** `validate(path, ctx => {...})`, `validateTree()` for
  multi-field/subtree, `applyEach()` for arrays, `applyWhen()`/`applyWhenValue()` for
  conditional schemas, `schema()` for reusable schemas, `validateStandardSchema()` for
  Zod/Valibot, `validateAsync()`/`validateHttp()` for async validation.
- **Field state** (call the field as a function): `.value()`, `.errors()`, `.valid()`,
  `.invalid()`, `.pending()`, `.touched()`, `.dirty()`, `.disabled()`, `.hidden()`,
  `.readonly()`; plus `markAsTouched()`, `reset()`, `errorSummary()`, form-level
  `submitting()`.
- **`submit(form, { action })`** returns `Promise<boolean>` — `true` on success, `false` if
  validation fails or the action returns errors; marks fields touched, blocks the action if
  invalid, sets `submitting()` during the action.
- **When to stay on Reactive Forms:** existing apps, or where the more battle-tested ecosystem
  matters more than being on the newest API. State this as a deliberate choice, not a default.

**Validation UX pattern (framework-agnostic, WCAG-aligned) — apply regardless of which form
API is used:**
- Show errors after `touched()` + `invalid()`, not on every keystroke.
- Associate errors with inputs via `aria-describedby`; set `aria-invalid`; use an
  `aria-live="polite"` region for a dynamic error summary.
- On submit failure, move focus to the first invalid field and/or a summary.
- Respect **Redundant Entry (3.3.7)** — don't re-ask for data already provided — and
  **Accessible Authentication (3.3.8)** — allow paste in OTP/password fields, no cognitive
  puzzles.

## 6. Storybook

Storybook (current major line) is a full component-testing platform for Angular: interaction
tests (play functions), accessibility tests (`@storybook/addon-a11y`, grouped violations),
visual regression (Chromatic), and a Vitest-powered test runner (matching Angular's own
default). For Angular + Vite/Vitest, `@analogjs/storybook-angular` is a commonly used
integration supporting zoneless apps — verify current version/compatibility before adopting.

- Pair Storybook + Chromatic for component-level visual regression with Playwright
  `toHaveScreenshot()` for page-level visual regression — component-level alone misses
  integration/layout conflicts.
- Presentational (dumb) components with no injected dependencies are the sweet spot for
  Storybook stories — another reason to keep the smart/dumb split clean (see
  `angular-clean-architecture.md`).

## 7. Performance as UX / Core Web Vitals

- **Targets, measured at p75 of real users:** LCP < 2.5s, INP < 200ms, CLS < 0.1. INP is
  usually the hardest for data-dense apps (heavy main-thread JS work) — this is exactly where
  zoneless + OnPush + signals earns its keep.
- **Incremental hydration is on by default** with `provideClientHydration()` (opt out with
  `withNoIncrementalHydration()`); it auto-enables event replay. Driven by
  `@defer (hydrate on ...)` triggers.
- **Bundle budgets:** enforce in `angular.json`; use `@defer` + route lazy-loading; measure
  with source-map-explorer against a **production build** — dev servers eager-load `@defer`
  chunks for HMR, which will give a falsely pessimistic read if measured there.
- **Skeletons vs. spinners:** prefer skeleton screens that mirror the actual layout for loads
  over roughly 500ms; show no loader at all for operations under ~300ms to avoid flicker
  (`@loading (minimum ...)`, `@placeholder (minimum ...)`). The academic evidence for
  skeleton screens being faster-*feeling* is real but modest — don't quote a specific
  percentage improvement as settled fact, the source study itself found no statistically
  significant difference despite a directional preference. Always reserve space to protect
  CLS regardless of which loading indicator is used.

## 8. Data-dense enterprise UI patterns

- **Tables:** virtual scroll (CDK) for large sets; server-side pagination/sort/filter for very
  large sets; AG Grid when spreadsheet-grade performance is genuinely needed. Sticky headers
  need to respect Focus Not Obscured (2.4.11); column resize/reorder needs non-drag
  alternatives per 2.5.7.
- **Filtering:** debounce signal-based filter inputs (verify the exact signal-debounce API
  status before using it — it may still be experimental); reflect filters in the URL query
  params for shareable/restorable state.
- **Bulk actions:** persistent selection across pages, a clear "N selected" affordance,
  confirmation for destructive actions.
- **Optimistic UI:** update the signal store immediately, reconcile on server response, roll
  back on error — a natural fit for a signal store's `patchState`.
- **Empty & error states:** design first-run empty, no-results-after-filter,
  permission-denied, and load-error-with-retry explicitly. `@error` blocks and a resource's
  `.error()` make these first-class rather than an afterthought.

## 9. Component library decision table

| Option | Best fit | Watch-outs |
|---|---|---|
| CDK + Angular Material 3 | Broadly Material-aligned design, official support, zoneless-ready | Rigid to restyle heavily beyond the Overrides API |
| CDK alone (headless) + custom design system | Design system diverges from Material | More initial build effort; pair with Angular Aria once it's stable, not before |
| PrimeNG | Fast CRUD/dashboard delivery, large free component set | Visual consistency/polish can drift at scale |
| Kendo UI (commercial) | Support-driven/compliance-heavy orgs, specialized components (scheduler, spreadsheet) | Licensing cost |
| Taiga UI | Greenfield, signals-friendly, modular/headless-leaning | Smaller community, thinner docs — verify maturity |
| Spartan/ng (shadcn-style headless + Tailwind) | Teams wanting full design-system ownership | Verify current maturity/version support before betting on it |
| AG Grid | Genuinely high-performance data grid needs beyond what Material/PrimeNG tables handle | Overkill for simple tables |

**Anti-patterns:** don't choose a library by GitHub star count; don't mix multiple component
libraries in one app — their CSS/token systems will clash.
