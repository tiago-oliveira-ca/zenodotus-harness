# Pythonic Structural Idioms

Deeper, non-framework-specific structural idioms for Python that stays readable as it grows.
The parent `../SKILL.md` owns the base layer (PEP 8/20/257 layout, naming, docstrings, basic
typing, comparisons, comprehension complexity limits, mutable defaults) — this file covers the
structural patterns on top of it: EAFP, advanced typing, exception chaining, custom context
managers, generators, dataclasses, decorators, concurrency model choice, package layout, and
memory trade-offs. Test code itself belongs to `zeno-stack/zeno-python-testing`.

---

## 1. EAFP over LBYL

Python favors exception handling ("Easier to Ask Forgiveness than Permission") over
pre-checking conditions ("Look Before You Leap") — it avoids a race between the check and the
use, and reads more directly:

```python
# ✅ Good — EAFP
def get_value(d: dict, key: str, default=None):
    try:
        return d[key]
    except KeyError:
        return default

# ❌ Worse — LBYL, and racy under concurrent mutation
def get_value(d: dict, key: str, default=None):
    if key in d:
        return d[key]
    return default
```

---

## 2. Advanced Type Hints

The parent file covers annotation basics (built-in generics, `X | Y` unions, annotating all
public APIs). Beyond those:

```python
# Type aliases and TypeVar for reusable shapes
from typing import TypeVar
JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
T = TypeVar('T')

def first(items: list[T]) -> T | None:
    return items[0] if items else None

# Protocol for structural typing — duck typing the type checker can verify
from typing import Protocol

class Renderable(Protocol):
    def render(self) -> str: ...

def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)
```

A signature without types is a contract the caller has to reverse-engineer from the
implementation — annotate every function signature in library and service code.

---

## 3. Exception Chaining

Catch specific exceptions and chain with `from` to preserve the traceback when translating a
low-level failure into a domain-level one:

```python
# ✅ Good — specific exceptions, chained with `from` to preserve the traceback
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config: {path}") from e

# ❌ Bad — bare except silently discards the failure
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except:
        return None
```

For a full typed-exception hierarchy (`AppError`, `NotFoundError`, `ValidationError`, ...) and
the FastAPI handlers that render them, see `zeno-stack/zeno-error-handling` — this file covers
the language-level idiom (specific excepts, `raise ... from`), that one covers the application
error contract.

---

## 4. Custom Context Managers

The parent file mandates `with` for anything that must be released. Writing your own:

```python
# Custom context manager via generator
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    print(f"{name} took {time.perf_counter() - start:.4f} seconds")

# Custom context manager class — for stateful resources like a DB transaction
class DatabaseTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        return False  # never suppress the exception
```

---

## 5. Generators for Lazy Evaluation

The parent file owns the "keep comprehensions simple" rule. When the data is large or
streamed, prefer a generator over a fully-materialized list:

```python
# Generator expression for lazy evaluation over large ranges — avoids the
# intermediate list a list comprehension would materialize
total = sum(x * x for x in range(1_000_000))

# Generator function for streaming large files without loading them fully into memory
def read_large_file(path: str) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()
```

---

## 6. Dataclasses and Named Tuples

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")

# Immutable value type — NamedTuple when the object is a small, hashable value
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

    def distance(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```

---

## 7. Decorators

```python
import functools

def timer(func):
    @functools.wraps(func)  # preserves __name__/__doc__ — never omit this
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.4f}s")
        return result
    return wrapper

def repeat(times: int):
    """Parameterized decorator — one extra layer of nesting."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator
```

---

## 8. Concurrency Model — Pick by Workload

| Workload | Tool | Why |
|---|---|---|
| I/O-bound, many blocking calls (HTTP, file I/O) | `ThreadPoolExecutor` | GIL releases during I/O waits; threads are cheap here |
| CPU-bound (heavy computation) | `ProcessPoolExecutor` | The GIL blocks CPU parallelism in threads; separate processes bypass it |
| I/O-bound, high concurrency, async-native libraries | `asyncio` + `asyncio.gather` | Single-threaded event loop scales to thousands of concurrent waits without thread overhead |

```python
# I/O-bound: threads
def fetch_all_urls(urls: list[str]) -> dict[str, str]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}
        return {future_to_url[f]: f.result() for f in concurrent.futures.as_completed(future_to_url)}

# CPU-bound: processes
def process_all(datasets: list[list[int]]) -> list[int]:
    with concurrent.futures.ProcessPoolExecutor() as executor:
        return list(executor.map(process_data, datasets))

# I/O-bound, async-native: asyncio
async def fetch_all(urls: list[str]) -> dict[str, str]:
    tasks = [fetch_async(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip(urls, results))
```

---

## 9. Package Layout

```
myproject/
├── src/mypackage/
│   ├── __init__.py        # re-export public API, define __all__
│   ├── main.py
│   ├── api/
│   ├── models/
│   └── utils/
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── pyproject.toml
└── README.md
```

Import ordering (stdlib → third-party → local) is the parent file's rule; enforce it with
Ruff's `I` rule.

---

## 10. Memory and Performance

```python
# __slots__ trades flexibility for memory — worth it on classes instantiated in bulk
class Point:
    __slots__ = ['x', 'y']
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y
```

String building is the parent file's rule: O(n) `"".join(...)`, never O(n²) `+=` in a loop.
