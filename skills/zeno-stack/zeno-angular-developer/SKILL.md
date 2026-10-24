---
name: zeno-angular-developer
description: >
  Angular code generation and architectural guidance — reactivity (signals, linkedSignal,
  resource), forms (signal/reactive/template-driven), dependency injection, routing, SSR,
  accessibility, animations, styling, testing, and CLI tooling. Use when creating Angular
  projects, components, or services, or deciding between Angular API options. Trigger on:
  "create an Angular component", "Angular service", "ng new", "Angular signals", "signal
  forms vs reactive forms", "Angular routing", "Angular dependency injection", "Angular SSR",
  "Angular animations", "Angular testing", "Angular CLI".
---

# Angular Developer

Guidance for generating Angular code and making the version-sensitive API choices Angular
presents at nearly every layer — reactivity, forms, DI, routing, styling, and testing.

**Split with `code-standards`** (mirrors the Postgres precedent): TS/code *style* for Angular code is owned by `code-standards/typescript-code-standards` (`frameworks/angular.md`) and wins on style questions; this leaf owns framework API selection, version features, and tooling.

## Before anything else

1. Determine the project's Angular version before recommending an API — best practice and
   feature availability shift meaningfully release to release. For a brand-new project, don't
   pin a version unless the user asked for one.
2. Generate code through the Angular CLI (`ng generate component/service/...`) rather than
   hand-rolling boilerplate, so naming and file structure stay consistent with the rest of the
   project.
3. After generating code, run `ng build` and fix any errors before considering the task done —
   this is not optional; it's the only cheap signal that the generated code is actually valid.

## Creating a new project

Absent other guidance, default to the latest stable Angular release, and prefer Signal Forms
for new projects only when the target version supports them.

Execution rule for `ng new`, in order:

1. **User named a version explicitly** (e.g. "Angular 15") -> bypass any local install, use
   `npx @angular/cli@<requested_version> new <project-name>`.
2. **No version requested, but `ng version` succeeds locally** -> use the local/global install:
   `ng new <project-name>`.
3. **No version requested and `ng version` fails** (no local Angular CLI) -> fall back to
   `npx @angular/cli@latest new <project-name>`.

## Components

Match the task to the right depth of guidance:

- **Fundamentals** — anatomy, metadata, template control flow (`@if`, `@for`, `@switch`).
- **Inputs** — signal-based inputs, transforms, model inputs.
- **Outputs** — signal-based outputs, custom event conventions.
- **Host elements** — host bindings, attribute injection.

When the built-in references don't cover the case, consult https://angular.dev/guide/components
directly rather than guessing at API shape.

## Reactivity

Angular's reactivity model centers on signals:

- **Signals** (`signal`, `computed`, `untracked`) for the core primitives and reactive
  contexts.
- **`linkedSignal`** for writable state that stays derived from — but overridable relative to
  — a source signal.
- **`resource`** for fetching async data directly into signal state.
- **`effect`** for logging or third-party DOM manipulation (`afterRenderEffect`); do not use
  `effect()` for derived state — that's what `computed()` is for.

## Forms

Prefer **signal forms** for new forms when the project's Angular version supports them. For
older applications or existing forms, match whatever strategy the app already uses rather than
mixing paradigms mid-codebase.

- **Signal forms** — signal-driven form state for new projects.
- **Template-driven forms** — simple forms with minimal logic.
- **Reactive forms** — complex forms needing programmatic control.

Signal form pitfalls: never initialize a field with `null`/`undefined` — use `''`, `0`, or
`[]`; access state flags by calling the field first (`form.field().valid()`, not
`form.field.valid()`); don't set `min`/`max`/`value`/`disabled`/`readonly` as raw HTML
attributes on a `[formField]` input — express them as schema rules instead.

## Dependency injection

- **Fundamentals** — the DI model, services, the `inject()` function.
- **Services** — `providedIn: 'root'`, and injecting into components or other services.
- **Providers** — automatic vs. manual provision, `InjectionToken`, `useClass`, `useValue`,
  `useFactory`, and provider scopes.
- **Injection context** — where `inject()` is legal, and `runInInjectionContext` /
  `assertInInjectionContext` for the cases where it isn't naturally available. Calling
  `inject()` outside an injection context is a common and avoidable error.
- **Hierarchical injectors** — `EnvironmentInjector` vs. `ElementInjector`, resolution order,
  modifiers (`optional`, `skipSelf`), and `providers` vs. `viewProviders`.

## Angular Aria — accessible custom components

For headless, accessible implementations of Accordion, Listbox, Combobox, Menu, Tabs, Toolbar,
Tree, and Grid patterns, use Angular's Aria components rather than hand-rolling ARIA wiring —
they handle keyboard interaction and ARIA state management consistently across the pattern set.
For general WCAG criteria beyond Angular specifics, see `zeno-accessibility`.

## Routing

- **Defining routes** — static vs. dynamic segments, wildcards, redirects.
- **Loading strategy** — eager vs. lazy, and context-aware loading.
- **Outlets** — `<router-outlet>`, nested and named outlets.
- **Navigation** — declarative (`RouterLink`) vs. programmatic (`Router`).
- **Guards** — `CanActivate`, `CanMatch`, and related access-control hooks.
- **Resolvers** — pre-fetching data with `ResolveFn` before route activation.
- **Lifecycle** — the chronological order of navigation events, for debugging.
- **Rendering strategy** — CSR, SSG (prerendering), SSR with hydration.
- **Route animations** — the View Transitions API for route-change motion.

Consult https://angular.dev/guide/routing for anything not covered by the above.

## Styling and animations

- **Tailwind CSS** integration into an Angular project.
- **Angular Animations** — prefer native CSS for dynamic effects; fall back to the legacy DSL
  only where CSS can't express the transition.
- **Component styles** — encapsulation and style-scoping best practices.

## Testing

- **Fundamentals** — unit testing conventions, async patterns, `TestBed`.
- **Component harnesses** — the standard pattern for robust, implementation-detail-resistant
  component interaction in tests.
- **Router testing** — `RouterTestingHarness` for reliable navigation assertions.
- **E2E** — Cypress or Playwright conventions for full-flow tests.

## Tooling

- **Angular CLI** — project creation, code generation, serve, build.
- **Angular MCP server** — available tools, configuration, experimental features.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `null`/`undefined` as an initial signal form field value | `''`, `0`, or `[]` |
| `form.field.valid()` | `form.field().valid()` — call the field, then read the flag |
| Starting a new form with the reactive/template API when Signal Forms are available | Use Signal Forms for new forms on a supporting Angular version |
| `min`/`max`/`value`/`disabled`/`readonly` set as raw attributes on `[formField]` | Express them as schema rules |
| `inject()` called outside an injection context | Call within one, or wrap with `runInInjectionContext` |
| `effect()` used to derive state | `computed()` |
| `$parent.$index` in a nested `@for` | `let outerIdx = $index` in the outer loop — Angular has no `$parent` |
| Hand-rolling ARIA for Accordion/Listbox/Combobox/Menu/Tabs/Toolbar/Tree/Grid | Angular Aria's headless components |

## Pre-flight checklist — run before delivering any Angular code

- [ ] The project's actual Angular version was checked before recommending an API
- [ ] Code was generated via the Angular CLI, not hand-assembled from scratch
- [ ] `ng build` was run and passes cleanly
- [ ] Forms use the strategy the app already uses, or Signal Forms on a new form where supported
- [ ] `inject()` calls happen inside a valid injection context
- [ ] Custom interactive components use Angular Aria rather than ad hoc ARIA wiring
- [ ] Route guards/resolvers are in place for any route requiring access control or pre-fetched data
