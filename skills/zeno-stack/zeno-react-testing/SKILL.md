---
name: zeno-react-testing
description: >
  React component testing with React Testing Library, Vitest/Jest, MSW network mocking,
  axe accessibility assertions, custom hook testing, and the decision boundary between
  component tests and Playwright/Cypress end-to-end runs. Use when writing or fixing tests
  for React components, hooks, or pages. Trigger on: "write a test for this component", "test
  this hook", "mock this API call in a test", "why is this test flaky", "RTL vs E2E", "test
  coverage for React", "add accessibility assertions", "React Testing Library".
---

# React Testing

Behavior-focused testing for React components and hooks: what the user sees and does, not how
the component is implemented internally.

## Core principle

A good test renders the component with the same providers it has in production, interacts via
accessible queries (role, label) and `userEvent`, and asserts visible output or an observable
side effect (a callback fired, a request sent). It never inspects component state, the props
passed to children, which hooks ran, or the number of renders.

## Runner and library choice

| Runner | When |
|---|---|
| Vitest | Vite, Remix, modern setups — faster, native ESM, Jest-compatible API |
| Jest | Next.js, CRA, established repos — still the default for many |
| Playwright Component Testing | JSDOM lacks a feature the component genuinely needs |
| Cypress Component Testing | Real browser, Cypress already in the stack |

Pick one runner. Running RTL+Vitest alongside Playwright CT in the same repo needs a clear lane
split or it becomes two competing test suites.

## Query priority

Use RTL's queries top-down — reach for `getByTestId` only as a last resort:

```tsx
screen.getByRole("button", { name: /save/i });   // best
screen.getByLabelText("Email");                   // fine for inputs
screen.getByTestId("save-btn");                   // escape hatch
```

`getBy*` throws when nothing matches; `queryBy*` returns `null` (use to assert absence);
`findBy*` is async and returns a Promise (use for elements that appear after async work).

## A worked example: Button component

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

This covers the three things a presentational component almost always needs proven: it
renders its content, it fires the callback it promises, and it respects the prop that changes
its interactive state. `fireEvent` dispatches a single synthetic event and is fine for a
simple click like this; for anything that simulates a real interaction sequence (typing, tab
order, multi-step gestures), reach for `userEvent` instead — see below.

## User interaction with `userEvent`

```tsx
import userEvent from "@testing-library/user-event";

test("submits the form", async () => {
  const user = userEvent.setup();
  const onSubmit = vi.fn();
  render(<UserForm onSubmit={onSubmit} />);

  await user.type(screen.getByLabelText("Email"), "user@example.com");
  await user.click(screen.getByRole("button", { name: /save/i }));

  expect(onSubmit).toHaveBeenCalledWith({ email: "user@example.com" });
});
```

Always `await` `userEvent` calls. Call `userEvent.setup()` once per test and reuse the
returned `user`. `userEvent` simulates a realistic browser event sequence (focus, keydown,
input, keyup); `fireEvent` dispatches one synthetic event — prefer `userEvent` whenever the
interaction is more than a single click.

## Async patterns

```tsx
expect(await screen.findByText("Loaded")).toBeInTheDocument();   // appears after async work
await waitFor(() => expect(saveSpy).toHaveBeenCalled());          // side-effect assertion
await waitForElementToBeRemoved(() => screen.queryByText("Loading")); // disappears
```

Never pair `setTimeout` with an assertion — it's flaky by construction. Use the matchers above.

## Network mocking with MSW

Mock Service Worker intercepts at the network layer, so the component, its hooks, and the
fetch library all run exactly as they do in production.

```ts
// test/setup.ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/users/:id", ({ params }) => HttpResponse.json({ id: params.id, name: "Alice" })),
  http.post("/api/users", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: "new-id", ...body }, { status: 201 });
  }),
];

export const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

`onUnhandledRequest: "error"` makes any unmocked request fail the test loudly instead of
passing silently. Override a handler per test with `server.use(...)` — e.g. return a 500 to
test the error path.

## Provider wrapping

Wrap providers once in a shared helper so every test file imports the same setup:

```tsx
// test-utils.tsx
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function renderWithProviders(ui: React.ReactElement, options?: RenderOptions) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={lightTheme}><MemoryRouter>{ui}</MemoryRouter></ThemeProvider>
    </QueryClientProvider>,
    options,
  );
}
export * from "@testing-library/react";
```

## Custom hook testing

```tsx
import { renderHook, act } from "@testing-library/react";

test("useCounter increments and decrements", () => {
  const { result } = renderHook(() => useCounter(0));
  expect(result.current.count).toBe(0);
  act(() => result.current.increment());
  expect(result.current.count).toBe(1);
});

test("useUser fetches user data", async () => {
  // Instantiate QueryClient ONCE per test, outside the wrapper closure — creating it
  // inside the wrapper resets cache state on every render and produces flaky tests.
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const { result } = renderHook(() => useUser("1"), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toEqual({ id: "1", name: "Alice" });
});
```

Wrap state-changing calls in `act`; test only through the hook's public API; pass a `wrapper`
for any hook that consumes context.

## Accessibility assertions

```tsx
import { axe, toHaveNoViolations } from "jest-axe"; // or vitest-axe
expect.extend(toHaveNoViolations);

test("UserCard has no a11y violations", async () => {
  const { container } = render(<UserCard user={mockUser} />);
  expect(await axe(container)).toHaveNoViolations();
});
```

Run `axe` on every interactive component test. It catches missing form labels, invalid ARIA
usage, missing image alt text, and heading-order violations — but only inline-style contrast
issues, since JSDOM has no real CSS engine; visual contrast checks belong in Playwright. See
`zeno-accessibility` for the broader audit playbook this feeds into.

## When not to use snapshot tests

Snapshots of rendered output break on every styling change, get rubber-stamped in review, and
assert implementation detail (DOM structure) rather than behavior. Acceptable uses: pure data
serialization functions (`formatInvoice(invoice) -> stable string`) or generated config output.
For real visual regression, use Playwright/Cypress screenshots or a service like
Percy/Chromatic — actual pixel diffs, not DOM strings.

## When to reach for Playwright or Cypress instead

JSDOM cannot render real layout (flexbox/grid/viewport queries), run native CSS
transitions/animation, test scrolling/drag-and-drop/clipboard paste, handle iframes or
cross-origin flows, or exercise real network with full devtools. Decision boundary:

- A hook, a presentational component, or a form with logic -> RTL
- A component whose layout matters or that touches browser APIs JSDOM lacks -> Playwright CT
- A full user flow across multiple pages -> Playwright/Cypress E2E (see `zeno-e2e-testing`)

## Coverage targets

| Layer | Target |
|---|---|
| Pure utilities | >=90% |
| Custom hooks | >=85% |
| Presentational components | >=80% — behavior, not line count |
| Container components | >=70% — golden paths + error states |
| Pages | E2E covers the flow; smoke test only here |

```ts
// vitest.config.ts
test: {
  coverage: {
    provider: "v8",
    reporter: ["text", "html", "lcov"],
    thresholds: { lines: 80, functions: 80, branches: 70, statements: 80 },
  },
}
```

## Test-first workflow

RED (write a failing test for the next requirement) -> GREEN (minimal component code to pass)
-> REFACTOR (clean up with tests staying green) -> REPEAT. For a new component: define its
prop signature, write the simplest test first, confirm it fails for the right reason,
implement just enough to pass, add the next case, and refactor once a third similar test
reveals a pattern worth extracting.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `container.querySelector(...)` | Accessible queries (`getByRole`, `getByLabelText`) |
| Asserting on render count | Assert on visible output or fired callbacks |
| `jest.mock("react", ...)` | Never mock React — refactor the component instead |
| Mocking every child component by default | Mock only children with heavy side effects; test the integration otherwise |
| Ignoring `act()` warnings | Fix them — they signal a real bug (state update after unmount, missing async wrap) |
| Sharing mutable state across tests | Each test sets up and tears down its own data |
| Snapshotting rendered component output | Snapshot pure serialization functions only; use Playwright/Percy for visual diffs |
| `setTimeout` + assertion | `findBy*` / `waitFor` / `waitForElementToBeRemoved` |

## Pre-flight checklist — run before delivering any React component or hook test

- [ ] Queries follow the accessible-first priority order; `getByTestId` used only as a last resort
- [ ] Interactions use `userEvent` (awaited) except for simple single-event clicks
- [ ] Network calls are mocked at the MSW layer with `onUnhandledRequest: "error"`
- [ ] Async assertions use `findBy*`/`waitFor`, never `setTimeout`
- [ ] An `axe` assertion covers every new interactive component
- [ ] No test asserts on internal state, render count, or DOM structure irrelevant to users
- [ ] Coverage meets the layer's target before calling the test suite done
