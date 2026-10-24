---
name: python
description: >
  Comprehensive Python code standards based on PEP 8, PEP 20, PEP 257, and the Google Python
  Style Guide — the base layer for all Python work; routes to framework standards (FastAPI, DRF,
  Airflow) in `frameworks/` and deeper architecture references. Use whenever writing, reviewing,
  or refactoring Python. Trigger on: "write Python", "Python function", "is this Pythonic",
  "Python best practices", "PEP 8", "Python code review", "FastAPI", "Django REST Framework",
  "DRF", "Airflow", "DAG", "DDD", "clean architecture", "hexagonal architecture", "design
  pattern", or any Python development task.
---

# Python Code Standards

When writing, reviewing, or refactoring Python code, follow these standards (based on
[PEP 8](https://peps.python.org/pep-0008/), [PEP 20](https://peps.python.org/pep-0020/),
[PEP 257](https://peps.python.org/pep-0257/), and the
[Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)).

This is the base layer for all Python code, general or framework-specific; test code itself
belongs to `zeno-stack/zeno-python-testing`. This is one skill:
core Python standards live in this file, framework-specific standards live as plain reference
files in `frameworks/`, and deeper same-language material lives in `references/`. If the task
involves a specific framework, apply this file's standards **plus** the matching framework
reference below — each `frameworks/` file assumes this file's PEP 8/naming/docstring/typing
rules and only covers what's specific to that framework:

| Framework | Reference |
|---|---|
| FastAPI, Pydantic v2, async SQLAlchemy | `frameworks/fastapi.md` |
| Django REST Framework, Django, DRF | `frameworks/django-rest-framework.md` |
| Apache Airflow 3, Astronomer, DAG authoring | `frameworks/airflow.md` |

For deeper, non-framework-specific Python material, load the matching file in `references/`:

| Concern | Reference |
|---|---|
| DDD, Clean/Hexagonal Architecture, SOLID, ports & adapters, design patterns in idiomatic Python | `references/ddd-clean-architecture.md` |
| Strategic DDD (bounded contexts, context mapping, EventStorming), TDD practice, BDD/Gherkin, Kafka event-driven testing | `references/ddd-tdd-bdd-workflow.md` |
| Pythonic structural idioms — EAFP vs LBYL, advanced typing (`Protocol`, `TypeVar`), exception chaining, custom context managers, generators, dataclasses, decorators, concurrency model choice (threads/processes/asyncio), package layout, `__slots__` | `references/pythonic-idioms.md` |

For domain modeling, Clean/Hexagonal Architecture, SOLID applied to Python specifically, or
choosing/rejecting a design pattern or dependency-injection approach, additionally load
`references/ddd-clean-architecture.md` — load it alongside this file (and the framework
reference, if any) whenever the task is architectural, not just stylistic: aggregates, ports
and adapters, a Repository/Unit-of-Work, a composition root, or a "should I use a design
pattern here" question.

For strategic domain design (bounded contexts, context mapping, EventStorming), TDD/BDD
process, or Kafka-specific event-driven testing, additionally load
`references/ddd-tdd-bdd-workflow.md` — load it alongside `references/ddd-clean-architecture.md`,
not instead of it: that file owns tactical patterns (aggregates, repositories, UoW) and the
test pyramid; this one owns strategic design and the TDD/BDD/Kafka-testing methodology built
around those tactical patterns.

---

## 1. The Zen of Python (PEP 20)

These guiding principles should inform every design and coding decision:

```
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
```

---

## 2–4. Layout, Imports, Whitespace — enforced by Ruff, not restated here

Raw PEP 8 mechanics (indentation and continuation-line alignment, blank-line counts, import
ordering, operator spacing, whitespace pet peeves) are mechanically enforced by this skill's own
Ruff configuration in §11 — run it rather than reviewing for these by hand; a rule the formatter
already enforces is not worth a human (or model) pass. The house *choices* layered on top of
plain PEP 8, which Ruff is configured to enforce and which do need stating:

- **Line length: 79 characters** for code (Ruff `line-length = 79`), 72 for docstrings/comments —
  the stricter PEP 8 limit, not the common 88/100 relaxations.
- **4 spaces, never tabs**; hanging indents add a level, closing brackets align with the first
  character of the construct's line.
- **Import groups** stdlib → third-party → local, blank line between groups, one module per
  `import` line, **no wildcard imports** (`from x import *` breaks static tooling), and prefer
  absolute imports; explicit relative imports are acceptable within a package.
- **Module-level dunders** (`__all__`, `__version__`) sit after the module docstring but before
  any imports except `from __future__`.

## 5. Naming Conventions

### 5.1 Summary Table

| Type | Convention | Example |
|---|---|---|
| Module | `lowercase_with_underscores` | `my_module.py` |
| Package | `lowercase` (no underscores) | `mypackage` |
| Class | `CapitalizedWords` (CamelCase) | `MyClass` |
| Exception | `CapitalizedWords` + `Error` suffix | `ConnectionError` |
| Function | `lowercase_with_underscores` | `calculate_total()` |
| Method | `lowercase_with_underscores` | `get_name()` |
| Variable | `lowercase_with_underscores` | `total_count` |
| Constant | `UPPER_CASE_WITH_UNDERSCORES` | `MAX_OVERFLOW` |
| Type Variable | `CapitalizedWords` (short) | `T`, `AnyStr` |

### 5.2 Underscore Conventions

| Pattern | Meaning |
|---|---|
| `_single_leading` | Weak "internal use" indicator; not imported by `from M import *` |
| `single_trailing_` | Used to avoid conflicts with Python keywords (e.g., `class_`) |
| `__double_leading` | Triggers name mangling in classes |
| `__dunder__` | "Magic" attributes/methods; never invent new ones |

### 5.3 Names to Avoid

- **Never** use `l` (el), `O` (oh), or `I` (eye) as single-character variable names.
- Avoid abbreviations that are ambiguous or unfamiliar outside your project.
- Don't include the type in the variable name (e.g., `id_to_name_dict`).
- Always use descriptive names; descriptiveness should be proportional to scope.

### 5.4 Function and Method Arguments

- Always use `self` as the first argument to instance methods.
- Always use `cls` as the first argument to class methods.
- If an argument name clashes with a keyword, append a trailing underscore (`class_`).

---

## 6. Comments

### 6.1 Block Comments

- Indented to the same level as the code they describe.
- Each line starts with `#` followed by a single space.
- Separate paragraphs within a block comment with a line containing only `#`.

### 6.2 Inline Comments

- Use sparingly and only when they add non-obvious context.
- Separate from the statement by at least **two spaces**, starting with `# `.
- Never state the obvious:

```python
# ❌ Wrong
x = x + 1  # Increment x

# ✅ Correct
x = x + 1  # Compensate for border
```

### 6.3 TODO Comments

Format (Google Style):

```python
# TODO(username): Refactor this to use the new Widget class.
# TODO: b/12345678 - Remove this after the migration is complete.
```

---

## 7. Docstrings (PEP 257 + Google Style)

### 7.1 General Rules

- Always use `"""triple double quotes"""`.
- Write docstrings for **all public modules, functions, classes, and methods**.
- The first line is a **summary** ending in a period, question mark, or exclamation point.
- If multi-line, leave a **blank line** after the summary, then add elaboration.
- One-liner docstrings keep closing `"""` on the same line.
- Multi-line docstrings place the closing `"""` on its own line.

### 7.2 One-Line Docstrings

```python
def kos_root():
    """Return the pathname of the KOS root directory."""
    global _kos_root
    if _kos_root:
        return _kos_root
```

### 7.3 Multi-Line Docstrings (Google Style)

```python
def fetch_smalltable_rows(
    table_handle: smalltable.Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """Fetch rows from a Smalltable.

    Retrieve rows pertaining to the given keys from the Table instance
    represented by table_handle. String keys will be UTF-8 encoded.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each table row
            to fetch. String keys will be UTF-8 encoded.
        require_all_keys: If True, only rows with values set for all keys
            will be returned.

    Returns:
        A dict mapping keys to the corresponding table row data fetched.
        Each row is represented as a tuple of strings.

    Raises:
        IOError: An error occurred accessing the smalltable.
    """
```

### 7.4 Class Docstrings

```python
class SampleClass:
    """Summary of class here.

    Longer class information...

    Attributes:
        likes_spam: A boolean indicating if we like SPAM or not.
        eggs: An integer count of the eggs we have laid.
    """

    def __init__(self, likes_spam: bool = False):
        """Initialize SampleClass with preference settings."""
        self.likes_spam = likes_spam
        self.eggs = 0
```

### 7.5 Module Docstrings

Every module should begin with a docstring:

```python
"""A one-line summary of the module, terminated by a period.

Leave one blank line. The rest of this docstring should contain an
overall description of the module or program. Optionally, it may also
contain a brief description of exported classes and functions and/or
usage examples.

Typical usage example:

    foo = ClassFoo()
    bar = foo.function_bar()
"""
```

Cross-cutting doc discipline (when to document, keeping docs in sync with code / drift, driving
Sphinx/`mkdocstrings`): see `documenting-code`. Prefer docstrings with runnable `doctest` examples —
they self-verify and are the cheapest drift guard.

---

## 8. Type Annotations (PEP 484 + Google Style)

### 8.1 General Rules

- **Annotate all public APIs** with type hints.
- Use built-in generics (`list`, `dict`, `tuple`, `set`) instead of imports from `typing` where possible (Python 3.9+).
- Use `X | Y` union syntax instead of `Union[X, Y]` (Python 3.10+).
- Annotating `self` or `cls` is generally unnecessary.
- Don't annotate the return value of `__init__`.

### 8.2 Examples

```python
def greeting(name: str) -> str:
    """Generate a greeting message."""
    return f"Hello, {name}!"

def process_items(items: list[int], threshold: float = 0.5) -> dict[str, int]:
    """Process items above a threshold."""
    return {"above": sum(1 for x in items if x > threshold)}

# For complex signatures, break one parameter per line
def my_method(
    self,
    first_var: int,
    second_var: Foo,
    third_var: Bar | None,
) -> int:
    ...
```

---

## 9. Exception Handling (Google Style)

### 9.1 Rules

- Use built-in exception classes when appropriate (e.g., `ValueError`, `TypeError`).
- Custom exceptions should inherit from an existing exception class and end with `Error`.
- **Never** use bare `except:` or catch `Exception` unless re-raising or creating an isolation point.
- **Minimize** code inside `try/except` blocks.
- Use `finally` for cleanup.
- Do **not** use `assert` for validation of production data—only for internal invariants and tests.

### 9.2 Example

```python
def connect_to_next_port(self, minimum: int) -> int:
    """Connect to the next available port.

    Args:
        minimum: A port value greater or equal to 1024.

    Returns:
        The new minimum port.

    Raises:
        ConnectionError: If no available port is found.
    """
    if minimum < 1024:
        raise ValueError(f"Min. port must be at least 1024, not {minimum}.")
    port = self._find_next_open_port(minimum)
    if port is None:
        raise ConnectionError(
            f"Could not connect to service on port {minimum} or higher."
        )
    return port
```

---

## 10. Programming Recommendations

### 10.1 Comparisons

- Use `is` / `is not` for comparisons with singletons like `None`, never `==` / `!=`:

```python
# ✅ Correct
if foo is not None:
    ...

# ❌ Wrong
if foo != None:
    ...
```

### 10.2 Boolean Checks

- Use implicit truthiness where possible:

```python
# ✅ Correct
if items:
    ...
if not items:
    ...

# ❌ Wrong
if len(items) != 0:
    ...
if items == []:
    ...
```

### 10.3 String Concatenation

- For joining many strings, use `"".join()` instead of `+=` in loops:

```python
# ✅ Correct
result = "".join(items)

# ❌ Wrong (O(n²) in some implementations)
result = ""
for item in items:
    result += item
```

### 10.4 Context Managers

- Use `with` statements for resource management (files, sockets, locks):

```python
# ✅ Correct
with open("file.txt") as f:
    data = f.read()

# ❌ Wrong
f = open("file.txt")
data = f.read()
f.close()
```

### 10.5 Comprehensions & Generators

- Prefer comprehensions for simple cases; avoid for complex logic:

```python
# ✅ Good — simple and readable
squares = [x * x for x in range(10)]

# ❌ Bad — too complex, use a loop instead
result = [
    (x, y, z)
    for x in range(5)
    for y in range(5)
    if x != y
    for z in range(5)
    if y != z
]
```

### 10.6 Default Arguments

- **Never** use mutable objects as default argument values:

```python
# ✅ Correct
def foo(a: list[int] | None = None):
    if a is None:
        a = []

# ❌ Wrong
def foo(a: list[int] = []):
    ...
```

### 10.7 The Main Guard

- Always wrap executable code in a `__main__` check:

```python
def main():
    ...

if __name__ == "__main__":
    main()
```

---

## 11. Linting & Formatting Tools

Enforce these standards automatically using the following tools:

| Tool | Purpose | Install |
|---|---|---|
| **Ruff** | Fast linter + formatter — the single recommended tool; replaces flake8, isort, and black | `pip install ruff` |
| **mypy** | Static type checker | `pip install mypy` |
| **pylint** | Comprehensive linter (optional; Google style guide references it) | `pip install pylint` |
| **bandit** | Security linter for common Python security issues | `pip install bandit` |
| **pip-audit** | Dependency vulnerability scanning (run in CI) | `pip install pip-audit` |

Use Ruff as the one formatter/linter. **Black** and **isort** are legacy standalone alternatives — do not add them alongside Ruff, which already covers both (`ruff format` = Black-compatible formatting, the `I` rule = isort).

### Recommended `pyproject.toml` configuration:

```toml
[tool.ruff]
line-length = 79
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "D",     # pydocstyle
    "UP",    # pyupgrade
    "B",     # bugbear
    "SIM",   # simplify
    "ANN",   # annotations
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Tabs for indentation | 4 spaces per level, always |
| `import os, sys` on one line | One import per line, grouped stdlib → third-party → local |
| Wildcard imports (`from module import *`) | Import the module or specific names explicitly |
| Spaces around `=` in keyword arguments/defaults (`imag = 0.0`) | `imag=0.0` — no spaces for kwargs and default values |
| `l`, `O`, `I` as single-character variable names | Descriptive names, proportional to scope |
| Inline comments stating the obvious (`x = x + 1  # Increment x`) | Comment only non-obvious context (`# Compensate for border`) |
| `foo != None` / `foo == None` | `foo is not None` / `foo is None` |
| `if len(items) != 0` or `items == []` | Implicit truthiness: `if items:` / `if not items:` |
| Building strings with `+=` in a loop | `"".join(items)` |
| Manual `open()` / `close()` for files, sockets, locks | `with` context manager |
| Multi-clause comprehensions with complex logic | A plain loop |
| Mutable default arguments (`def foo(a: list[int] = [])`) | Default to `None` and guard inside the function |
| Bare `except:` or catching `Exception` broadly | Catch specific exceptions; re-raise or isolate deliberately |
| `assert` to validate production data | Raise real exceptions (`ValueError`, etc.); reserve `assert` for internal invariants and tests |
| Executable code at module top level | Wrap in `main()` behind `if __name__ == "__main__":` |
| `type(obj) == list` | `isinstance(obj, list)` — respects subclasses |
| Re-raising a translated exception without `from` | `raise NewError(...) from exc` — preserves the original traceback chain |
| Threads for CPU-bound work | `ProcessPoolExecutor` — the GIL blocks thread-based CPU parallelism (see `references/pythonic-idioms.md`) |
| Regular class instantiated by the thousands with no `__slots__` | Add `__slots__` once instance count matters for memory |

---

## Pre-flight checklist — run before delivering any Python code

When writing or reviewing Python code, verify:

- [ ] **Indentation**: 4 spaces, no tabs
- [ ] **Line length**: ≤79 chars (72 for docstrings/comments)
- [ ] **Imports**: Ordered (stdlib → third-party → local), one per line, no wildcards
- [ ] **Blank lines**: 2 around top-level definitions, 1 around methods
- [ ] **Naming**: `snake_case` for functions/variables, `CamelCase` for classes, `UPPER_CASE` for constants
- [ ] **Docstrings**: Triple double quotes, present on all public APIs, Google style Args/Returns/Raises
- [ ] **Type hints**: Present on public APIs, using modern syntax
- [ ] **Whitespace**: No trailing whitespace, proper operator spacing
- [ ] **Comparisons**: `is`/`is not` for singletons, implicit truthiness for containers
- [ ] **No mutable defaults**: Use `None` + guard instead
- [ ] **Context managers**: `with` for files, sockets, locks
- [ ] **Main guard**: `if __name__ == "__main__"` present
- [ ] **Exception handling**: Specific exceptions, no bare `except:`
- [ ] **Exception chaining**: `raise ... from` used when translating one exception into another
- [ ] **Generators**: Large or streamed data uses a generator, not a fully-materialized list
- [ ] **Concurrency**: Tool matches the workload — threads for blocking I/O, processes for CPU, asyncio for async-native I/O (see `references/pythonic-idioms.md`)
