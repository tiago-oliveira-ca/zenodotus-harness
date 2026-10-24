---
name: zeno-react-patterns
description: >
  React 18/19 component patterns — hooks discipline, server/client component boundaries,
  Suspense and error boundaries, form actions, data fetching, state-location decision trees,
  composition recipes, and accessibility-first markup. Use when writing or reviewing React
  function components, custom hooks, or component trees, or when deciding where state should
  live. Trigger on: "write a React component", "custom hook", "where should this state live",
  "server component or client component", "React form", "Suspense boundary", "error boundary",
  "compound component", "React state management", "review this JSX".
---

# React Patterns

Idiomatic patterns for React 18/19 function components: keeping render pure, choosing where
state lives, drawing Server/Client Component boundaries correctly, and composing components
without reaching for inheritance that doesn't exist in this model.

## Render is a pure function of props and state

Derive values during render instead of syncing them into their own state slot.

```tsx
// Bad — derived state stored separately, desyncs, costs an extra render
function Cart({ items }: { items: CartItem[] }) {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    setTotal(items.reduce((sum, i) => sum + i.price * i.qty, 0));
  }, [items]);
  return <span>{formatMoney(total)}</span>;
}

// Good — derive during render
function Cart({ items }: { items: CartItem[] }) {
  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  return <span>{formatMoney(total)}</span>;
}
```

Side effects (mutations, network calls, subscriptions) belong in event handlers or `useEffect`
— never inline in the render body. Composition (via `children`, render props, or component
props) replaces inheritance, which React has no model for.

## Hooks discipline

- Call hooks at the top level only — never inside a condition, loop, or nested function.
- Every subscription, interval, or listener registered in `useEffect` gets a cleanup function.
- When new state depends on old state, use the functional updater: `setX(prev => prev + 1)`.
- Default to not memoizing. Add `useMemo`/`useCallback` only once a profiler or a broken
  dependency chain proves it's needed — premature memoization is itself overhead.
- Extract a custom hook only once the same hook sequence appears in two or more components.

## Where should state live?

```
Used by one component?
  -> useState inside it

Used by parent + a few descendants?
  -> lift to nearest common ancestor

Used across distant branches AND read infrequently (theme, auth, locale)?
  -> React Context

High-frequency updates shared across the tree?
  -> external store (Zustand, Jotai, Redux Toolkit)

Derived from a server?
  -> server-state library (TanStack Query, SWR, RSC fetch)
```

Most pages need neither Context nor a global store. Resist introducing either until repeated
prop-lifting actually hurts.

## Server and Client Components

```tsx
// Server Component — default, async, ships no JS of its own
export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findUnique({ where: { id: params.id } });
  if (!product) notFound();
  return <ProductView product={product} />;
}

// Client Component — opt in with "use client"
"use client";
export function AddToCartButton({ productId }: { productId: string }) {
  const [pending, startTransition] = useTransition();
  return (
    <button disabled={pending} onClick={() => startTransition(() => addToCart(productId))}>
      {pending ? "Adding..." : "Add to cart"}
    </button>
  );
}
```

Rules at the boundary:

- Server -> Client: pass only serializable props or `children`.
- Client -> Server: invoke Server Actions via `<form action={...}>` or imperatively from event
  handlers.
- Never `import` a Server Component from inside a Client Component's file — compose them via
  `children` from a shared parent instead.

## Suspense and error boundaries

```tsx
<ErrorBoundary fallback={<ErrorView />}>
  <Suspense fallback={<UserSkeleton />}>
    <UserDetail id={id} />
  </Suspense>
</ErrorBoundary>
```

Place `Suspense` boundaries close to the data that's loading, not at the route root, so the
page can progressively reveal content. `ErrorBoundary` remains a class-only API in React;
`react-error-boundary` gives a hook-friendly wrapper. A boundary catches errors thrown during
render, lifecycle methods, and constructors of its children — it does NOT catch errors in
event handlers or async callbacks; those need their own try/catch.

## Forms

Prefer React 19 form actions for new code:

```tsx
// actions/update-user.ts — server actions live in their own "use server" module.
// Two rules this example exists to demonstrate: an inline "use server" function inside a
// "use client" file does not compile (inline directives are valid only in Server Components),
// and a "use server" module may export ONLY async functions — so shared state/types live
// with the client component, not here.
"use server";

type FormState = { error: string | null };

export async function updateUserAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const parsed = UserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: "Invalid input" };
  await db.user.update({ where: { id: parsed.data.id }, data: parsed.data });
  return { error: null };
}
```

```tsx
// user-form.tsx — the client component imports the action and owns the initial state.
"use client";
import { useActionState } from "react";
import { updateUserAction } from "./actions/update-user";

const initial = { error: null as string | null };

export function UserForm() {
  const [state, formAction, pending] = useActionState(updateUserAction, initial);
  return (
    <form action={formAction}>
      <input name="name" required />
      <button type="submit" disabled={pending}>Save</button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

Use controlled inputs when the value drives other UI, formats on every keystroke, or needs
real-time validation. For multi-step forms, dynamic field arrays, or cross-field validation,
reach for React Hook Form or TanStack Form — rolling your own state machine past trivial
complexity is a maintenance trap.

## Data fetching

| Need | Tool |
|---|---|
| Per-request data in Next.js App Router | RSC `await fetch()` |
| Client-side cache + mutations + invalidation | TanStack Query |
| Lightweight client cache + revalidation | SWR |
| Real-time subscriptions | Server-Sent Events, WebSockets, or the library's subscription API |
| One-off fire-and-forget | `fetch()` in an event handler |

Avoid `useEffect` + `fetch` for application data — it has no cache, no retry, no Suspense
integration, and races itself on rapid prop changes.

## Composition recipes

```tsx
// Slot via children
<Layout><Header /><Main>{content}</Main></Layout>

// Named slots
<Page header={<Nav />} sidebar={<Filters />}><Results /></Page>

// Compound components — shared state via Context
<Tabs defaultValue="profile">
  <Tabs.List>
    <Tabs.Trigger value="profile">Profile</Tabs.Trigger>
    <Tabs.Trigger value="settings">Settings</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="profile"><Profile /></Tabs.Panel>
  <Tabs.Panel value="settings"><Settings /></Tabs.Panel>
</Tabs>
```

Render props / function-as-child are useful when the parent must pass a runtime value into
the rendered output (`<DataLoader id={id}>{({ data, isLoading }) => ...}</DataLoader>`), but a
hook returning the same shape (`useData(id)`) is usually cleaner in modern code.

## `React.memo` — when it actually helps

Wrap a component only when all three hold: it re-renders often, its props are usually
unchanged between renders, and its render is measurably expensive. `React.memo` adds an
equality check on every render — pure overhead when props differ most of the time.

Beyond memoization: lift state down rather than up where possible; split Context by concern so
a `themeContext` change doesn't re-render auth consumers; give lists stable `key`s (a database
id, never array index); virtualize lists once visible row count passes roughly 50 with
non-trivial row content.

## Accessibility-first composition

Reach for semantic HTML (`<button>`, `<a>`, `<nav>`, `<main>`) before `role` attributes. Every
interactive element must be keyboard-reachable. Inputs need a real label (`<label htmlFor>` or
`aria-label` when visually labeled only by an icon). Manage focus explicitly on route changes
and modal open/close. Run `axe` assertions in component tests — see `zeno-react-testing`. For
the full WCAG criteria and cross-platform mapping, see `zeno-accessibility`.

## Custom hook example — debounced search

```tsx
function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function SearchBox() {
  const [query, setQuery] = useState("");
  const debounced = useDebounce(query, 300);
  const { data } = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => searchApi(debounced),
    enabled: debounced.length > 0,
  });
  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <Results items={data ?? []} />
    </>
  );
}
```

## Optimistic UI with `useOptimistic`

```tsx
"use client";
import { useOptimistic } from "react";

export function MessageList({ messages }: { messages: Message[] }) {
  const [optimistic, addOptimistic] = useOptimistic(
    messages,
    (state, newMessage: Message) => [...state, newMessage],
  );

  async function send(formData: FormData) {
    const text = String(formData.get("text"));
    addOptimistic({ id: "pending", text, sender: "me" });
    await saveMessage(text);
  }

  return (
    <>
      <ul>{optimistic.map((m) => <li key={m.id}>{m.text}</li>)}</ul>
      <form action={send}>
        <input name="text" />
        <button type="submit">Send</button>
      </form>
    </>
  );
}
```

This skill is router-agnostic — the patterns above hold across React Router, TanStack Router,
Next.js App Router, and Remix. Router-specific concerns (loaders, actions, nested layouts)
follow that router's own documentation. For the performance-tuned variant of these rules, see
`zeno-react-performance`; for testing them, see `zeno-react-testing`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Derived state synced via `useEffect` | Compute the value inline during render |
| Conditional or nested hook calls | Keep every hook call unconditional and top-level |
| Memoizing everything by default | Memoize only after a profiler shows it's needed |
| Importing a Server Component into a Client Component file | Compose them via `children` from a shared parent |
| `useEffect` + `fetch` for application data | TanStack Query, SWR, or RSC `await fetch()` |
| Defining a component inside another component's body | Hoist it — an inline definition creates a new type every render |
| Array index used as list `key` | A stable identifier such as a database id |
| Rolling a hand-built state machine for a complex form | React Hook Form or TanStack Form |

## Pre-flight checklist — run before delivering any React component or hook

- [ ] Render stays a pure function of props/state — no derived state synced via `useEffect`
- [ ] All hooks are called unconditionally at the top level, with cleanup for every subscription
- [ ] State lives at the location the decision tree above indicates, not reflexively in Context
- [ ] Server/Client boundaries pass only serializable props; no cross-boundary imports
- [ ] Suspense and error boundaries sit close to the data, and event-handler errors are caught explicitly
- [ ] Lists use stable keys and are virtualized past roughly 50 non-trivial rows
- [ ] Every interactive element is reachable by keyboard and has an accessible name
