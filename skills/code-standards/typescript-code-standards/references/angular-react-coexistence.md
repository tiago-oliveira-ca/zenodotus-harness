# Angular ↔ React Whole-App Coexistence

Read this file when Angular and React must run as **two independent applications** sharing a
page or a domain — not one widget embedded in one host. If the actual task is "put one React
chart/grid/widget inside an Angular app" (or vice versa), stop here and use
`angular-react-interop.md` instead — that is the far more common task, and this file's patterns
are needless weight for it.

## When this file actually applies

In practice this combination is almost never a deliberate, permanent architecture — it's a
bridge. The real-world triggers are:

- **Incremental full-app migration.** A team is moving an Angular app to React (or the reverse)
  a route at a time, and both frameworks must serve traffic side by side until the migration
  finishes.
- **Micro-frontend org split.** Different teams own different routes/domains and have picked
  different frameworks; the two must compose into one product without a shared build.
- **One specific component must cross the boundary**, but the rest of each app stays untouched
  and independently deployed (narrower than a full micro-frontend split).

If none of these apply, you almost certainly want `angular-react-interop.md`'s leaf-widget
adapter instead.

## Decision gate — pick one, don't default to the fanciest

| Pattern | Reach for it when | Cost |
|---|---|---|
| **single-spa** | Whole routes/apps need independent build + deploy, orchestrated by a framework-agnostic root config; the classic fit for incremental full-route migration. | A root config + per-app lifecycle wiring; shared deps go through import maps. |
| **Module/Native Federation** | Apps need to share more than routing — runtime code sharing (a design system, auth state, a specific component) across independently-built, independently-deployed bundles. | The most infrastructure-heavy option; real version-skew risk across remotes. |
| **Custom elements (Angular Elements ↔ react-to-web-component)** | Only one specific component needs to be reusable in the other framework's shell — either direction: Angular → React via `@angular/elements`, or React → Angular via `@r2wc/react-to-web-component` (see `angular-react-interop.md` strategy (b) for that direction). | Narrower blast radius than single-spa/Federation, but still a permanent custom-element boundary to maintain on whichever side produces it. |
| **iframe** | Hard runtime isolation is itself the requirement (untrusted third-party widget), or a legacy tool has no other integration path and this is explicitly temporary. | Not a real micro-frontend architecture — the blunt-force option, with the worst accessibility/UX story of the four. |

Default order of preference when more than one would technically work: single-spa for a genuine
route-level migration → Angular Elements for a single reusable component → Module/Native
Federation only when runtime code-sharing beyond routing is the actual requirement → iframe only
as a last resort.

## 1. single-spa — orchestrating two whole apps

[single-spa](https://single-spa.js.org) mounts/unmounts independently-built micro-frontends by
route via a framework-agnostic root config, each app implementing `bootstrap`/`mount`/`unmount`
lifecycles.

**Version-drift warning, verify before quoting:** single-spa's own `ecosystem-angular` docs page
still shows Angular 16-18 in its support table, but as of this writing `single-spa-angular` on
npm is at **v21.0.2** (peer `@angular/core: ">=21.0.0 <22.0.0"`), tracking Angular's major
directly — the docs page's *code shape* is current, its *version table* is stale. Confirm against
npm, not the docs page, before stating a supported-Angular-version claim.

**Angular side** (`single-spa-angular`, current wiring):
```typescript
import { platformBrowserDynamic } from "@angular/platform-browser-dynamic";
import { NgZone } from "@angular/core";
import { Router, NavigationStart } from "@angular/router";
import { singleSpaAngular, getSingleSpaExtraProviders } from "single-spa-angular";
import { AppModule } from "./app/app.module";

const lifecycles = singleSpaAngular({
  bootstrapFunction: (singleSpaProps) =>
    platformBrowserDynamic(getSingleSpaExtraProviders()).bootstrapModule(AppModule),
  template: "<app-root />",
  Router,
  NavigationStart,
  NgZone,
});

export const { bootstrap, mount, unmount } = lifecycles;
```

**React side** (`single-spa-react`, latest stable **6.0.2**; a 7.0.0-beta targets React ≥19 but
isn't GA — stay on 6.x for a production app until it is):
```javascript
import React from "react";
import ReactDOMClient from "react-dom/client";
import rootComponent from "./path-to-root-component.js";
import singleSpaReact from "single-spa-react";

export const { bootstrap, mount, unmount } = singleSpaReact({
  React,
  ReactDOMClient,
  rootComponent,
  errorBoundary(err, info, props) {
    return <div>This renders when a catastrophic error occurs</div>;
  },
});
```
Every React micro-frontend needs its own `errorBoundary`/`errorBoundaryClass` — without one,
single-spa's own docs warn an uncaught error can unexpectedly unmount the whole app, not just
this micro-frontend.

**Root config — routing split between Angular and React:**
```javascript
singleSpa.registerApplication({
  name: "angularApp",
  app: () => import("src/angularApp/main.single-spa.js"),
  activeWhen: "/app1",
});
singleSpa.registerApplication({
  name: "reactApp",
  app: () => import("src/reactApp/main.js"),
  activeWhen: (location) => location.pathname.startsWith("/app2"),
});
```
`activeWhen` accepts a path-prefix string, an activity function, or a mix — this is the whole
routing-split mechanism.

**Load-bearing gotchas:**
- **Exactly one zone.js on the page, loaded once in the root HTML** — never per-app. This is the
  single most common way an Angular-in-single-spa setup breaks.
- Share frameworks/libraries via the root config's **import map** so each is fetched once across
  all micro-frontends — don't let each app bundle its own copy of React or Angular's core.
- Keep UI frameworks out of the root config itself. The root config's only job is orchestration;
  putting framework code there re-couples every app to it, defeating the point of independent
  deploys.

## 2. Module Federation / Native Federation — runtime code sharing

Webpack 5's `ModuleFederationPlugin` lets independently-built bundles expose and consume code
from each other at runtime — sharing more than routing, e.g. a design system or a specific
component, while each app still deploys independently.

```javascript
// remote: expose a module
new ModuleFederationPlugin({
  name: "app1",
  filename: "remoteEntry.js",
  exposes: { "./Button": "./src/Button" },
  shared: { react: { singleton: true, requiredVersion: deps.react } },
});

// host: consume it
new ModuleFederationPlugin({
  name: "host",
  remotes: { app1: "app1@http://localhost:3001/remoteEntry.js" },
  shared: { react: { singleton: true, requiredVersion: deps.react } },
});
```
`singleton: true` defaults to `false` and is, per webpack's own docs, "critical for libraries
with global state like react" — without it each side loads its own copy, which for
React/Angular's core runtime causes duplicate-instance bugs, not just bundle bloat.

**Angular tooling has shifted — verify which one the project actually uses.** Since Angular's
CLI default builder moved from webpack to esbuild at v17, the classic
`@angular-architects/module-federation` package is a **legacy/maintenance path** for Angular
projects still on the webpack builder. The current default is
**`@angular-architects/native-federation`** — a thin wrapper that delegates to Angular's esbuild
`ApplicationBuilder` directly, using the same mental model without requiring webpack. Its own
GitHub org has moved to `github.com/native-federation`, and the classic plugin's README now
points migrators there. Don't assume a project is on the classic plugin just because "Module
Federation" is the requested term — ask or check `package.json` before writing config.

**The specific Angular-into-React gotcha (this is the one worth remembering):** exposing an
Angular remote — even packaged as a web component — into a non-Angular host throws
`Error: In this configuration Angular requires Zone.js at new NgZone` if the host's federation
config shares only `react`/`react-dom` and omits zone.js and Angular's own core deps
(`@angular/core`, `@angular/common`, `@angular/router`). **The React host must still declare and
load Angular's shared dependencies, even though the host itself isn't an Angular app.** This is
documented against real angular-architects tooling issues, not a hypothetical. The pattern that
avoids the whole class of problem: treat each remote as a **framework-agnostic black box** — wrap
what crosses the boundary as a Web Component / custom element, and communicate via DOM
`CustomEvent`s rather than sharing framework-specific component instances directly across the
Angular↔React line. Plain component-level federation (sharing an actual React or Angular
component object across the wire) is fine Angular-to-Angular or React-to-React; it is the wrong
tool once the two sides are different frameworks.

**Version-skew risk is the main operational cost.** With `singleton: true`, if a host and remote
disagree on version, webpack loads the *higher* version and only warns the side running the
lower one — it does not fail the build. Since remotes deploy independently, that means a
version-skewed remote can reach production silently. The documented mitigation is **contract
tests in CI**: verify the host actually renders the remote's exposed module with the props it
really passes, before either side ships — "teams that skip this step find out about version skew
from users," not from a pipeline failure.

## 3. Angular Elements ↔ React — bidirectional custom elements

Both directions of this specific pattern rely on the same native Custom Elements standard, and
both are current/maintained in 2026: **Angular → React** is production-mature via the first-party
`@angular/elements` package; **React → Angular** has no first-party equivalent (React itself has
no "export as custom element" API, in React 19 or otherwise) but is well served by the
third-party `@r2wc/react-to-web-component` — see `angular-react-interop.md` strategy (b) for that
direction's full detail (props/events mapping, `CUSTOM_ELEMENTS_SCHEMA`, shadow DOM). This section
covers Angular → React.

Package one Angular component as a native Custom Element via `@angular/elements`, then render it
as a plain tag inside an otherwise-React app:

```typescript
import { createCustomElement } from '@angular/elements';
import { createApplication } from '@angular/platform-browser';
import { Popup } from './popup';

const app = await createApplication({ providers: [ /* global providers */ ] });
const PopupElement = createCustomElement(Popup, { injector: app.injector });
customElements.define('popup-element', PopupElement);
```
`createCustomElement(component, { injector })` is the stable, unchanged signature. The
`createApplication()` step matters specifically for this scenario: a React host has no
bootstrapped Angular root component to inject from, so `createApplication()` (from
`@angular/platform-browser`, Angular ≥14.2) builds a bare application context purely to obtain an
`Injector` for the element — this is the piece that changes from the single-app scenario
`angular-react-interop.md` and `frameworks/angular.md` already document, where an `Injector` is
just constructor-injected inside an already-running Angular app. One documented limitation: there
is currently no way to set a custom zone (e.g. a `noop` zone) through this API.

**Naming caveat straight from Angular's own docs**: never reuse the Angular component's own
selector as the custom-element tag name — doing so makes Angular create two component instances
for a single DOM element.

**Build tooling — ship one consumable bundle.** The Angular CLI emits separate
`main`/`polyfills`/`runtime`/`styles` chunks with content hashes by default; a React app loading
this via a plain `<script>` tag needs one stable bundle instead:
- **`ngx-build-plus`** (`ng add ngx-build-plus`, then `ng build --single-bundle`) — puts
  everything reachable from the entry point into one file. Verify its current default flags
  against the installed version before assuming `--single-bundle`/`keepPolyfills`/`keepStyles`
  behave exactly as an older tutorial describes; these have changed to track CLI defaults.
- **Manual concatenation** — build with `--output-hashing=none` for stable filenames, then
  concatenate the emitted files into one script.

**React consumes it as a plain tag** — `<popup-element></popup-element>` — with input/output
mapping following native Custom Element semantics, not React props. **React 19 changed how much
of this is declarative** — treat React 18 and React 19 as genuinely different tiers here, not
interchangeable:

- **Inputs → attributes**, dash-separated lowercase (an aliased input `myInputProp` becomes
  attribute `my-input-prop`); attributes only ever carry strings.
- **Outputs → `CustomEvent`s**, event name matching the Angular output exactly (camelCase
  preserved), payload on `event.detail`.
- **Non-primitive inputs need DOM properties, not attributes** — the typed `NgElement &
  WithProperties<T>` shape exists so you can assign objects/arrays directly
  (`el.someInput = objectValue`) rather than serializing to a string.

**React 19 (current default approach)** — properties and events can be passed declaratively in
JSX: a prop is assigned as a DOM **property** if the element instance exposes that property name,
otherwise as an attribute; an `on<EventName>` prop registers `addEventListener` for
`<EventName>` verbatim, casing and dashes preserved:
```tsx
// message flows through as a property (Popup's `message` input); onclosed listens for the
// CustomEvent named "closed"
<popup-element message={someObject} onclosed={handleClosed} />
```
Two open issues to know about before relying on this: **a TypeScript-typing bug** rejects
`on`-prop names with no hyphen (facebook/react#32258) — an Angular output like `valueChanged`
needs `onvalueChanged` at runtime, which is valid JS but may not type-check; and **React 19 does
not attach these listeners during SSR hydration** (facebook/react#35446) — they attach on first
client render, so an Angular Element behind a hydrated boundary needs its interactive behavior
verified post-hydration, not assumed.

**React 18 (fallback, or when the TS/SSR issues above block the declarative form)** — set
properties and listen for events imperatively via a `ref`:
```tsx
const ref = useRef<HTMLElement & { message?: unknown }>(null);
useEffect(() => {
  if (!ref.current) return;
  ref.current.message = someObject;                    // property, not attribute
  const onClosed = (e: Event) => handleClosed((e as CustomEvent).detail);
  ref.current.addEventListener('closed', onClosed);
  return () => ref.current?.removeEventListener('closed', onClosed);
}, [someObject]);
return <popup-element ref={ref} />;
```

**Destroy/reattach is a known, tracked rough edge** (angular/angular#38778): re-attaching a
custom element created this way after it's been disconnected can misbehave in
`disconnectedCallback`. Be deliberate about React's key-based remounting near this boundary — an
unnecessary remount is more likely to trigger it than leaving the element in place.

**SSR note**: Angular Elements bootstrap on `connectedCallback` and are inherently client-side —
don't expect them to render during an Angular or React SSR pass without extra work; treat them as
client-only (dynamic import inside `useEffect`, or `'use client'` in a Next.js/RSC host).

## 4. iframe embedding — the last resort, named honestly

Two fully separate deployments, one embedded in the other via `<iframe>`. Zero shared runtime,
zero framework coupling — and, correspondingly, the worst integration ergonomics of the four
patterns here. Reach for this only when isolation is the actual requirement (an untrusted
third-party widget) or a legacy tool has no other reasonable path in and this is explicitly
temporary — not as a default "fastest way to combine two apps."

- **Cross-frame communication is manual**, via `postMessage`/`addEventListener('message', …)` —
  there is no shared state, routing, or event system across the boundary by default.
  Same-origin content can use direct DOM/JS access instead, but that reintroduces the coupling
  iframes exist to avoid.
- **Sizing/resizing is the recurring pain point**: the parent doesn't know the iframe content's
  natural height without the child actively reporting it back (typically via `postMessage` on
  content resize).
- **Deep-linking and routing sync between parent and iframe is entirely hand-built** — the
  browser's own history/URL doesn't automatically reflect state inside the frame.
- **Accessibility is worse here than in any of the other three patterns.** Focus management
  across a frame boundary, screen-reader announcement of frame content changes, and keyboard
  navigation into/out of the iframe all need deliberate, explicit testing — don't assume it works
  because the content inside the frame is itself accessible.

## Clean Architecture fit

Same rule as `angular-react-interop.md`, applied at a larger grain: the coexistence mechanism
itself — a single-spa root config, a federation shell's remote-loading code, custom-element
registration, or an iframe boundary — is pure composition-root/infrastructure concern. It must
never leak into either app's domain or use-case layers; neither app's business logic should know
or care that it's being orchestrated this way. See `angular-clean-architecture.md` for the full
layering discipline this composes with.

## Honest costs

- **Independent deploys mean independent regression risk.** A route or remote can break in
  production without either team's own CI catching it — the failure only appears when both sides
  run together. Contract tests (Module Federation) or cross-app e2e coverage (single-spa) are
  load-bearing, not optional polish.
- **Shared-runtime singleton conflicts are the most common integration bug across single-spa and
  Module Federation alike** — zone.js, RxJS, React itself. Get the shared-dependency
  configuration right before writing any feature code that depends on it; debugging a duplicate-
  instance bug across two independently-built bundles is expensive.
- **None of these four are meant to be permanent architecture.** In practice they're bridges —
  plan the migration's end state and exit condition up front, rather than letting the coexistence
  layer become a permanent fixture nobody budgeted for.

## Testing

- **Cross-boundary coverage only shows up as e2e.** A broken `activeWhen` route match, a missing
  shared-singleton entry, or a version-skewed remote are all invisible to either app's own unit
  tests — only a real browser hitting the actual mounted boundary (Playwright, driving real
  routes) catches them.
- **Contract-test Module Federation remotes before they ship** — assert the host actually renders
  the remote's exposed module with the props it really passes, in CI, ahead of an independent
  remote deploy reaching production with a version mismatch.
- **Custom elements (either direction)**: test the wrapped component in isolation the normal way
  for its own framework; separately test the host's property/event wiring across the custom-
  element boundary (React's `ref`-based assignment and listeners, or Angular's
  `[prop]`/`(event)` bindings under `CUSTOM_ELEMENTS_SCHEMA`), since that boundary has no type
  safety on either side.
