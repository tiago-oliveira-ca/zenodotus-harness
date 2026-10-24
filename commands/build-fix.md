---
description: Detect the project build system and incrementally fix build/type errors with minimal safe changes.
---

# /build-fix

Drives the build to green one error at a time, using the smallest edit that resolves each one.
Never a wholesale rewrite — this command exists for the case where the build is broken and needs
fixing, not for improving the code around it.

## Step 1 — identify the build system

Pick the command from whichever project file is present:

| Project file | Build command |
|---|---|
| `package.json` with a `build` script | `npm run build` or `pnpm build` |
| `tsconfig.json` only (no bundler) | `npx tsc --noEmit` |
| `Cargo.toml` | `cargo build 2>&1` |
| `pom.xml` | `mvn compile` |
| `build.gradle` | `./gradlew compileJava` |
| `go.mod` | `go build ./...` |
| `pyproject.toml` | `python -m compileall -q .` or `mypy .` |

## Step 2 — collect and order the errors

1. Run the build command and capture stderr.
2. Group the output by file.
3. Order groups so import/type errors are addressed before the logic errors that depend on them.
4. Note the total error count so progress is visible as the loop runs.

## Step 3 — fix loop

Work through the errors one at a time:

1. Read enough surrounding context (roughly 10 lines around the reported line) to understand it.
2. Diagnose the actual cause — missing import, type mismatch, syntax slip — rather than guessing.
3. Apply the narrowest edit that resolves it.
4. Re-run the build to confirm the error cleared and nothing new appeared.
5. Move to the next error.

## Step 4 — when to stop and ask

Pause and check in with the user rather than continuing if:

- A fix produces **more errors than it removed**.
- The **same error survives three fix attempts** — that's a signal of a deeper problem, not a
  build syntax issue.
- Resolving it would require an **architectural change**, which is out of scope for this command.
- The errors trace back to **missing dependencies** and need an install step (`npm install`,
  `cargo add`, etc.) rather than a code change.

## Step 5 — report

Summarize the run:

- Which errors were fixed, with file paths.
- Which remain, if any.
- Any newly introduced errors (this should be zero).
- Suggested next steps for anything left unresolved.

## Recovery playbook

Common failure shapes and how to approach them:

| Situation | Approach |
|---|---|
| Missing module/import | Confirm whether the package is installed; suggest the install command. |
| Type mismatch | Read both sides' type definitions and fix toward the narrower type. |
| Circular dependency | Trace the cycle via the import graph; suggest where to extract a shared module. |
| Version conflict | Check the constraint in `package.json` / `Cargo.toml`. |
| Build tool misconfiguration | Read the config and compare it against a known-working default. |

Stay on one error at a time, and favor the minimal diff over a broader cleanup — that belongs to
`/refactor-clean`, not this command.
