---
description: Enforce TDD workflow for React. Write React Testing Library tests first (behavior-focused, accessibility-first), then implement components. Detects Vitest or Jest and verifies coverage targets.
---

# /react-test

Enforces test-first development for React with React Testing Library, on top of whichever runner
the project already uses — Vitest or Jest, detected automatically.

## What it does

1. **Define the component's signature** — scaffold the component, its prop type, and its exports.
2. **Write behavior tests first** — RTL queries (role-first), `userEvent`, MSW for network — RED.
3. **Run the tests** and confirm they fail for the right reason.
4. **Implement the minimum** needed to pass — GREEN.
5. **Refactor** while keeping the tests green.
6. **Check coverage** against the targets below.

## When to reach for it

- Implementing a new React component or custom hook.
- Adding coverage to a component that has none.
- Fixing a bug — write the failing reproduction test first.
- Building forms, state machines, or accessibility-sensitive UI.
- Getting onboarded to the RTL + Vitest/Jest workflow.

## The cycle

```
RED      -> Write failing test for the next behavior
GREEN    -> Implement minimal component code to pass
REFACTOR -> Improve component, tests stay green
REPEAT   -> Next behavior
```

## Runner detection

```bash
test -f vitest.config.ts -o -f vitest.config.js -o -f vite.config.ts   # Vitest
grep -l '"jest"' package.json                                          # Jest
```

Default to Vitest on new Vite-based projects; keep an existing Jest setup as-is.

## Test patterns, coverage targets, anti-patterns

The RTL pattern catalog (query priority, awaited `userEvent`, MSW wiring, provider wrappers), the coverage targets, and the anti-pattern list are owned by the lane's skills — `zeno-stack/zeno-react-testing` (test code) with the RED/GREEN discipline from `zeno-workflow/zeno-tdd` — and are deliberately not duplicated here. Load `zeno-react-testing` before writing any test this command drives.

## Test commands

```bash
# Vitest
vitest                              # watch
vitest run                          # one-shot
vitest run --coverage               # with coverage
vitest run path/to/file.test.tsx    # single file

# Jest
jest --watch
jest --coverage
jest path/to/file.test.tsx

# CI mode
CI=true vitest run --coverage
```

## Related commands

- `/react-build` — fix build errors before running tests.
- `/react-review` — review after implementation.
- `zeno-verify` skill — the full verification loop.

## Related

- Skills: `skills/zeno-stack/zeno-react-testing/`, `skills/zeno-workflow/zeno-tdd/`, `skills/zeno-stack/zeno-accessibility/`, `skills/zeno-stack/zeno-e2e-testing/`
- Agents: `zeno-react-reviewer` (reviews test quality), `zeno-tdd-guide` (enforces the TDD process)
