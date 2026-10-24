---
description: Fix React build failures (Vite, webpack, Next.js, CRA, Parcel, esbuild, Bun) incrementally — JSX/TSX compile errors, hydration mismatches, server/client component boundary failures, missing types. Invokes the zeno-react-build-resolver agent for minimal, surgical fixes.
---

# /react-build

Delegates to the **zeno-react-build-resolver** agent to drive a broken React build back to green,
one minimal fix at a time. The diagnostics playbook, error/fix catalog, and worked examples live
in that agent's contract (`agents/zeno-react-build-resolver.md`) — deliberately not duplicated
here, so the command and the agent cannot drift apart.

## What it does

1. **Identify the build system** — Vite, webpack, Next.js, CRA, Parcel, esbuild, or Bun.
2. **Run the build** using the project's own build script.
3. **Group the errors** by layer — TypeScript, bundler config, runtime, hydration.
4. **Fix one at a time**, re-running the build after each change to confirm progress.
5. **Summarize** what changed and what, if anything, is still outstanding.

## When to reach for it

- `npm run build` (or the pnpm/yarn/bun equivalent) is red.
- JSX/TSX stops compiling after a TypeScript or React bump.
- Next.js throws a hydration mismatch at runtime.
- A Server/Client Component boundary breaks under App Router.
- Right after upgrading `react`, `react-dom`, `@types/react`, or the bundler.
- "Module not found" or missing-type errors that involve React.

## Scope

This command owns React-specific build/bundler/runtime-hydration failures. Plain TypeScript type
errors with no React involvement belong to the generic `/build-fix` instead.

## Order of operations

1. Compile errors first — nothing else matters until the code builds.
2. Hydration errors second — these affect production correctness.
3. Bundler config third — restore plugin/loader correctness.
4. One fix at a time, each one verified before moving to the next.
5. Minimal diffs — no `// @ts-ignore` without an explanation attached.
6. Re-run the build after every fix so new errors surface immediately.

## When it stops

The agent halts and reports rather than continuing when:

- The same error survives 3 fix attempts.
- A fix produces more errors than it removed.
- The real fix requires an architectural change beyond build resolution (e.g. redesigning the RSC
  boundary).
- The bundler version doesn't support the installed React major at all.

## Output contract

A summary listing: build system detected, each error fixed (file + one-line cause + fix), the
final build status with the real command output, and anything intentionally left outstanding.

## Related

- Agent: `agents/zeno-react-build-resolver.md` (owns the playbook)
- Commands: `/react-test` (tests once green), `/react-review` (quality once green),
  `/build-fix` (generic non-React builds)
- Skills: `skills/zeno-stack/zeno-react-patterns/`, `skills/zeno-stack/zeno-accessibility/`;
  `zeno-verify` for the full verification loop
