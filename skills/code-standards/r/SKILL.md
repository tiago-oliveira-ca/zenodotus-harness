---
name: r
description: >
  R code standards adapting Clean Code, SOLID, Clean Architecture, and selected DDD ideas to R's
  functional, vectorized nature: tidyverse style, object-system selection (S3/S4/S7/R6), package
  structure (roxygen2/testthat/CRAN), layered Shiny architecture (golem, rhino/box), pipeline
  design (targets), over-engineering thresholds. Use whenever writing, reviewing, or refactoring
  R code. Trigger on: "R script", "R package", ".R file", "tidyverse", "dplyr", "ggplot2",
  "Shiny", "R6", "S3 method", "S7", "roxygen", "testthat", "golem", "targets pipeline", "CRAN",
  "tibble", "DDD in R", or any code generation, review, or architecture question in R.
---

# R Code Standards & Best Practices

Adhere strictly to these standards when generating, reviewing, or refactoring R code.
They adapt Clean Code, SOLID, Clean Architecture, design patterns, and selected DDD
concepts to R's functional grain. Sources: *Advanced R* and *R Packages* (Wickham &
Bryan), the tidyverse style and design guides, rOpenSci and Bioconductor dev guides,
CRAN policy, and the golem/rhino/mlr3/targets ecosystems.

---

## 1. The prime directive — R is functional first

R is a functional, vectorized, copy-on-modify language. You solve complex problems by
decomposing them into simple **functions**, not simple objects. Embrace this; don't
fight it.

**Rules:**

- **Default to plain functions + data frames/tibbles + S3.** Reach for heavier
  machinery only when a threshold in §9 is crossed.
- **Never import enterprise OOP scaffolding wholesale** (DI containers, deep class
  hierarchies, DDD aggregates) into analytical code. Functions applied to data frames
  are the idiom; code that fights it is code other R users cannot read.
- Prefer immutability: copy-on-modify makes R values immutable by default — treat that
  as a feature, not an obstacle.

## 2. Choosing an object system

Four systems, two paradigms: **functional OOP** (S3, S4, S7 — methods belong to
generics) vs **encapsulated OOP** (R6, RC — methods belong to objects, reference
semantics).

| Situation | Use |
|---|---|
| Polymorphic returns, analytical code, most packages | **S3** (default) |
| Repeated `if (inherits(x, ...))` / `class(x) ==` branching | Introduce an **S3/S7 generic** |
| Genuine mutable state: API clients, DB connections/pools, Shiny app state, ML pipelines, simulations | **R6** |
| Large formally-typed system, many contributors, multiple dispatch, validity enforcement | **S4** (Bioconductor standard) or **S7** |
| New formal-OOP code where S4 would otherwise be chosen | Consider **S7** (S3/S4 successor; still maturing — flag its experimental status) |
| RC (Reference Classes / R5) | Don't — use R6 |

**Rules:**

- **S3 constructors follow the constructor / validator / helper pattern**: a
  low-level `new_myclass()` constructor, a `validate_myclass()` that checks invariants,
  and a user-facing `myclass()` helper.
- **R6 comes with obligations:** reference semantics reintroduce aliasing bugs foreign
  to copy-on-modify R — implement/verify `$clone(deep = TRUE)` behavior whenever an R6
  object holds other R6 objects; side-effecting methods return `invisible(self)` to
  enable chaining.
- "Create many small methods" applies to R6 (local namespace) — it does **not** apply
  to S3, where every method is a global function.
- Respect ecosystem norms: tidyverse-adjacent code leans S3/R6; Bioconductor requires
  S4 and reusing existing classes (SummarizedExperiment etc.) over inventing new ones.

## 3. Clean Code — tidyverse style rules

Apply the tidyverse style guide unless the project already follows Google's R guide
(BigCamelCase functions, `.` prefix for private) — never mix the two.

| Concern | Rule | Example |
|---|---|---|
| Variables | `snake_case` nouns | `day_one`, `model_fit` |
| Functions | `snake_case` verbs | `invert_matrix()`, `fit_model()` |
| Dots in names | Reserved **exclusively** for S3 methods | never `my.variable` |
| Assignment | `<-`, never `=` | `x <- 5` |
| Logicals | `TRUE`/`FALSE`, never `T`/`F` | — |
| Strings | `"` double quotes | — |
| Line length | ≤ 80 characters | — |

**Function design rules:**

- **One function, one purpose** — describable in a single sentence.
- **Return an object OR perform a side effect — never both.** Side-effecting functions
  return `invisible(x)` so they stay pipeable.
- `return()` only for early returns; the last expression is the return value otherwise.
- Signal with `message()`/`warning()`/`stop()`, never `print()`/`cat()` for conditions.
- Pass internal choices up to the caller as arguments with defaults (e.g. expose
  `optim()` options) instead of hard-coding them — this is dependency inversion at the
  function level.
- Names are the ubiquitous language: evocative, human-centered, one canonical term per
  domain concept across the codebase.

## 4. SOLID, translated to R idiom

| Principle | R expression |
|---|---|
| **S**RP | One-purpose functions; architecturally, business logic separated from app/reactive logic (§6) so you debug one or the other, never both |
| **O**CP | Generic functions: downstream code adds methods to `summary()`-style generics without touching them; registry/dictionary pattern (mlr3's `mlr_learners`) for plugin extension |
| **L**SP | Polymorphic dispatch contracts: S4 validity methods enforce substitutability formally; R6 `inherit =` subclasses must honor superclass method contracts |
| **I**SP | Small, focused generics; in R6, small "abstract interface" classes whose methods `stop("abstract method")` |
| **D**IP | Pass dependencies (functions, connections, objects) as arguments — not hard-coded internals; R6 fields typed to interface classes when object-shaped |

**Rule:** dependency injection in R is a function argument with a sensible default —
never a DI container.

```r
# DIP + Strategy in one idiomatic move: the dependency is an argument
summarise_scores <- function(scores, agg = mean) {
  agg(scores, na.rm = TRUE)
}
```

## 5. DDD — borrow three ideas, skip the rest

DDD has almost no established R practice. Borrow only the low-cost concepts:

- **Ubiquitous language** → tidyverse naming discipline (§3): domain vocabulary in
  function and column names.
- **Bounded context** → the **package** (or box/rhino module): a namespace with an
  explicit exported API is R's bounded context. One package per context vocabulary.
- **Repository** → data-access abstraction via DBI/pool/dbplyr or an R6 repository
  class (§7) — but only when you need swappable backends or in-memory test fakes.
- **Value objects** → validated immutable S3/S7 records (constructor + validator);
  copy-on-modify gives you immutability for free.
- **Entities with identity and mutable lifecycle** → the one place R6 plays the DDD
  role.
- **Skip**: aggregates, domain events, full tactical DDD in analytical pipelines —
  indirection without payoff. Treat the `ddd`/`R6P` packages as non-standard references,
  not dependencies to adopt by default.

## 6. Layered architecture — separate pure logic from framework code

The load-bearing rule across every production R architecture: **business logic lives in
plain, Shiny-free, I/O-free, testable functions; framework code stays thin.**

| Clean Architecture layer | Idiomatic R home |
|---|---|
| Presentation / UI | Shiny UI (`app_ui.R`, `mod_*` UI, rhino `app/view`), R Markdown/Quarto |
| Application / use cases | Shiny server modules, `targets` pipeline definition, top-level exported functions |
| Domain / business logic | Pure functions in `R/`, golem `fct_*`, rhino `app/logic`; S4/S7 generics; R6 domain objects |
| Data access / ETL | DBI/pool/dbplyr, readr/arrow, repository classes |

**Rules:**

- **Production Shiny app → build it as a package** with **golem** (`fct_*` = business
  logic, `mod_*` = one Shiny module each, `utils_*` = helpers) **or rhino/box**
  (`app/logic` = Shiny-independent, `app/view` = Shiny modules; `box::use()` gives an
  explicit, enforced import graph). Pick per team background; don't mix frameworks.
- **Long-lived analytical pipeline → `targets`**: functions in `R/` are the domain
  layer; the `_targets.R` pipeline is the use-case/orchestration layer. Never bury
  orchestration inside domain functions.
- Domain-layer functions take data as arguments and return values — no database
  calls, no `reactive()`, no file I/O inside them. I/O happens at the edges.
- If UI and computation are tangled and hard to test, that alone is the signal to
  split logic/view layers.

## 7. Design patterns, idiomatically

- **Strategy** — pass a function as an argument, or return a configured function from
  a closure. Never build a strategy class hierarchy where a function argument works.
- **Factory** — closures returning configured functions; R6 generators
  (`Class$new()`); mlr3-style sugar constructors (`lrn()`, `tsk()`) that build and
  configure in one call.
- **Repository / data access** — DBI is the interface, backend drivers (RSQLite,
  RPostgres, …) are the adapters; **pool** for connection pooling (mandatory for Shiny
  + DB); **dbplyr** to treat remote tables as data frames. For unit-testable domain
  code, define an R6 repository interface with in-memory (test fake) and DBI-backed
  implementations.
- **Registry/dictionary** — a named collection add-on packages can populate (mlr3's
  `mlr_learners`) when you need plugin-style extensibility.
- **Observer** — Shiny reactivity *is* the observer system; don't hand-roll one inside
  a Shiny app.
- **Method chaining** — R6 methods return `invisible(self)`; functional code uses the
  pipe instead. Don't offer both styles on one API.
- **Decorator / Composite / Abstract Factory** — possible in R6 but documented as
  complex (distr6); require explicit justification before using.

```r
# Factory via closure — idiomatic R, no class needed
make_scaler <- function(center, scale) {
  function(x) (x - center) / scale
}
scale_iris <- make_scaler(mean(iris$Sepal.Length), sd(iris$Sepal.Length))
```

## 8. Package structure, documentation, testing

**Structure (per *R Packages* 2nd ed.):** code in `R/`, generated docs in `man/`,
tests in `tests/testthat/`; workflow via devtools/usethis; package names short,
descriptive, lowercase; default branch `main`.

**Documentation (roxygen2):**

- Every exported function: `#'` block with `@param`, `@return`, `@examples`, `@export`.
- Internal functions: document with `@noRd` rather than leaving bare.
- Examples must run — they are executed by checks and double as smoke tests. Wrap
  long-running ones in `\donttest{}`.
- Cross-cutting doc discipline (drift, when to update, generators): see `documenting-code`.

**Testing (testthat):**

- One test covers one unit of functionality; test names complete the sentence
  "Test that …".
- Business logic layers (§6) are tested as plain functions — architecture exists
  partly so this is possible.
- CI + coverage reporting from day one for anything shared (rOpenSci requirement).

**CRAN / dependency rules:**

- `R CMD check` must pass with no warnings or significant notes.
- Dependencies in `Imports` + `pkg::fun()` calls — never attach with `library()` inside
  package code; make minimum dependency versions a conscious choice.
- DESCRIPTION names a single human maintainer; source tarball ≤ 10 MB.

**Bioconductor divergences (apply only there):** S4 required, CamelCaps class names,
`AllGenerics.R`/`AllClasses.R` file conventions, reuse core classes before defining new
ones.

## 9. Escalation thresholds — when to add machinery, when to stop

Adopt in stages; each stage requires its trigger, not aspiration:

1. **Always:** tidyverse style, single-purpose functions, roxygen2 + testthat. (~80% of
   Clean Code's value, near-zero cost.)
2. **Code is reused or shared →** make it a package; separate pure logic from I/O; add
   CI; use S3 generics for extensibility.
3. **Production app or long-lived team pipeline →** golem/rhino layering or targets
   orchestration; all business logic in a Shiny-free testable layer.
4. **Genuine mutable state or large typed system →** R6 (study mlr3: R6 + registry +
   sugar factories + checkmate-validated inputs) or S4/S7; repository abstraction only
   when backends must swap or tests need in-memory fakes.

**Threshold triggers:**

- Many `if (class(x) == ...)` branches → introduce a generic.
- Same growing state threaded through many calls → consider R6.
- UI tangled with computation → split logic/view.
- **Reverse trigger:** class hierarchy has more abstraction layers than concrete
  behaviors, or DDD aggregates appearing in a data pipeline → over-engineered; revert
  to functions and data frames.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| OOP-first design for a data analysis | Functions + data frames + S3 |
| `if (class(x) == ...)` chains | S3/S7 generic + methods |
| Reference Classes (RC/R5) | R6 |
| R6 for stateless computation | Plain functions / closures |
| Strategy or factory class hierarchies | Function arguments / closures |
| DI containers, DDD aggregates in pipelines | Arguments with defaults; plain functions |
| Business logic inside `server()` / `reactive()` | `fct_*` / `app/logic` layer, unit-tested |
| `library()` calls inside package code | `Imports` + `pkg::fun()` |
| `print()`/`cat()` for conditions | `message()` / `warning()` / `stop()` |
| Functions that transform AND side-effect | One or the other; side-effectors return `invisible(x)` |
| `T`/`F`, `=` assignment, dots in non-S3 names | `TRUE`/`FALSE`, `<-`, snake_case |
| Uncloned nested R6 objects | `$clone(deep = TRUE)` with tested semantics |
| Hand-rolled observer inside Shiny | Shiny reactivity |
| New S4 classes on Bioconductor when core classes fit | Reuse SummarizedExperiment etc. |

## Pre-flight checklist — run before delivering any R code

Verify each item before presenting generated or reviewed R code. Fix failures first.

1. Style: snake_case, verbs for functions/nouns for variables, `<-`, `TRUE`/`FALSE`,
   double quotes, ≤ 80 chars, dots only in S3 method names.
2. Every function has one purpose; no function both returns a value and side-effects;
   side-effectors return `invisible(x)`.
3. Object-system choice matches §2 — and the answer "plain functions + S3" was
   considered first. R6 present only with a genuine mutable-state justification.
4. No `class(x) ==` dispatch chains; generics used instead.
5. Shiny work: business logic lives outside modules/reactives in a testable layer
   (golem `fct_*` or rhino `app/logic`); pipelines: orchestration in `targets`, not
   inside domain functions.
6. Dependencies passed as arguments with defaults; no hard-coded internal choices the
   caller may need to vary; package code uses `Imports` + `::`.
7. Exported functions have complete roxygen2 blocks with runnable examples; internal
   ones have `@noRd`.
8. testthat tests cover the logic layer; names read as "Test that …".
9. Ecosystem norms respected (tidyverse vs Google style consistent; Bioconductor → S4
   + class reuse).
10. Escalation audit (§9): no machinery present without its trigger; no reverse-trigger
    smells (abstraction layers > concrete behaviors).
