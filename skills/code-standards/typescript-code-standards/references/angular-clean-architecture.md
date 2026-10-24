# Clean Architecture & DDD on the Angular Frontend

This supersedes the generic `code-standards/software-architecture` skill for Angular/TypeScript
— read this file first for Angular architecture/domain-modeling decisions and fall back to the
generic skill only for concerns not covered here.

## Contents
1. [Layer mapping](#1-layer-mapping)
2. [Ports: abstract class vs InjectionToken](#2-ports-abstract-class-vs-injectiontoken)
3. [Worked example](#3-worked-example)
4. [Enforcing boundaries: Nx tags vs Sheriff](#4-enforcing-boundaries-nx-tags-vs-sheriff)
5. [State management decision tree](#5-state-management-decision-tree)
6. [Testing per layer](#6-testing-per-layer)
7. [The honest debate: when this is over-engineering](#7-the-honest-debate-when-this-is-over-engineering)
8. [Staged recommendations](#8-staged-recommendations)
9. [Consuming a buildable library from a sibling checkout](#9-consuming-a-buildable-library-from-a-sibling-checkout)

---

## 1. Layer mapping

- **Domain** (innermost, framework-free): entities, value objects, aggregates (only where
  genuinely needed — see §7), domain services, and **port interfaces** (repository
  contracts). Zero `@angular/*` imports — this is the layer you can unit-test with zero
  `TestBed`.
- **Application / use-cases**: interactors that orchestrate the domain and depend only on
  ports. In Angular these are plain injectable classes that receive ports via `inject()`.
- **Infrastructure**: adapters implementing the ports — HTTP clients, WebSocket clients,
  `localStorage`, plus DTO↔domain mappers. This is the only layer that touches `HttpClient`.
- **Presentation**: components, directives, pipes, signal-based stores/facades, routing.
  Depends inward on application/domain, never the reverse.

The dependency rule (source dependencies point inward only) is the whole game — in
TypeScript/Angular you enforce it with tooling (§4), not willpower.

## 2. Ports: abstract class vs InjectionToken

TypeScript `interface`s cannot be DI tokens (no runtime artifact), so a port needs one of two
forms:

- **`InjectionToken<T>`** where `T` is an interface — most explicit, requires
  `@Inject(TOKEN)`/`inject(TOKEN)`. Best when the port is a pure interface and you want zero
  coupling to a class shape.
- **Abstract class as token** — `abstract class OrderRepository { abstract findById(...): Promise<Order>; }` doubles as both the type and the DI token; bind the concrete adapter with
  `{ provide: OrderRepository, useClass: HttpOrderRepository }`. Cleaner injection
  (`inject(OrderRepository)`), no separate token object needed.

Both give you the classic ports/adapters shape: application code depends on the abstraction,
infrastructure provides the implementation, DI wires them at the composition root
(`app.config.ts` providers, or route-level `providers` for narrower scoping).

## 3. Worked example

```ts
// domain/money.ts — value object, framework-free
export class Money {
  private constructor(readonly amountCents: number, readonly currency: string) {}
  static of(amountCents: number, currency = 'EUR'): Money {
    if (!Number.isInteger(amountCents)) throw new Error('amountCents must be integer');
    return new Money(amountCents, currency);
  }
  add(other: Money): Money {
    if (other.currency !== this.currency) throw new Error('currency mismatch');
    return new Money(this.amountCents + other.amountCents, this.currency);
  }
}

// domain/order.ts — entity/aggregate, only if the invariants genuinely warrant it
export class Order {
  private constructor(
    readonly id: string,
    private readonly lines: ReadonlyArray<{ sku: string; qty: number; price: Money }>,
  ) {}
  static create(id: string, lines: Array<{ sku: string; qty: number; price: Money }>): Order {
    if (lines.length === 0) throw new Error('order needs at least one line');
    return new Order(id, lines);
  }
  total(): Money {
    return this.lines.reduce(
      (sum, l) => sum.add(Money.of(l.price.amountCents * l.qty, l.price.currency)),
      Money.of(0),
    );
  }
}

// domain/order-repository.port.ts — abstract class doubles as DI token
export abstract class OrderRepository {
  abstract findById(id: string): Promise<Order>;
  abstract save(order: Order): Promise<void>;
}

// application/place-order.usecase.ts — depends only on the port
import { Injectable, inject } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PlaceOrderUseCase {
  private readonly repo = inject(OrderRepository);
  async execute(order: Order): Promise<void> {
    await this.repo.save(order); // domain invariants already enforced in Order.create()
  }
}

// infrastructure/order.mapper.ts — DTO ↔ domain, the only place that knows both shapes
export interface OrderDto { id: string; lines: { sku: string; qty: number; priceCents: number; ccy: string }[]; }
export const OrderMapper = {
  toDomain: (d: OrderDto): Order =>
    Order.create(d.id, d.lines.map(l => ({ sku: l.sku, qty: l.qty, price: Money.of(l.priceCents, l.ccy) }))),
  toDto: (o: Order): OrderDto => { /* ...serialize... */ return {} as OrderDto; },
};

// infrastructure/http-order.repository.ts — implements the port
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class HttpOrderRepository extends OrderRepository {
  private readonly http = inject(HttpClient);
  async findById(id: string): Promise<Order> {
    const dto = await firstValueFrom(this.http.get<OrderDto>(`/api/orders/${id}`));
    return OrderMapper.toDomain(dto);
  }
  async save(order: Order): Promise<void> {
    await firstValueFrom(this.http.post<void>('/api/orders', OrderMapper.toDto(order)));
  }
}

// app.config.ts — composition root: bind the port to the adapter
export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideHttpClient(),
    { provide: OrderRepository, useClass: HttpOrderRepository }, // Dependency Inversion, wired here
  ],
};

// presentation/order.store.ts — signal store as facade
export const OrderStore = signalStore(
  { providedIn: 'root' },
  withState<{ placing: boolean; error: string | null }>({ placing: false, error: null }),
  withMethods((store, placeOrder = inject(PlaceOrderUseCase)) => ({
    async place(order: Order) {
      patchState(store, { placing: true, error: null });
      try { await placeOrder.execute(order); }
      catch (e) { patchState(store, { error: (e as Error).message }); }
      finally { patchState(store, { placing: false }); }
    },
  })),
);
```

Smart/dumb split at the presentation layer: the smart container injects the store and calls
its methods; the dumb component takes `input()`/emits `output()` and injects nothing.

## 4. Enforcing boundaries: Nx tags vs Sheriff

Two real, verifiable tools — pick based on whether the project is already an Nx monorepo:

- **Nx `@nx/enforce-module-boundaries`** — tag each library in `project.json`
  (`type:feature`, `type:data-access`, `type:ui`, `type:util`, `scope:orders`) and declare
  `depConstraints` in the root ESLint config. `bannedExternalImports` can stop the domain
  layer from importing `@angular/*` directly. Requires the Nx build system and splitting into
  libraries.
- **Sheriff (`@softarc/sheriff-core` + `@softarc/eslint-plugin-sheriff`)** — a lighter,
  folder-based alternative for a plain Angular CLI workspace. Define `tagging` (folder → tag)
  and `depRules` in `sheriff.config.ts`; it enforces boundaries via `index.ts` barrel public
  APIs, without forcing an Nx library split.

**Default recommendation:** Sheriff for a single-app CLI workspace wanting boundaries without
monorepo overhead; Nx tags if the project is already in (or moving to) an Nx monorepo.
`dependency-cruiser` is a third option some teams use for broader graph rules.

## 5. State management decision tree

Pick the lightest tool that fits — don't jump tiers preemptively:

- **Plain signals in a service** — local or small feature state. Zero dependencies. This is
  the default; don't reach further without a concrete reason.
- **NgRx SignalStore (`@ngrx/signals`)** — feature-level structured state without Redux
  ceremony: `signalStore(withState, withComputed, withMethods, withHooks)`, plus
  `withEntities` for collections and `rxMethod` for RxJS-driven side effects. A reasonable
  default once plain signals in a service get unwieldy for a feature.
- **NgRx `signalState`** — middle ground: signal-based nested state with `patchState`, no
  full store ceremony.
- **Classic NgRx Store (actions/reducers/effects/selectors)** — reserve for large,
  event-driven apps needing centralized event processing, global synchronization, or
  time-travel debugging. Both classic Store and SignalStore are officially supported and can
  coexist in one app.

Rule of thumb: small/mid-size project, ≤4-5 developers → plain signals or `signalState` is
safe. Medium/large → SignalStore. Enterprise with strict cross-cutting/audit requirements →
classic NgRx Store for those specific concerns, not necessarily the whole app.

Don't add a facade layer on top of a signal store "just in case you swap state libraries
later" unless that migration is an actual planned requirement — a signal store already *is*
effectively a facade over its own internals.

## 6. Testing per layer

- **Domain tests**: pure Vitest, no `TestBed`, no browser — this is the concrete payoff of
  keeping the domain framework-free.
- **Use-case tests**: instantiate the interactor with mock ports (plain objects implementing
  the abstract class/interface, or `{ provide: Port, useValue: { ... } }` via `TestBed` if you
  want DI resolution exercised too).
- **Component tests**: `TestBed` + Vitest (jsdom/happy-dom by default; Vitest Browser Mode via
  Playwright when a real browser is needed).
- Presentational (dumb) components with no injected dependencies are the best Storybook
  candidates — another reason the smart/dumb split pays for itself.

## 7. The honest debate: when this is over-engineering

This is genuinely contested — represent both sides rather than picking one as obviously
correct:

**Against full Clean Architecture on the frontend:**
- Most frontend "domain" logic is orchestration/presentation/I/O, not invariant-rich business
  rules — those usually live in the backend. Building aggregates, domain events, and a full
  tactical layer for what's really a CRUD screen produces ceremony with little payoff.
- **Bundle cost is real and frontend-specific** (Alex Bespoyasov's framing): more abstraction
  code means more bytes the browser downloads, parses, and interprets before it can render —
  a cost that a backend Clean Architecture layer doesn't pay.
- The frontend is inherently coupled to a rendering model, router, and change-detection
  strategy — it can't be made truly framework-independent, so "swap the framework later"
  rarely materializes as a real justification.
- Vertical Slice / Feature-Sliced Design (organize by feature/use-case, tolerate a little
  duplication, maximize cohesion within a slice) is often a better fit, and aligns with
  Angular's own style guide (organize by feature, avoid `components`/`services` folders).

**Where Angular's own guidance diverges from Clean Architecture orthodoxy:**
- The official style guide explicitly favors feature-based organization over horizontal,
  type-based layering at the folder level — closer to vertical slices than to a global
  layered tree.

**Synthesis (the recommendation this skill follows):** take the dependency-inversion spine
(ports, mappers, use-cases, enforced boundaries) because it delivers testability and
controlled change at low cost. Skip heavy tactical DDD (aggregates, domain events) unless a
specific feature has real domain complexity. Organize primarily by feature/domain (vertical
slices), layering *within* each slice rather than across the whole app.

## 8. Staged recommendations

**Stage 1 — foundations:** standalone + zoneless + OnPush (all defaults already). Organize by
feature, not by type. Default to plain signals in services for state. Vitest from day one.

**Stage 2 — introduce the dependency-inversion spine where it pays:** for any feature talking
to a backend, define an abstract-class port + HTTP adapter + DTO mapper, bind at the
composition root. Wrap non-trivial orchestration in use-case services depending only on
ports.

**Stage 3 — enforce boundaries as the app/team grows:** Sheriff for a CLI project, Nx tags for
a monorepo. Adopt NgRx SignalStore once plain signals get unwieldy for a feature; reserve
classic NgRx for genuinely event-driven/audit-heavy areas.

**Stage 4 — bounded contexts / micro-frontends, only if warranted:** split into domain
libraries (strategic DDD). Consider Module Federation only if independent deployment is an
actual requirement, not a hypothetical one.

**Thresholds that should change the decision:** don't add a facade unless insulating against
a planned state-library migration; don't build aggregates/domain events unless a feature has
real invariants beyond form validation; if abstraction is measurably growing the bundle
without improving testability or change-isolation, cut it.

## 9. Consuming a buildable library from a sibling checkout

When a shell app consumes an ng-packagr library from a sibling checkout via an npm
`file:../lib/dist/lib` dependency, two non-obvious traps recur:

- **`preserveSymlinks: true` in the consuming app's builder options is mandatory.** npm
  installs `file:` directory dependencies as symlinks, and with the CLI default
  (`preserveSymlinks: false`) the library FESM's `@angular/*` imports resolve from the
  *library repo's own* `node_modules` — silently bundling a second Angular runtime. The build
  stays green; the failure is NG0203-class DI breakage at runtime. Any symlinked package that
  carries its own `node_modules` can duplicate a framework runtime this way.
- **Split eager contracts from lazy features into separate entry points.** When a library
  exports both lazy route configs and injection tokens the host must provide eagerly, putting
  the tokens in the primary entry point drags the whole feature bundle into the host's initial
  chunk. Give the contract a tiny secondary entry point (e.g. `lib/auth-contract`) so the
  composition-root import stays cheap. Shape the contract interfaces structurally to the
  host's stores so `useExisting` provider wiring works with zero adapter classes.
