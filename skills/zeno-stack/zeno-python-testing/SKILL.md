---
name: zeno-python-testing
description: >
  Python testing with pytest — the RED/GREEN/REFACTOR TDD cycle, fixture scopes and
  parametrization, mocking and patching (including async), markers and test selection,
  coverage requirements, and test suite organization. Use when writing new Python
  functionality test-first, designing a pytest fixture or fixture hierarchy, mocking an
  external dependency, or reviewing Python test coverage. Trigger on: "write a pytest test",
  "TDD this in Python", "pytest fixture", "mock this function", "parametrize this test",
  "Python test coverage", "conftest.py", "red green refactor", or any request to write or
  review Python test code.
---

# Python Testing Patterns

pytest-based testing discipline for Python: write the failing test first, then the minimal
code to pass it, then refactor with the safety net in place.

## The TDD Cycle — RED, GREEN, REFACTOR

This is the authoritative cycle definition for Python test-first work in this repo.

1. **RED** — write a test for the desired behavior and confirm it fails for the *right*
   reason.
2. **GREEN** — write the minimal implementation that makes it pass. Resist adding anything
   the test doesn't require yet.
3. **REFACTOR** — improve the implementation (naming, duplication, structure) with the test
   suite green throughout, committing to no behavior change.

```python
# RED — this fails because add() doesn't exist yet
def test_add_numbers():
    assert add(2, 3) == 5

# GREEN — minimal implementation
def add(a, b):
    return a + b

# REFACTOR — only if there's something worth improving; a one-liner like this may need none
```

A RED result only counts if it is caused by the missing/buggy behavior under test, not by an
unrelated problem:

- The test file **compiles/imports successfully** and the new test is **actually executed** —
  a test that was written but never run is not RED, it's unverified.
- The failure traces to the intended gap (`AttributeError: module has no attribute 'add'`,
  a wrong assertion value, etc.) — not to a typo in test setup, a missing fixture, or an
  unrelated import error elsewhere in the suite.
- Don't edit production code until this genuine RED state is confirmed; skipping straight to
  GREEN without a verified RED means the test was never proven capable of catching the bug.

Rerun the exact same test after the fix to confirm GREEN — not just "tests pass" in general,
but this specific test, so the RED→GREEN pair is a real proof, not a coincidence.

## Coverage Requirements

- Target 80%+ overall; critical paths (auth, payments, data mutation) at 100%.
- Coverage is a floor for *finding untested code*, not a target to game with assertion-free
  tests — a covered line that no assertion depends on proves nothing.

```bash
pytest --cov=mypackage --cov-report=term-missing --cov-report=html
```

## pytest Fundamentals

```python
import pytest

def test_string_uppercase():
    assert "hello".upper() == "HELLO"

# Exception testing — the pytest.raises pattern, not try/except in the test body
with pytest.raises(ValueError, match="invalid input"):
    raise ValueError("invalid input provided")

with pytest.raises(ValueError) as exc_info:
    raise ValueError("error message")
assert str(exc_info.value) == "error message"
```

Prefer `is None` / `is True` for identity checks (`assert result is None`), `==` for value
equality, and `isinstance(result, str)` for type checks — see `code-standards/python` for why.

## Fixtures

```python
@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 30}

# Setup/teardown via yield
@pytest.fixture
def database():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

# Scope controls how often the fixture re-runs
@pytest.fixture(scope="module")   # once per test module
def module_db(): ...

@pytest.fixture(scope="session")  # once per test run — for genuinely expensive setup
def shared_resource(): ...

# autouse — runs for every test in scope without being requested by name
@pytest.fixture(autouse=True)
def reset_config():
    Config.reset()
    yield
    Config.cleanup()
```

Put fixtures shared across files in `tests/conftest.py`; keep fixtures local to one file when
only that file needs them — a fixture visible everywhere but used once is a discovery cost for
every other test file.

## Parametrization

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
], ids=["lowercase", "another-word"])
def test_uppercase(input, expected):
    assert input.upper() == expected

# Parametrized fixtures run the whole test once per param value
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def db(request):
    return make_database(request.param)
```

Use `ids=` once the parameter values themselves aren't self-explanatory in test output.

## Markers and Test Selection

```python
@pytest.mark.slow
def test_slow_operation(): ...

@pytest.mark.integration
def test_api_integration(): ...
```

```bash
pytest -m "not slow"              # skip slow tests during inner-loop development
pytest -m "integration or slow"
```

Register custom markers in `pytest.ini`/`pyproject.toml` under `markers = [...]` — an
unregistered marker used with `--strict-markers` fails the run, which is the point: it forces
every marker to be a deliberate, documented category.

## Mocking and Patching

```python
from unittest.mock import patch

@patch("mypackage.external_api_call")
def test_with_mock(api_call_mock):
    api_call_mock.return_value = {"status": "success"}
    result = my_function()
    api_call_mock.assert_called_once()
    assert result["status"] == "success"

# side_effect raises instead of returning — for testing error paths
@patch("mypackage.api_call")
def test_api_error_handling(api_call_mock):
    api_call_mock.side_effect = ConnectionError("Network error")
    with pytest.raises(ConnectionError):
        api_call()

# autospec catches API misuse the plain Mock would silently accept
@patch("mypackage.DBConnection", autospec=True)
def test_autospec(db_mock):
    db_mock.return_value.query("SELECT * FROM users")
    db_mock.assert_called_once()
```

```python
# Async mocking — pytest-asyncio + assert_awaited*
@pytest.mark.asyncio
@patch("mypackage.async_api_call")
async def test_async_mock(api_call_mock):
    api_call_mock.return_value = {"status": "ok"}
    result = await my_async_function()
    api_call_mock.assert_awaited_once()
    assert result["status"] == "ok"
```

Mock at the boundary your code owns (the function that calls the external API), not deep
inside a third-party library — mocking a library internal breaks the moment that library's
implementation changes, even though its public contract didn't.

## Test Organization

```
tests/
├── conftest.py          # shared fixtures
├── unit/                # pure logic, fully mocked dependencies
├── integration/         # real DB/API interaction, still no network to prod
└── e2e/                 # full user flow — see zeno-e2e-testing for browser-driven flows
```

```python
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UserService()

    def test_create_user(self):
        user = self.service.create_user("Alice")
        assert user.name == "Alice"
```

Group related tests in a class only when they share setup via an autouse fixture — a class
with no shared state is just indentation.

## pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--cov=mypackage", "--cov-report=term-missing"]
markers = ["slow: marks tests as slow", "integration: marks tests as integration tests"]
```

```bash
pytest                      # run everything
pytest tests/test_utils.py::test_function   # one test
pytest -x                   # stop on first failure
pytest --lf                 # rerun only what failed last time
pytest -k "test_user"       # pattern match by name
pytest --pdb                # drop into debugger on failure
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Writing implementation before a failing test exists | RED first — verify the test fails for the right reason before writing any implementation |
| A test that was written but never actually run/verified failing | Run it; an unexecuted test is not RED, it's unverified |
| Asserting on internal state (`obj._cache`, `component.state.count`) | Assert on observable behavior/output |
| Bare `except:` inside a test to suppress a flaky failure | Fix the flake or `pytest.raises` the specific exception — never swallow |
| Tests that depend on execution order or shared mutable state | Each test creates its own data; no cross-test dependency |
| Deep-mocking a third-party library's internals | Mock at the boundary your own code calls |
| Coverage-only tests with no meaningful assertion | Every test asserts on behavior the change is meant to guarantee |
| One giant fixture used everywhere "just in case" | Scope fixtures to what actually needs them; keep single-file fixtures local |

## Pre-flight checklist — run before delivering any Python test change

- [ ] New behavior was proven RED (test fails for the intended reason) before implementation
- [ ] The same test was rerun and confirmed GREEN after the minimal fix
- [ ] Refactor step, if any, kept the full suite green throughout
- [ ] Coverage meets the 80%+ target, 100% on critical paths, with no assertion-free padding
- [ ] Fixtures are scoped appropriately (function/module/session) and shared ones live in `conftest.py`
- [ ] Mocks target the boundary the code under test actually calls, not library internals
- [ ] Async code is tested with `pytest.mark.asyncio` and `assert_awaited*`, not sync mock assertions
- [ ] Markers used are registered; `--strict-markers` passes
- [ ] Tests are independent — no ordering assumptions, no shared mutable state
