---
description: Analyze coverage, identify gaps, and generate missing tests toward the target threshold.
---

# /test-coverage

Analyzes current test coverage, finds the gaps, and writes the missing tests needed to clear an 80%+ threshold.

## Step 1 — detect the test framework

| Indicator | Coverage command |
|-----------|-----------------|
| `jest.config.*` or `package.json` jest | `npx jest --coverage --coverageReporters=json-summary` |
| `vitest.config.*` | `npx vitest run --coverage` |
| `pytest.ini` / `pyproject.toml` pytest | `pytest --cov=src --cov-report=json` |
| `Cargo.toml` | `cargo llvm-cov --json` |
| `pom.xml` with JaCoCo | `mvn test jacoco:report` |
| `go.mod` | `go test -coverprofile=coverage.out ./...` |

## Step 2 — read the coverage report

1. Run the coverage command for the detected framework.
2. Parse its output (JSON summary, or terminal output if that's all that's available).
3. List every file **under 80% coverage**, worst first.
4. For each, note:
   - functions/methods with no test at all
   - missing branch coverage (if/else, switch, error paths)
   - dead code inflating the denominator

## Step 3 — write the missing tests

Work through under-covered files in this priority order:

1. **Happy path** — core functionality with valid inputs
2. **Error handling** — invalid inputs, missing data, network failures
3. **Edge cases** — empty arrays, null/undefined, boundary values (0, -1, MAX_INT)
4. **Branch coverage** — every if/else, switch case, ternary

### How the tests should be written

- Place a new test file next to its source (`foo.ts` → `foo.test.ts`, or whatever the project already does)
- Match the project's existing test style — import conventions, assertion library, mocking approach
- Mock external dependencies (database, APIs, filesystem)
- Keep each test independent — no shared mutable state between tests
- Name tests for what they assert: `test_create_user_with_duplicate_email_returns_409`

## Step 4 — verify

1. Run the full suite — everything must pass, not just the new tests.
2. Re-run coverage and confirm it actually improved.
3. Still under 80%? Go back to Step 3 for what's left.

## Step 5 — report the delta

```
Coverage Report
──────────────────────────────
File                   Before  After
src/services/auth.ts   45%     88%
src/utils/validation.ts 32%    82%
──────────────────────────────
Overall:               67%     84%  PASS:
```

## Where to focus

- Functions with heavy branching (high cyclomatic complexity)
- Error handlers and catch blocks
- Utility functions used all over the codebase
- API endpoint handlers, request through to response
- Edge cases: null, undefined, empty string, empty array, zero, negative numbers
