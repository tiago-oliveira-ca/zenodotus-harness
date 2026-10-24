# Angular Code Standards & Best Practices

> **Split with `zeno-stack/zeno-angular-developer`:** this file owns Angular TS style, patterns and templates; framework API selection, version features and CLI/build tooling are owned there (CLAUDE.md lane note).

When generating, reviewing, or refactoring Angular code, adhere strictly to the following
standards. They are aligned with the official Angular Style Guide and cover Angular 22 — the
"signal-first consolidation" release, where OnPush is the default change-detection strategy,
zoneless is the default posture for new projects, Signal Forms and the Resource API are
stable, and Vitest is the default test runner.

General TypeScript/JavaScript standards (strict mode, the `unknown`-not-`any` rule, type-system
idiom, generics, async/Promise correctness, modules, null handling, immutability, tsconfig
strict flags) are covered by the parent `../SKILL.md` (`typescript-code-standards`) — **read it
first.** This file only covers what is specific to Angular.

This file covers component architecture, not visual styling. Any task touching SCSS/CSS,
design tokens, or visual layout must also load `../ui-style/SKILL.md` — it defines the default
Angular UI design system and applies to Angular styling work regardless of project.

## Epistemic calibration — verify before asserting

Angular ships on a fast, opinionated cadence. Treat the following as genuinely different
tiers of confidence, and don't flatten them:

- **Stable, safe to assert directly:** standalone components, signals (`signal`, `computed`,
  `effect`, `linkedSignal`), zoneless change detection, OnPush as the default strategy,
  the Resource API (`resource`/`rxResource`/`httpResource`), Signal Forms
  (`@angular/forms/signals`), incremental hydration, Vitest as the default test runner,
  functional guards/resolvers/interceptors.
- **Developer preview / experimental — do not present as stable:** router view transitions
  (`withViewTransitions`, dev preview since v19), Angular Aria (`@angular/aria`, dev preview
  per the official roadmap — some third-party blogs claim "production-ready," which
  conflicts with the roadmap; flag this conflict rather than pick a side), the `debounced()`
  signal utility, WebMCP APIs (`declareExperimentalWebMcpTool`,
  `provideExperimentalWebMcpForms`), and any "selectorless components" claim (heavily
  discussed in community coverage but not confirmed against official docs).
- **Version-sensitive, check the installed patch:** exact API signatures for Signal Forms,
  `resource()`, and `@ngrx/signals` — these evolve across minor releases. Confirm against
  angular.dev / ngrx.io for the project's actual version before relying on exact syntax. The
  same applies to embedding React: whether the default esbuild builder cleanly compiles
  `.tsx` without extra configuration, and the exact `afterRenderEffect` phase semantics, are
  the least-settled parts of that story — verify against the CLI actually installed before
  asserting either as fixed.
- **Stable fact, safe to assert directly despite sounding surprising:** there is no
  maintained, version-current Angular↔React interop library. Every well-known name
  (`ngReact`, `react2angular`, `angular2react`, `@angular-react/core`) is years stale; the
  newest attempt (`@bubblydoo/angular-react`) is itself low-adoption and NgModule-era. Don't
  suggest installing a bridge library — the adapter is meant to be hand-written and small; see
  `../references/angular-react-interop.md`.
- **Version-sensitive, verify against the live package registry, not a docs page:** for
  whole-app Angular↔React coexistence (single-spa, Module/Native Federation, Angular Elements),
  package docs pages lag real releases — e.g. `single-spa-angular`'s own ecosystem page still
  lists Angular 16-18 support while npm has moved well past that. Confirm exact versions and
  peer ranges against the registry before quoting them. Also don't assume a project is on the
  classic webpack `@angular-architects/module-federation` just because "Module Federation" is
  the term used — Angular's CLI default moved to esbuild at v17, and `native-federation` is now
  the default recommendation for that builder; check `package.json` first. The same caution
  applies to `@r2wc/react-to-web-component` (the React→custom-element tool in §16): its own
  README currently scopes v2 to React 18 — verify React 19 compatibility against the repo, not
  by assumption, before adopting it on a React 19 codebase. See
  `../references/angular-react-coexistence.md`.

Load `../references/angular-clean-architecture.md` when a task involves layering an Angular
feature (ports, use-cases, DTOs/mappers, state-management tier selection, or boundary
enforcement), `../references/angular-accessibility.md` for anything touching accessibility,
Angular Material theming, Storybook, performance/Core Web Vitals, or Signal Forms validation
UX, `../references/angular-react-interop.md` before embedding any React component inside an
Angular host — load it before reaching for a third-party bridge library, since none is
currently trustworthy — and `../references/angular-react-coexistence.md` when Angular and React
must run as two independent apps (micro-frontends, incremental migration) rather than one
widget in one host.

---

## 1. Project Structure (LIFT Principle)

Organize code so you can **L**ocate it quickly, **I**dentify it at a glance, keep the **F**lattest structure possible, and **T**ry to stay DRY.

- **Feature-based Structure:** Organize by feature area, not by file type. Avoid global `components/`, `services/`, or `pipes/` folders — this is also the official Angular style guide's own position, not just a Clean Architecture preference.
- **One Thing Per File:** Define one component, service, pipe, or directive per file.
- **File Size Limits:** Aim for ≤ 400 lines per file and ≤ 75 lines per function to ensure readability.
- **Colocation:** Keep a component's template, styles, and spec file in the same directory as its TypeScript class.

```text
src/
  app/
    features/
      heroes/
        hero-list/
          hero-list.component.ts
          hero-list.component.html
          hero-list.component.scss
          hero-list.component.spec.ts
        hero-detail/
          ...
        hero.service.ts
        hero.model.ts
        heroes.routes.ts
    shared/
      components/
      pipes/
    core/
      interceptors/
      guards/
```

### Core vs. Shared

- **`core/`**: Code that is instantiated only once in the application lifecycle (e.g., `AuthService`, `JwtInterceptor`). Provide at the root via `providedIn: 'root'`. Do **not** import `core/` into feature modules — it should only be bootstrapped at the app level.
- **`shared/`**: Code that is reused across multiple features (e.g., `ButtonComponent`, `DateFormatPipe`). Import directly into standalone components as needed.

### Barrel Files

Use `index.ts` barrel files at the feature level to expose its public API, hiding internal implementation details:

```typescript
// features/heroes/index.ts — expose only what external consumers need
export { HeroListComponent } from './hero-list/hero-list.component';
export { HeroService } from './hero.service';
export type { Hero } from './hero.model';
```

---

## 2. Naming Conventions

| Entity              | Convention                                               | Example                            |
|---------------------|----------------------------------------------------------|------------------------------------|
| File names          | `feature.type.ts` in `kebab-case`                        | `hero-list.component.ts`           |
| Classes             | `UpperCamelCase` + type suffix                           | `HeroListComponent`, `HeroService` |
| Variables/Methods   | `lowerCamelCase`                                         | `heroList`, `getHeroById()`        |
| Constants           | `UPPER_SNAKE_CASE`                                       | `MAX_HEROES_PER_PAGE`              |
| Component Selectors | `kebab-case` with custom app prefix                      | `app-hero-list`                    |
| Signals             | Plain noun, no suffix                                    | `count`, `selectedHero`            |
| Observables         | Suffix with `$`                                          | `count$`, `heroes$`                |

These are Angular's framework-specific naming rules. General TypeScript naming conventions
(and the reasoning behind them) live in the parent `../SKILL.md`.

---

## 3. Standalone Components

Standalone components are the default and recommended approach; `bootstrapApplication` is
preferred over `bootstrapModule`.

- **Default to Standalone:** Generate all new components, directives, and pipes with `standalone: true` (implicit by default in current CLI versions — don't add the flag redundantly if the generator already omits it).
- **Explicit Imports:** Import only what is needed within each standalone component to minimize bundle size.
- **Lazy Load Standalone Components:** Use `loadComponent` in the router for direct lazy loading instead of `loadChildren` with a module.
- **NgModules are not deprecated** — only "not recommended for new code" per the official NgModules guide. Don't tell a team they're gone; migrate incrementally for existing NgModule-based apps.

```typescript
// ✅ Correct: Standalone component with explicit imports
@Component({
  selector: 'app-hero-list',
  imports: [RouterModule, HeroCardComponent],
  templateUrl: './hero-list.component.html',
})
export class HeroListComponent {}

// ✅ Correct: Lazy loading a standalone component in a route
{
  path: 'heroes',
  loadComponent: () =>
    import('./features/heroes/hero-list/hero-list.component').then(
      (m) => m.HeroListComponent
    ),
}
```

---

## 4. Signals, Zoneless & the Resource API

Angular Signals provide a fine-grained reactivity model. Zoneless change detection is the
default posture for new projects, and OnPush is now the default change-detection strategy
for components (the prior default was renamed `ChangeDetectionStrategy.Eager` — if you see
`Eager` markers in a migrated codebase, they're `ng update`'s way of preserving old behavior
on components that relied on always-check; treat them as a cleanup TODO list, not a
permanent fixture).

- **Use Signals for UI State:** Signals are ideal for synchronous, component-level state (UI flags, form values, local data lists).
- **Keep Signals Granular:** Break large state objects into smaller, more focused Signals rather than one monolithic signal.
- **Use `computed()` for Derived Values:** Never manually derive and update values; let `computed()` handle it. Keep `computed()` functions pure — no side effects, no async calls.
- **Use `linkedSignal()`** for writable derived state that should reset when a source changes (e.g., resetting a selected row when a filter changes) — this is a different job than `computed()` (read-only) or `effect()` (side effects only).
- **Use `effect()` sparingly and only for genuine side effects** (DOM APIs, logging, third-party integration). Don't use `effect()` to propagate state into other signals (use `computed`/`linkedSignal` instead) and don't use it for data fetching (use `resource`).
- **`resource()` / `rxResource()` / `httpResource()`** are stable and are the default way to fetch async data reactively — they expose `.value()`, `.isLoading()`, `.error()`, `.status()`, and re-fetch automatically when a signal read in the request changes. They are for **reads**; use `HttpClient` directly for POST/PUT/DELETE mutations.
- **Bridge with RxJS at boundaries:** Use `@angular/core/rxjs-interop` (`toSignal()`, `toObservable()`) for genuine event streams, complex time-based orchestration (debounce/switchMap/combineLatest), or WebSockets/SSE — not as the default for simple data fetching now that `httpResource` exists.
- **Normalize Collection State:** When managing collections of entities, store them as a `Map` or dictionary indexed by ID rather than plain arrays. This enables O(1) lookups and prevents inconsistencies when updating or deleting records.
- **Zoneless failure mode to watch for:** if you mutate a plain object/array in place (not through a signal write) or update state from a non-signal async source without a signal write, the UI silently will not update. Hold all template-relevant view state in signals and update immutably.

```typescript
// ✅ Correct Signal usage
@Component({ ... })
export class CounterComponent {
  count = signal(0);
  doubled = computed(() => this.count() * 2); // derived, auto-updates

  increment() {
    this.count.update((c) => c + 1);
  }
}

// ✅ httpResource for reactive reads
userId = input.required<string>();
user = httpResource<UserDto>(() => `/api/users/${this.userId()}`);

// ✅ Bridging a genuine event stream with toSignal()
readonly heroes = toSignal(this.heroService.getHeroes(), { initialValue: [] });
```

---

## 5. Modern Template Control Flow

Prefer the built-in control flow syntax over structural directives.

```html
<!-- ✅ Use @if instead of *ngIf -->
@if (isLoggedIn()) {
  <app-dashboard />
} @else {
  <app-login />
}

<!-- ✅ Use @for instead of *ngFor — track is REQUIRED -->
@for (hero of heroes(); track hero.id) {
  <app-hero-card [hero]="hero" />
} @empty {
  <p>No heroes found.</p>
}

<!-- ✅ Use @switch instead of [ngSwitch] -->
@switch (status()) {
  @case ('active') { <span class="active">Active</span> }
  @case ('inactive') { <span class="inactive">Inactive</span> }
  @default { <span>Unknown</span> }
}

<!-- ✅ Use @defer for declarative lazy loading of heavy UI blocks -->
@defer (on viewport) {
  <app-heavy-chart [data]="chartData()" />
} @loading (minimum 200ms) {
  <p>Loading chart...</p>
} @placeholder {
  <div class="chart-placeholder"></div>
}
```

- `*ngIf`/`*ngFor`/`*ngSwitch` are deprecated (since v20) with intent to remove in a future
  major release, but are still present and functional — don't tell a team they're gone yet,
  but do steer new code to `@if`/`@for`/`@switch`.
- Give `@placeholder`/`@loading` fixed dimensions to avoid layout shift (CLS), and don't defer
  above-the-fold content. See `../references/angular-accessibility.md` for the full `@defer` UX
  checklist (including the `aria-live` requirement for screen readers).

---

## 6. Component Design

- **Separation of Concerns:** Keep business logic in Services (or use-case services — see
  `../references/angular-clean-architecture.md`); keep templates for presentation only.
- **Smart vs. Dumb Components:**
  - **Container/Smart:** Manages data fetching, state, and orchestration. Injects a facade/store and reads signals. Passes data down via `input()`.
  - **Presentational/Dumb:** Displays data received via `input()`, emits events via `output()`. Injects nothing. OnPush is now the default for these anyway, but keep them signal-input-driven so that default actually pays off.
- **No Direct DOM Manipulation:** Never use `document.querySelector` or similar browser APIs in components. Use Angular's template binding, directives, or `Renderer2`.
- **Signal Forms for new forms; Reactive Forms remain valid** for existing apps or where you need the more battle-tested ecosystem — see `../references/angular-accessibility.md` for Signal Forms API and validation-UX patterns.
- **Use `inject()` for DI:** Prefer the `inject()` function over constructor injection, per the official style guide.

```typescript
// ✅ Modern injection with inject()
@Component({ ... })
export class HeroDetailComponent {
  private heroService = inject(HeroService);
  private route = inject(ActivatedRoute);
}
```

---

## 7. Performance Optimization

- **OnPush is now the default** change-detection strategy — you no longer need to set it
  explicitly on new components, but do audit migrated codebases for `ChangeDetectionStrategy.Eager` markers left by `ng update` and clean them up deliberately rather than leaving them as silent opt-outs.
- **Zoneless is the default posture** for new projects (`provideZonelessChangeDetection()`).
  Combined with OnPush and signals, this is the biggest lever for INP (Interaction to Next
  Paint) on data-dense UIs — see `../references/angular-accessibility.md` for Core Web Vitals targets.
- **Lazy Loading Routes:** Always lazy-load feature routes using `loadComponent` or `loadChildren`.
- **`@defer` Blocks:** Use `@defer` to defer loading of non-critical UI components until they are needed (e.g., `on viewport`, `on idle`), with fixed-dimension placeholders to protect CLS.
- **Incremental hydration is enabled by default** when using `provideClientHydration()` for SSR (opt out with `withNoIncrementalHydration()`); it auto-enables event replay, so `withEventReplay()` is usually redundant.
- **Prevent Memory Leaks in RxJS Subscriptions:**
  - **Prefer:** `async` pipe in templates (auto-unsubscribes).
  - **Prefer:** `toSignal()` to convert Observables to Signals (auto-unsubscribes).
  - **Acceptable:** `takeUntilDestroyed()` (from `@angular/core/rxjs-interop`) in component classes.
  - **Avoid:** Manual `ngOnDestroy` + `Subject` teardown patterns when modern alternatives exist.
- **Avoid Nested Subscriptions:** Use higher-order mapping operators (`switchMap`, `concatMap`, `mergeMap`, `exhaustMap`) to flatten Observable streams.
- **Cache API Calls:** Use `shareReplay(1)` on Observables that should be shared across subscribers, or prefer a signal store for anything already migrating to signals.

---

## 8. Security Best Practices

- **Trust Angular's Sanitization:** Angular automatically sanitizes values bound to HTML, styles, and URLs. Do NOT bypass sanitization with `bypassSecurityTrustHtml()` unless absolutely necessary and the source is fully trusted.
- **No Direct `[innerHTML]` Binding with Untrusted Data:** Avoid binding user-provided content to `[innerHTML]`.
- **Use HTTP Interceptors for Auth:** Attach JWT tokens and CSRF headers via a centralized `HttpInterceptorFn`. Never hardcode tokens in service calls.
- **Content Security Policy (CSP):** Configure CSP headers on the server to mitigate XSS risks.
- **Route Guards:** Protect sensitive routes using `CanActivateFn` / `CanMatchFn` guards with role-based access control.
- **HTTPS Everywhere:** All backend communication must use HTTPS.
- **No Secrets in Frontend Code:** Never hardcode API keys, passwords, or secrets in the Angular codebase. Use environment files for non-sensitive runtime configuration only.
- **Secure Cookies:** Ensure authentication cookies are set with `HttpOnly`, `Secure`, and `SameSite=Strict` or `Lax` attributes.

---

## 9. Dependency Injection

- **Root-level by default:** Provide services at the root via `@Injectable({ providedIn: 'root' })` unless component-specific or route-level scoping is required.
- **Functional Providers:** Use `provideHttpClient()`, `provideRouter()`, `provideZonelessChangeDetection()`, and other functional providers in `app.config.ts` instead of NgModules.
- **`inject()` Function:** Use the `inject()` function in components, directives, pipes, guards, and interceptors for a cleaner, class-decorator-free approach.
- **Ports as abstract classes or `InjectionToken`s** for anything talking to a backend or external system — see `../references/angular-clean-architecture.md` for the Dependency Inversion pattern and when it's worth the ceremony.

---

## 10. HTTP & Data Layer

- **Services (or repository adapters) own HTTP calls:** Components must never call `HttpClient` directly.
- **`FetchBackend` is the default HTTP backend** — `withFetch()` is no longer required to get it.
- **Functional Interceptors:** Define interceptors as pure functions using `HttpInterceptorFn` instead of class-based interceptors.
- **Error Handling:** Handle HTTP errors centrally in an interceptor, with `catchError` in the service, or via a resource's `.error()`. Never let raw HTTP errors propagate to the template.
- **Typed HTTP Requests:** Always provide a generic type to `HttpClient`/`httpResource` calls (e.g., `this.http.get<Hero[]>('/api/heroes')`).
- **Reads vs. writes:** prefer `httpResource`/`rxResource` for reads; use `HttpClient` directly for mutations (resources abort in-flight requests on param change, which is wrong for POST/PUT/DELETE).

---

## 11. Testing Standards

- **Vitest is the default test runner** (Karma is deprecated). New `ng new` projects generate Vitest configuration; existing Karma projects can migrate with `ng generate @angular/core:karma-to-vitest`. Note `fakeAsync`/`tick`/`waitForAsync` need the `zone.js/plugins/vitest-patch` polyfill or a rewrite to Vitest fake timers.
- **Component Tests:** Test with `TestBed` + `ComponentFixture` under Vitest. Prefer testing behavior through the DOM rather than internal implementation details.
- **Domain/use-case tests need no `TestBed` at all** if you've pulled business logic into framework-free domain types and use-case services with mocked ports — this is one of the concrete payoffs of the Clean Architecture spine described in `../references/angular-clean-architecture.md`. Don't reach for `TestBed` out of habit where a plain Vitest test would do.
- **Mocking:** Mock services/ports with plain objects or `vi.fn()`. Avoid mocking full modules with standalone components.
- **E2E Tests:** Use Playwright or Cypress for end-to-end testing of critical user flows.
- **Test Isolation:** Each test must be independent. Avoid shared mutable state between tests.

---

## 12. Tooling & Configuration

- **Angular CLI:** Use the Angular CLI for all scaffolding (`ng generate`), building, and testing. Never manually create files without the CLI as a starting point.
- **ESLint:** Use `@angular-eslint` for linting. Enforce and configure rules to block common anti-patterns (`no-any`, `no-unused-vars`, etc.). Add `@nx/enforce-module-boundaries` or Sheriff if enforcing architectural boundaries — see `../references/angular-clean-architecture.md`.
- **Prettier:** Use Prettier for consistent code formatting. Configure it to complement ESLint rules.
- **AOT Compilation:** Always build for production using AOT (`ng build`). AOT catches template errors at compile time.
- **`strictTemplates: true`** (on by default in current versions) for full template type-checking — this is the Angular-specific complement to the parent skill's `strict: true` baseline.
- **Keep Dependencies Updated:** Regularly run `ng update` and `npm audit` to stay current on Angular versions and patch security vulnerabilities. Angular ships roughly every 6 months with frequent patches — re-verify version-sensitive claims in this file against angular.dev for the project's actual installed version.

---

## 13. Routing & Navigation

### Functional Route Guards

Prefer functional guards over class-based guards for cleaner, `inject()`-friendly code.

```typescript
// ✅ Correct — functional guard with inject()
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }
  return router.parseUrl('/login');
};

// Usage:
// { path: 'dashboard', canActivate: [authGuard] }
```

### Route Lazy Loading & Router UX

```typescript
export const routes: Routes = [
  {
    path: 'profile',
    loadComponent: () =>
      import('./features/profile/profile.component').then(m => m.ProfileComponent),
  },
  {
    path: 'admin',
    loadChildren: () =>
      import('./features/admin/admin.routes').then(m => m.ADMIN_ROUTES),
    canMatch: [authGuard],
  },
];
```

- `withComponentInputBinding()` — bind route params directly to component `input()`s.
- `withInMemoryScrolling({ scrollPositionRestoration: 'enabled' })` — restore scroll on back-navigation; coordinate manually with server-fetched lists since the `Scroll` event can fire before data arrives.
- `withViewTransitions()` wraps navigation in `document.startViewTransition` — **developer preview**, progressive enhancement only (no-op in unsupported browsers). Don't present it as stable.
- `withPreloading(PreloadAllModules)` (or a custom strategy) for background prefetch of lazy routes.

---

## 14. Clean Architecture, DDD & State Management — summary

Full detail, worked code example, and the honest debate about over-engineering live in
`../references/angular-clean-architecture.md`. Load it before making an architectural call on a
feature; the summary here is only for orientation:

- **Layers map cleanly:** domain (framework-free entities/value objects/ports) → application
  (use-case services depending only on ports) → infrastructure (HTTP/WebSocket adapters +
  DTO↔domain mappers) → presentation (smart/dumb components, signal stores, routing).
- **Ports are `InjectionToken<T>` or abstract classes**, bound to concrete adapters at the
  composition root (`app.config.ts` providers or route-level providers).
- **Take the dependency-inversion spine (ports, mappers, use-cases); skip heavy tactical DDD**
  (aggregates, domain events) unless a specific feature has real invariants beyond form
  validation — most frontend "domains" are thin, and over-abstraction has a real, measurable
  bundle-size cost in the browser (not just a legibility one).
- **State management tiers, lightest first:** plain signals in a service (default) → NgRx
  `signalState`/`SignalStore` (feature-scoped structured state) → classic NgRx Store (only for
  genuinely cross-cutting, event-driven, or audit-heavy concerns). Don't jump tiers
  preemptively.
- **Enforce boundaries mechanically:** Sheriff (folder-based, lighter, plain CLI projects) or
  Nx `@nx/enforce-module-boundaries` (monorepo, `type:`/`scope:` tags) — code review alone
  does not hold a layering discipline over time.
- **Consuming a buildable library from a sibling checkout** (npm `file:../lib/dist/lib`
  dependency): set `preserveSymlinks: true` in the consuming app's builder options, and give
  eager host-provided contracts (injection tokens) their own tiny secondary entry point —
  full rationale and the failure modes in `../references/angular-clean-architecture.md` §9.

---

## 15. Accessibility, Design Tokens & UX — summary

Full detail (WCAG 2.2 AA criteria, Angular Material 3 token theming rules, CDK/Angular Aria,
Storybook, Core Web Vitals targets, Signal Forms validation UX) lives in
`../references/angular-accessibility.md`. Orientation only:

- **Build to WCAG 2.2 AA** as the baseline — it's a superset of 2.0/2.1 AA, so it satisfies
  Ontario's AODA, the federal Accessible Canada Act, and the EU's Accessibility Act
  simultaneously. Pay particular attention to Target Size (2.5.8), Dragging Movements (2.5.7,
  relevant if using CDK drag-drop), and Focus Not Obscured (2.4.11) — these are the criteria
  that most often bite data-dense enterprise UIs.
- **Never override `--mat-*` tokens directly in CSS.** Use the Overrides API
  (`mat.<component>-overrides(...)`) — it's the only customization surface that survives
  Angular Material version upgrades.
- **Core Web Vitals targets (p75):** LCP < 2.5s, INP < 200ms, CLS < 0.1. Zoneless + OnPush +
  signals is the main lever for INP on data-dense dashboards.
- **Angular Aria is developer preview**, not production-ready, despite some third-party blogs
  claiming otherwise — verify against the official roadmap before depending on it.

---

## 16. Embedding React Leaf Widgets — summary

Full detail (the three integration strategies, zoneless callback rules, SSR/hydration
safety, build tooling, a worked directive + host + tests) lives in
`../references/angular-react-interop.md`. Load it before embedding any React component.
Orientation only:

- **Gate the decision first.** Only embed React when no first-party Angular option exists —
  check Angular CDK / `@angular/aria` for headless primitives and AG Grid's official
  `ag-grid-angular` bindings for data grids before reaching for React. Embedding React costs a
  second rendering runtime (~55 KB gzipped for React+React-DOM alone), a second reconciliation
  model to debug, and permanent adapter-maintenance ownership — it must be paying for itself.
- **Direct imperative mounting is the default strategy** for a self-contained "props in,
  events out" leaf widget: a reusable Angular directive calls `createRoot` once in
  `afterNextRender`, re-renders via `afterRenderEffect`'s `write` phase when signal inputs
  change, and `unmount()`s via `DestroyRef.onDestroy`. Reach for a custom-element wrapper only
  if the same widget must also be consumed outside Angular, and for Module/Native Federation
  only for runtime-loaded micro-frontends — both are overkill for a single leaf widget.
- **The custom-element wrapper strategy uses `@r2wc/react-to-web-component`, not a hand-rolled
  `HTMLElement`.** Unlike the Angular↔React bridges below, `r2wc` doesn't know Angular exists —
  it just packages the React component as a generic Web Component, which Angular then consumes
  via `CUSTOM_ELEMENTS_SCHEMA`. Verify its React-version compatibility against its own repo
  before adopting (its README currently scopes v2 to React 18).
- **The zoneless rule that matters most:** every callback a React widget fires back into
  Angular must write a signal (and/or emit via `output()` bound with a template `(event)`
  listener) — mutating a plain component field inside the callback produces no re-render under
  zoneless. This is the single most common way this bridge breaks.
- **No maintained Angular↔React bridge library exists** — `ngReact`, `react2angular`,
  `angular2react`, and `@angular-react/core` are years stale; `@bubblydoo/angular-react` is
  low-adoption and NgModule-era. For direct mounting, write the ~40-line adapter directive
  yourself; for the custom-element boundary, use `r2wc` (above) instead of hand-rolling that
  too.
- **Treat the React widget as a presentation-layer detail**, per this file's Clean
  Architecture guidance above: the Angular host is the Adapter and the anti-corruption layer
  (map domain models → plain props at the boundary); the React widget itself must stay a pure
  function of props with no DI, HTTP, or domain knowledge. Enforce this with the same Nx
  tags/Sheriff boundary mechanism used elsewhere in this file.

---

## 17. Whole-App Angular↔React Coexistence — summary

Full detail (the decision gate, single-spa, Module/Native Federation, bidirectional custom
elements, iframe, Clean Architecture fit, honest costs, testing) lives in
`../references/angular-react-coexistence.md`. Load it only when Angular and React must run as
**two independent apps** — not for embedding one widget in one host (that's §16 above).
Orientation only:

- **Gate the decision first.** Most tasks that mention "Angular and React together" are actually
  the leaf-widget case in §16, not this. This file's four patterns exist for genuine
  micro-frontend splits or incremental full-app migration — confirm which before reaching for
  any of them.
- **single-spa** orchestrates independently-built/-deployed whole apps by route via a
  framework-agnostic root config (`activeWhen`); each app implements
  `bootstrap`/`mount`/`unmount`. Load zone.js exactly once in the root HTML, never per-app —
  that is the most common way an Angular-in-single-spa setup breaks.
- **Module/Native Federation** shares code at runtime across independently-built bundles.
  Angular's tooling has shifted from the classic webpack-based
  `@angular-architects/module-federation` to `native-federation` since the CLI's esbuild-default
  move at v17 — verify which one a given project actually uses. The specific Angular↔React
  gotcha: an Angular remote exposed into a React host still needs the host to share zone.js and
  Angular's own core deps, even though the host isn't an Angular app; treat cross-framework
  remotes as framework-agnostic black boxes (web components + `CustomEvent`s), not shared
  component instances.
- **Custom elements are bidirectional.** Angular → React (the reverse direction of §16):
  `createCustomElement(component, { injector })` packages one Angular component as a native
  custom element; a React-only host with no bootstrapped Angular app gets the required
  `Injector` via `createApplication()` instead of constructor injection. React 19 can consume it
  declaratively (property assignment + `on<Event>` listeners); React 18 needs a `ref` and
  imperative assignment. React → Angular (§16's direction, produced by a library instead of a
  hand-rolled wrapper): `@r2wc/react-to-web-component` — see §16 above.
- **iframe embedding** is the last resort, named honestly as the blunt-force, worst-ergonomics
  option — reach for it only when hard isolation is the actual requirement, not as a default.

---

## 18. Documentation & doc comments (TSDoc)

Public TypeScript surface is documented with TSDoc/JSDoc; TypeDoc renders the reference.
- `/** … */` on every exported class, interface, type, function, and public method.
- Use TSDoc tags: `@param`, `@returns`, `@remarks`, `@example`, `@deprecated`.
- Document the contract and inputs/outputs, not the obvious — let the types carry the shape.
- Components/directives: document each `@Input()` / `@Output()` and any non-obvious lifecycle behavior.

Cross-cutting doc discipline (drift, when to update, generators): see `documenting-code`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `effect()` used to propagate state into other signals | `computed()` for read-only derivation, `linkedSignal()` for writable derived state |
| `effect()` used for data fetching | `resource()` / `rxResource()` / `httpResource()` |
| Mutating a plain object/array in place (or updating state from a non-signal async source) under zoneless | Hold template-relevant state in signals and update immutably via signal writes |
| `httpResource`/`rxResource` used for POST/PUT/DELETE mutations | `HttpClient` directly for writes; resources are for reads only |
| Component calls `HttpClient` directly | Services (or repository adapters) own all HTTP calls |
| `*ngIf`/`*ngFor`/`*ngSwitch` in new code | `@if` / `@for` (with mandatory `track`) / `@switch` |
| Manual `ngOnDestroy` + `Subject` teardown for subscriptions | `async` pipe, `toSignal()`, or `takeUntilDestroyed()` |
| Nested `subscribe()` calls | Higher-order mapping operators (`switchMap`, `concatMap`, `mergeMap`, `exhaustMap`) |
| Direct DOM manipulation (`document.querySelector`, etc.) in components | Template binding, directives, or `Renderer2` |
| `bypassSecurityTrustHtml()` / `[innerHTML]` with untrusted data | Trust Angular's built-in sanitization; never bind user content to `[innerHTML]` |
| Overriding `--mat-*` tokens or internal Material CSS classes directly | The Overrides API (`mat.<component>-overrides(...)`) |
| Installing an Angular↔React bridge library (`ngReact`, `react2angular`, etc.) | Hand-write the small adapter directive per `../references/angular-react-interop.md` |
| Hand-rolling a React→custom-element `HTMLElement` wrapper from scratch | `@r2wc/react-to-web-component` already handles props/events cleanly — see `../references/angular-react-interop.md` strategy (b) |
| Reaching for single-spa/Module Federation/iframe to embed one leaf widget | That's §16's leaf-widget case (`angular-react-interop.md`) — the whole-app patterns in §17 are for genuine micro-frontend splits or migrations |
| Sharing a Module Federation remote's Angular component directly into a React host | Wrap it as a framework-agnostic web component and communicate via `CustomEvent`s instead |
| Global `components/`/`services/`/`pipes/` folders organized by file type | Feature-based structure (LIFT) |
| Presenting dev-preview APIs (view transitions, Angular Aria, `debounced()`, WebMCP) as stable | Explicitly flag experimental/dev-preview status |

(General TypeScript anti-patterns — `any`, `??` vs `||`, floating promises, `interface`/`type`
misuse — live in the parent `../SKILL.md`.)

---

## Pre-flight checklist — run before delivering any Angular code

When writing or reviewing Angular code, verify (this is the Angular-specific layer on top of
the parent TypeScript pre-flight in `../SKILL.md` — run both):

- [ ] **Architecture:** Is the component standalone? Are `core/` and `shared/` boundaries respected? Is business logic in a use-case/service, not the component or template?
- [ ] **State:** Are signals used for local state/UI derivation? Is the state-management tier (plain signal → SignalStore → NgRx Store) the lightest one that fits, not the heaviest available?
- [ ] **Performance:** Is the app zoneless, and does OnPush's now-default status actually pay off (no in-place mutation of template-read state)?
- [ ] **Injection:** Is `inject()` used instead of constructor injection? Are backend-facing dependencies behind a port (abstract class/`InjectionToken`)?
- [ ] **Templates:** Is `@if`/`@for` (with `track`) used instead of `*ngIf`/`*ngFor`? Do `@defer` placeholders have fixed dimensions?
- [ ] **Forms:** Signal Forms for new forms (or a deliberate, stated reason to stay on Reactive Forms)? Are validation errors shown after `touched()`+`invalid()`, not on every keystroke?
- [ ] **Observables:** If RxJS is used in templates, is it wrapped with `| async` or `toSignal()`? Is `httpResource`/`rxResource` used for reads instead of manual `toObservable().pipe(switchMap(...))` boilerplate?
- [ ] **Routing:** Are routes lazy-loaded (`loadComponent`) and protected with functional guards?
- [ ] **Typing:** Are all inputs, outputs, signals, and functions strictly typed? No `any`? (`strictTemplates` on?)
- [ ] **Testing:** Vitest, not Karma? Domain/use-case logic tested without `TestBed` where possible?
- [ ] **Accessibility:** WCAG 2.2 AA criteria checked, especially target size, focus-not-obscured, and drag alternatives if using CDK drag-drop?
- [ ] **Design tokens:** Material customization done via the Overrides API, never by targeting `--mat-*`/internal CSS classes directly?
- [ ] **Security:** No `bypassSecurityTrustHtml()` on untrusted data? Auth via interceptors?
- [ ] **Verification:** Any experimental API used (view transitions, Angular Aria, debounced signals, selectorless syntax) explicitly flagged as such, not presented as stable?
- [ ] **React interop (if applicable):** Was a first-party Angular option (CDK, Angular Aria, `ag-grid-angular`) ruled out before embedding React? Does every React→Angular callback write a signal or emit an `output()`, never mutate a plain field? Is the mount `afterNextRender`-gated (or `@defer`-hydrated) so it never runs during SSR? Is the React widget free of DI/HTTP/domain knowledge? If wrapped as a custom element, was `@r2wc/react-to-web-component` used instead of a hand-rolled `HTMLElement`, with its React-version compatibility checked against its own repo?
- [ ] **Whole-app coexistence (if applicable):** Confirmed this is genuinely two independent apps, not a leaf-widget task that belongs in §16 instead? For single-spa/Federation, is zone.js (and Angular's other shared deps) declared as a singleton on every side that needs it, including a non-Angular host? Is version drift between package docs and the live registry checked before quoting a version?
