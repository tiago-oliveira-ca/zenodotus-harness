---
description: Comprehensive React/JSX code review for hook correctness, render performance, server/client component boundaries, accessibility, and React-specific security. Invokes the zeno-react-reviewer agent (and zeno-typescript-reviewer alongside on TSX/JSX changes).
---

# /react-review

Delegates to the **zeno-react-reviewer** agent for React-specific review. On a PR that touches
`.tsx`/`.jsx` files, run `zeno-typescript-reviewer` alongside it — the two lanes are disjoint by
design, not competing.

## What it does

1. **Find the React surface** — modified `.tsx`/`.jsx` files, plus any React-touching `.ts`/`.js`,
   via `git diff`.
2. **Lint** with `eslint-plugin-react-hooks` and `eslint-plugin-jsx-a11y`.
3. **Typecheck** via `tsc --noEmit` or the project's canonical typecheck command.
4. **Review only the React lanes** — hook rules, RSC boundaries, accessibility, render
   performance, React-specific security.
5. **Report** issues bucketed CRITICAL / HIGH / MEDIUM.

## When to reach for it

- A PR or commit touches `.tsx`/`.jsx` files.
- After writing or changing React components, custom hooks, or pages.
- Before merging any React code.
- Auditing UI accessibility.
- Reviewing a new hook for rules-of-hooks and dependency correctness.
- Checking a Next.js App Router server/client boundary.

For `.ts`/`.js` changes with no React involved, use `/code-review` (general) or invoke
`zeno-typescript-reviewer` directly instead.

## Scope vs. `/code-review` and the TypeScript reviewer

| Tool | Scope |
|---|---|
| `zeno-react-reviewer` (this command) | Hook rules, JSX, RSC, a11y, React-specific security, render perf |
| `zeno-typescript-reviewer` | Generic TS/JS — `any` abuse, async correctness, Node security |
| `zeno-security-reviewer` | Project-wide security audit |
| `/code-review` | Generic uncommitted-changes or PR review |

On a TSX/JSX PR, run both `zeno-react-reviewer` and `zeno-typescript-reviewer` — their findings
don't overlap.

## Review categories

The full CRITICAL/HIGH/MEDIUM rubric — hook rules, RSC boundaries, a11y, render performance, React-specific security — lives in the `zeno-react-reviewer` agent's contract (deliberately not duplicated here, matching `/python-review`'s pattern, so the command and agent cannot drift).

## Automated checks it runs

```bash
# Lint (required for any meaningful review)
npx eslint . --ext .tsx,.jsx,.ts,.js

# Typecheck (skip cleanly for JS-only projects)
npm run typecheck --if-present
[ -f tsconfig.json ] && tsc --noEmit -p tsconfig.json

# Targeted a11y rules
npx eslint . --rule 'jsx-a11y/alt-text: error' \
              --rule 'jsx-a11y/anchor-is-valid: error' \
              --rule 'jsx-a11y/click-events-have-key-events: error'

# Supply-chain
npm audit
```

If `eslint-plugin-react-hooks` or `eslint-plugin-jsx-a11y` isn't configured, the review flags that
gap as a HIGH config issue and proceeds anyway.

## Approval criteria

| Status | Condition |
|---|---|
| PASS: Approve | No CRITICAL or HIGH issues |
| WARNING: Warning | Only MEDIUM issues (merge with caution) |
| FAIL: Block | CRITICAL or HIGH issues found |

## Fits with

- Run `/react-build` first if the build itself is broken.
- Run `/react-test` to confirm component tests pass.
- Run `/react-review` before merging.
- Use `/code-review` for non-React concerns on the same PR.

## Related

- Agent: `agents/zeno-react-reviewer.md`
- Companion agent: `agents/zeno-typescript-reviewer.md` (run alongside for TSX/JSX PRs)
- Skills: `skills/zeno-stack/zeno-react-patterns/`, `skills/zeno-stack/zeno-react-testing/`, `skills/zeno-stack/zeno-accessibility/`
