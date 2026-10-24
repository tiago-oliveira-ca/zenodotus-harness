# Embedding React Leaf Widgets in Angular

Read this file before embedding any React component inside an Angular application, and before
reaching for a third-party Angular↔React bridge library — none currently on the market is
trustworthy enough to depend on; the adapter here is meant to be hand-written and small.

## Gate the decision before writing any bridge code

Embedding React is a real, permanent tax: a second rendering runtime shipped alongside
Angular's (roughly 55 KB gzipped for React + React-DOM alone, before the widget's own
dependencies), two independent reconciliation models to reason about when debugging, and a
bridge that only you maintain across both frameworks' fast release cadences. Only pay it when
there's no first-party Angular option:

- **Data grid?** AG Grid ships first-party Angular bindings (`ag-grid-angular`,
  `[rowData]`/`[columnDefs]` inputs, event outputs, `api` via `viewChild`) — use those instead
  of embedding a React grid.
- **Headless primitive** (menu, dialog, listbox, focus trap)? Angular CDK / `@angular/aria`
  cover this space natively.
- **Framework-agnostic vanilla-JS library?** Mount it directly with the same directive pattern
  described below, minus the React runtime entirely — no React tax at all.
- **Could the widget be a plain web component?** Wrap it once as a custom element and consume
  it from anywhere, rather than building an Angular-specific React bridge.

Embed React only when: a best-in-class React-only widget has no Angular equivalent, or you're
reusing an existing, maintained corporate React design system, or this is a genuine
incremental migration.

## No maintained Angular↔React bridge library exists — write the adapter yourself

Every well-known Angular↔React interop name is stale or unfit for current versions:
`ngReact`, `react2angular`, `angular2react`, and `ngimport` target AngularJS 1.x and are
7–8 years stale. `@angular-react/core` peaked years ago. The one modern attempt,
`@bubblydoo/angular-react`, is low-adoption (roughly 199 weekly downloads per Socket.dev, with
its last release about a year old) and still built on `NgModule`/`ngAfterViewInit`/
`ngOnChanges` idioms rather than signals — it is not verified against current Angular or React
majors. **Do not add any of these as a dependency.** The direct-mounting adapter in strategy (a)
below is intentionally small (one directive) so owning it is cheap.

This is a distinct claim from strategy (b)'s tooling below: **`@r2wc/react-to-web-component`
is not an Angular↔React bridge** — it doesn't know Angular exists. It only packages a React
component as a generic, framework-agnostic Web Component, which Angular then consumes through
the standard Custom Elements API. That narrower scope is exactly why it's worth using there
instead of hand-rolling.

## The three integration strategies

### (a) Direct imperative mounting — the default for a leaf widget

The Angular host owns a container element, calls `createRoot` once the DOM exists, re-renders
with mapped props when signal inputs change, and unmounts on destroy. This is the
recommended default: fewest moving parts, no custom-element registry, no attribute/property
marshalling — plain JS objects go straight into `root.render(<Widget {...props}/>)`.

**Pitfalls to actively guard against:**
- **Double-root.** Never call `createRoot` more than once on the same DOM node — create it
  once, keep the `Root` reference, call `.render()` on it for updates.
- **Memory leaks.** Always `.unmount()` in `DestroyRef.onDestroy()`.
- **SSR timing.** Mount only inside `afterNextRender` (browser-only, runs once after the first
  render) so the mounting code never executes on the server at all.

### (b) Custom-element / web-component boundary

Wrap the React widget as a custom element rather than hand-rolling the `HTMLElement` subclass:
**`@r2wc/react-to-web-component`** (current major **v2**, `2.1.1` as of this writing, ~940
GitHub stars, actively maintained by Bitovi — last release shipped a shadow-DOM fix) is the
de-facto tool for exactly this job and is worth taking as a dependency, unlike the Angular↔React
bridge libraries above. **Its README states v2 targets React 18** — confirm React-19
compatibility against the repo before adopting on a React 19 codebase; use the legacy `v1`
package (`react-to-webcomponent`, which takes `React`/`ReactDOM` as explicit args) for React
16/17.

```jsx
import r2wc from '@r2wc/react-to-web-component';
import { StarRating } from './star-rating.widget';

const StarRatingElement = r2wc(StarRating, {
  shadow: 'open',                 // 'open' | 'closed' | omit for light DOM
  props: {
    value: 'number',
    max: 'number',
    onRate: 'function',           // callback prop — the other way to emit, besides events
  },
});
customElements.define('star-rating-element', StarRatingElement);
```

In Angular, add `CUSTOM_ELEMENTS_SCHEMA` to the host and consume it with `[prop]`/`(event)`
bindings — this requirement is a compiler concern that has not been removed across Angular
17-22; per angular.dev, wrap the third-party element in a dedicated component/module that
carries the schema so the rest of the app keeps full template type-checking, rather than
scattering the schema wherever a tag happens to appear.

- **Prop types**: `r2wc`'s `props` map takes `"string" | "number" | "boolean" | "function" |
  "json"` — `json` values are `JSON.parse`d from the attribute. By default an r2wc element only
  accepts **properties**, not attributes, for a prop unless you've declared it; complex data
  (objects/arrays) still goes through DOM **properties**, not attribute strings — in Angular
  that means `[richProp]="value"` property binding, or an explicit
  `elementRef.nativeElement.richProp = value`.
- **Emitting outward**: either a `function`-typed prop the React component calls directly, or
  r2wc's `events` option, which dispatches a real DOM event (`bubbles`/`composed` configurable)
  — the `events` route maps more directly onto Angular's native `(eventName)="handler($event)"`
  binding, reading the payload off `$event.detail`.
- **Shadow DOM** (`shadow: 'open'`) gives style encapsulation in both directions (React styles
  can't leak out, Angular theme can't cascade in) — good for isolation, bad if you *want* the
  host theme to reach the widget. Omitting `shadow` (light DOM) is the opposite tradeoff. To
  dispatch an event out of a shadow root, set `composed: true` on it.
- A `CustomEvent` handled via an Angular template `(event)` binding is a bound listener, which
  is one of the notification sources that schedules change detection under zoneless — this
  path integrates cleanly with zoneless *as long as* you use template event bindings rather
  than raw `addEventListener`.
- Only reach for this strategy when the same React widget must also be consumed by non-Angular
  hosts — it adds a layer of indirection (Angular → custom element → React root) that a leaf
  widget used only inside Angular doesn't need. If you specifically need the *reverse*
  direction — an Angular component consumed inside a React host — see
  `angular-react-coexistence.md`'s Angular Elements section instead; this strategy and that one
  are mirror images of the same Custom Elements standard.

### (c) Module Federation / Native Federation

Overkill for a self-contained leaf widget. Justified only when loading independently-deployed
remotes at runtime, doing incremental migration of whole route trees, or sharing a React
micro-frontend across separately-built apps (`@angular-architects/native-federation` is the
relevant tool). For a chart or date-picker, this is a heavyweight answer to a lightweight
question.

## Zoneless: the rule that matters most

Under zoneless (the v22 default), Angular schedules change detection only on explicit
notifications: a signal read in a template getting a new value, `ChangeDetectorRef.markForCheck`
(including `AsyncPipe`), `ComponentRef.setInput`, and bound template/host listener callbacks.
Angular no longer patches async APIs to detect "something happened."

**Therefore: every callback a React widget fires back into Angular must write a signal.** A
signal write schedules exactly the view update needed — you do not need `ApplicationRef.tick()`
and should not reach for manual `detectChanges()`. If you propagate the event via an `output()`
consumed with a template `(event)` binding, that bound listener also notifies the scheduler
correctly. **What breaks silently:** mutating a plain component field inside the React
callback. Under zoneless that produces no re-render, and the failure mode is a UI that just
doesn't update with no error anywhere — the fix is always "write a signal," never
"call `detectChanges()`."

The host itself stays `OnPush` (the v22 default) without any special handling — the React
subtree isn't part of Angular's view, so Angular never dirty-checks inside it. The host only
needs change detection for its own template (loading/error/placeholder state), which signal
reads drive correctly.

## Bridging signal inputs into React re-renders

Define inputs with `input<T>()`. To push updates into React when they change, read the
signals inside a reactive context that calls `root.render`:

- **`afterNextRender`** — mount once, browser-only, SSR-safe by construction. Use this for the
  one-time `createRoot` call.
- **`afterRenderEffect()`** — a render-aware effect with `earlyRead`/`write`/`mixedReadWrite`/
  `read` phases that tracks signals and runs in the DOM write phase after Angular commits, and
  does not run on the server. Use its `write` phase to re-render React when input signals
  change — this is the more correct tool for DOM-dependent third-party rendering than a plain
  `effect()`, though a plain `effect()` guarded appropriately is also defensible (Angular's own
  docs treat "initialize a non-Angular library" as a legitimate side effect). Confirm the exact
  phase semantics against angular.dev for the installed version before treating this as fixed
  syntax — it's flagged version-sensitive in the main skill file's epistemic-calibration
  section.

## Emitting React events back out

Expose `output<T>()` on the host. Pass a plain callback prop into React
(`onChange={(v) => this.valueChange.emit(v)}`); the widget invokes it, you emit, and parents
bind with `(valueChange)`. When the host's own template also depends on the value, have the
same callback write a local signal (see the zoneless rule above) in addition to emitting.

## SSR and hydration

A React widget mounted via `createRoot` is client-only rendering and must never execute during
Angular SSR. Two SSR-safe strategies, usable together:

1. **Mount only in `afterNextRender`** — the code path never runs server-side at all.
2. **Gate the host behind `@defer (hydrate on interaction | viewport | idle)`** with
   incremental hydration, so the whole subtree is dehydrated on the server and only
   fetches/activates on the client trigger — this also defers the React runtime into its own
   chunk, so non-React routes never pay for it. If a React widget does direct DOM manipulation
   that provably conflicts with Angular's hydration, `ngSkipHydration` on the host is the
   escape hatch — reach for it only when hydration actually breaks, not preemptively.

Angular's change detection and React's reconciler are fully independent as long as the
boundary stays clean: Angular must never try to project content into React-owned DOM, and
React must never reach outside its own container.

## Build tooling

- Set in `tsconfig.json`: `"jsx": "react-jsx"` (automatic runtime, no per-file `import React`)
  and `"jsxImportSource": "react"`. Rename host files that contain JSX to `.tsx`.
- The default Angular CLI esbuild builder (`@angular/build:application`) routes `.tsx` through
  the Angular `compiler-cli` before esbuild; a historical bug mishandling `.tsx` relative
  imports (angular/angular#66262) was fixed upstream, but the builder still does not expose
  esbuild's JSX-loader configuration as a documented, supported surface. **Prototype this on
  the actual CLI version you'll ship before committing to the approach.** If it proves
  fragile, `@angular-builders/custom-esbuild` (match its major to your Angular major) is the
  maintained escape hatch for injecting esbuild plugins without ejecting.
- Pin a single `@types/react` version. Mismatched/duplicate `@types/react` in a dependency
  tree (a recurring, well-known DefinitelyTyped pain point) produces confusing "two ReactNode
  types" errors; in a monorepo, force resolution via tsconfig `paths` or package-manager
  `resolutions`/`overrides`.
- Ensure a single copy of `react`/`react-dom` is deduped in the final bundle — multiple copies
  cause "invalid hook call" errors and broken context.
- Lazy-load the React runtime behind `@defer` so routes that never touch the widget don't pay
  its bundle cost.
- In an Nx monorepo, put the React widget in its own buildable UI library (plain React
  package) and consume it from the Angular host library — this is also the natural place to
  enforce the boundary described below.

### Verifying the @defer split across a library boundary

"React stays out of the initial bundle" is only as strong as its verification when the host
page ships inside a buildable library (partial-Ivy, ng-packagr) rather than app source.
ng-packagr emits defer-only component imports as dynamic-import FESM sub-chunks — but only
while *every* reference to the wrapper component in the page file stays inside `@defer`
blocks. A single eager reference silently collapses the split while the build stays green, so
verify at the dist level, not by source discipline:

- **Library dist:** `grep -o "import('./[^']*')" dist/<lib>/fesm2022/<page-chunk>.mjs` must
  show the React wrapper components as dynamic imports.
- **Consuming-app dist:** grep a marker string only the React/vendor code contains (e.g. a
  chart-library symbol) across `main-*.js` and `chunk-*.js` — it must appear only in a lazy
  chunk that `main` does not reference.
- **Dependency wiring:** the library declares `react`/`react-dom` (and any chart lib) as both
  `peerDependencies` and `devDependencies`; the consuming shell adds the chart lib to its own
  `dependencies` (plus `allowedCommonJsDependencies` if it ships CommonJS).

## Clean Architecture fit

This is a presentation-layer detail, not a special case of this file's Clean Architecture
guidance — apply it directly (see the Clean Architecture summary section elsewhere in this
file, and `angular-clean-architecture.md` for full detail):

- **The React widget is a leaf presentation detail.** It must never appear in domain,
  application/use-case, or infrastructure layers — no different in principle from a choice of
  CSS framework.
- **The Angular host is the Adapter** (GoF): it adapts Angular's world (DI, signals, outputs,
  change detection) to React's world (props, callbacks). The host is the smart/container
  component; the React widget is dumb/presentational — a pure function of props, with no DI,
  no HTTP, and no domain knowledge of its own.
- **The props interface is the anti-corruption layer.** Map Angular domain models to plain
  React props at the boundary; never leak domain entities, signals, RxJS, or services into
  React. The widget receives primitives/DTOs and returns primitives via callbacks — this keeps
  it swappable and keeps the domain uncontaminated.
- **Enforce the boundary mechanically**, the same way as any other layering rule in this
  file: tag the React UI library `type:ui-react` and forbid it from depending on
  `domain`/`data-access`/`feature` via `@nx/enforce-module-boundaries` or Sheriff; symmetrically,
  only presentation-layer Angular libs may depend on `type:ui-react`. If a React widget ever
  seems to need a service or domain entity, that's a design smell — push that logic up into
  the Angular host instead of reaching into React for it.
- **Don't over-pattern the adapter.** Adapter is the load-bearing pattern here and is
  non-negotiable. Facade is worth adding only if one Angular service fronts several related
  widgets. GoF Bridge is redundant for this — you're not varying an abstraction against
  multiple implementations, so invoking it adds vocabulary without adding structure to a
  ~40-line directive.

## Worked example

Treat this as a skeleton to verify against current API signatures before shipping, not
copy-paste-final code.

```tsx
// star-rating.widget.tsx — pure React leaf widget: props in, events out
import * as React from 'react';

export interface StarRatingProps {
  value: number;
  max?: number;
  onRate: (next: number) => void;   // event out
}

export function StarRating({ value, max = 5, onRate }: StarRatingProps) {
  return (
    <div role="radiogroup" aria-label="Rating">
      {Array.from({ length: max }, (_, i) => i + 1).map((n) => (
        <button
          key={n}
          role="radio"
          aria-checked={n === value}
          aria-label={`${n} star${n > 1 ? 's' : ''}`}
          onClick={() => onRate(n)}
        >
          {n <= value ? '★' : '☆'}
        </button>
      ))}
    </div>
  );
}
```

```ts
// react-mount.directive.ts — generic mount/update/unmount adapter (Adapter pattern)
import {
  Directive, ElementRef, DestroyRef, inject,
  input, afterNextRender, afterRenderEffect,
} from '@angular/core';
import { createRoot, type Root } from 'react-dom/client';
import * as React from 'react';

@Directive({ selector: '[appReactMount]' })
export class ReactMountDirective<P extends object> {
  readonly component = input.required<React.ComponentType<P>>();
  readonly props = input.required<P>();

  private readonly host = inject(ElementRef<HTMLElement>);
  private readonly destroyRef = inject(DestroyRef);
  private root: Root | null = null;

  constructor() {
    // Browser-only: create the root once, after the DOM exists (SSR-safe).
    afterNextRender(() => {
      this.root = createRoot(this.host.nativeElement);
      this.root.render(React.createElement(this.component(), this.props()));
      this.destroyRef.onDestroy(() => this.root?.unmount());
    });

    // Re-render whenever the component or props signals change (DOM write phase).
    afterRenderEffect({
      write: () => {
        const Cmp = this.component();
        const props = this.props();
        this.root?.render(React.createElement(Cmp, props));
      },
    });
  }
}
```

```ts
// rating-host.component.ts — smart/container component; maps domain -> plain props
import { Component, computed, input, output, signal } from '@angular/core';
import { ReactMountDirective } from './react-mount.directive';
import { StarRating, type StarRatingProps } from './star-rating.widget';

@Component({
  selector: 'app-rating-host',
  imports: [ReactMountDirective],
  template: `
    <div [appReactMount] [component]="StarRating" [props]="reactProps()"></div>
  `,
})
export class RatingHostComponent {
  readonly rating = input.required<number>();
  readonly rated = output<number>();

  private readonly local = signal<number | null>(null);
  protected readonly StarRating = StarRating;

  // Anti-corruption layer: map to plain React props; callback writes a signal AND emits.
  protected readonly reactProps = computed<StarRatingProps>(() => ({
    value: this.local() ?? this.rating(),
    max: 5,
    onRate: (next: number) => {
      this.local.set(next);      // zoneless: signal write schedules CD
      this.rated.emit(next);     // event out via Angular output()
    },
  }));
}
```

**SSR-safe, lazy-loaded variant:**

```html
@defer (hydrate on interaction) {
  <app-rating-host [rating]="model().stars" (rated)="save($event)" />
} @placeholder {
  <div class="rating-skeleton">☆☆☆☆☆</div>
}
```

**Testing, per layer:** test the React widget in isolation with React Testing Library +
Vitest (trivial for a pure props-in/events-out component). Test the Angular host with
Vitest + `TestBed`: assert it mounts the child, forwards mapped props, and emits `output()` on
the callback — don't assert React internals from the Angular side, test the contract. Under
zoneless `TestBed`, prefer `await fixture.whenStable()` over manual `fixture.detectChanges()`.

```ts
// star-rating.widget.spec.tsx — React side
import { render, screen, fireEvent } from '@testing-library/react';
import { StarRating } from './star-rating.widget';

test('emits selected rating', () => {
  const onRate = vi.fn();
  render(<StarRating value={2} onRate={onRate} />);
  fireEvent.click(screen.getByLabelText('4 stars'));
  expect(onRate).toHaveBeenCalledWith(4);
});
```

```ts
// rating-host.component.spec.ts — Angular side, zoneless
import { TestBed } from '@angular/core/testing';
import { RatingHostComponent } from './rating-host.component';

test('mounts React child and emits on rate', async () => {
  const fixture = TestBed.createComponent(RatingHostComponent);
  fixture.componentRef.setInput('rating', 3);
  let emitted: number | undefined;
  fixture.componentInstance.rated.subscribe((v) => (emitted = v));
  await fixture.whenStable();
  const btn = fixture.nativeElement.querySelector('[aria-label="5 stars"]') as HTMLButtonElement;
  btn.click();
  await fixture.whenStable();
  expect(emitted).toBe(5);
});
```

## Honest costs — say these plainly, don't undersell the tradeoff

- **Dual-framework bundle**: two rendering runtimes shipped together, plus whatever ecosystem
  the widget itself pulls in (a React chart library can dwarf React's own footprint).
- **Two reconciliation models on one page**: debugging spans two mental models and two
  devtools.
- **You own the bridge, permanently**: for strategy (a)'s hand-written directive, no maintained
  library carries this at all — every Angular or React major is a potential re-test. Strategy
  (b) via `r2wc` shifts some of that burden onto its maintainers, but not all of it: `r2wc`
  itself states version-specific React compatibility (v2 targets React 18; verify against its
  repo before a React 19 upgrade), so a React major bump can still force a re-verification pass.
- **Styling/theming conflicts**: an Angular design system and React widget styles collide
  unless deliberately isolated (shadow DOM) or reconciled (shared tokens); shadow DOM fixes
  leakage but also blocks the host theme from cascading in.
- **Accessibility/focus management is the most commonly under-estimated risk.** Focus can be
  lost or trapped across the Angular↔React boundary; keyboard order, `aria-activedescendant`,
  and focus restoration after the React subtree re-renders need deliberate, explicit testing —
  don't assume it works because both frameworks individually handle focus well.
- **Hiring/maintenance cost**: every contributor now needs competence in both stacks.

Re-validate the adapter's tests and the build prototype on every Angular or React major before
upgrading the rest of the app. If bridge maintenance ever exceeds the value the React-only
widget provides, replace it with a native Angular or web-component alternative rather than
continuing to carry it.
