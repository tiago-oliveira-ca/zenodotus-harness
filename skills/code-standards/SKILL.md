---
name: code-standards
description: >
  Code standards and best practices dispatcher. Routes to the correct language, framework,
  database, or messaging standard for the technology in use. Use whenever writing, reviewing, or
  refactoring code, or designing domain models and architecture. Trigger on: any code generation
  or review task, "write a", "review this", "refactor", "best practice", "domain modeling",
  "clean architecture", "DDD", "SOLID", "design pattern", "database schema", "message queue", or
  any mention of Python, FastAPI, Django, DRF, SQLAlchemy, Rust, Axum, Go, Airflow, TypeScript,
  JavaScript, Angular, Oracle, PL/SQL, PostgreSQL, RabbitMQ, JSON Schema, Swift, SwiftUI, R,
  tidyverse, or Shiny.
---

# Code Standards Dispatcher

When a code task is requested, identify the technology and load the appropriate sub-skill
from this directory before generating or reviewing any code.

## Routing Table

| Technology / Framework | Sub-skill to load |
|---|---|
| Python — general, or any framework (FastAPI, Django REST Framework, Airflow nested underneath as `frameworks/*.md`) | `python/SKILL.md` |
| Rust, Axum, Tokio, Cargo, Rust domain modeling / DDD / hexagonal architecture | `rust/SKILL.md` |
| Go, domain modeling / DDD / hexagonal architecture in Go | `go/SKILL.md` |
| TypeScript, JavaScript — general, or Angular (signals, standalone components, NgRx, nested underneath as `frameworks/angular.md`) | `typescript-code-standards/SKILL.md` |
| Angular SCSS/CSS, visual styling, design tokens (any Angular project) | `typescript-code-standards/ui-style/SKILL.md` |
| Oracle SQL, PL/SQL, Oracle AI Database 26ai, vector search, RAG/GenAI on Oracle | `database-data-modeling/oracle-plsql/SKILL.md` |
| PostgreSQL and general relational data modeling | `database-data-modeling/postgres/SKILL.md` |
| RabbitMQ, message queues, exchanges, retry/DLX patterns | `rabbitmq/SKILL.md` |
| JSON Schema (Draft 2020-12), JSON payload/API contract design, JSON validation (Ajv), OpenAPI 3.1 schemas | `json-standards/SKILL.md` |
| R, tidyverse, Shiny, R packages, R6/S3/S4/S7, golem/rhino, targets pipelines | `r/SKILL.md` |
| Swift, SwiftUI, iOS/macOS app architecture (MVVM/TCA/VIPER selection), Vapor, Hummingbird (server-side Swift) | `swift/SKILL.md` |
| Software architecture, DDD, SOLID, Clean Architecture, design patterns (language-agnostic fallback) | `software-architecture/SKILL.md` |

## Instructions

1. Identify the primary technology from the user's request or the existing codebase imports.
2. Load and apply **only** the matching sub-skill above.
3. If multiple technologies are in scope (e.g. a FastAPI backend + Angular frontend),
   apply each relevant sub-skill to its respective layer.
4. If the technology is not listed above, apply general clean code and SOLID principles.
5. Any Python task always loads `python/SKILL.md` first (core language standards). If the
   task also involves FastAPI, Django REST Framework, or Airflow, additionally load the
   matching plain reference file — `python/frameworks/fastapi.md`,
   `python/frameworks/django-rest-framework.md`, or `python/frameworks/airflow.md` — which
   assumes the base Python standards and only covers what's framework-specific, so load both
   together. If the task is architectural — domain modeling, aggregates, ports/adapters, a
   Repository/Unit-of-Work, a composition root, or picking/rejecting a design pattern or DI
   approach in Python — additionally load `python/references/ddd-clean-architecture.md`
   alongside whichever framework reference applies. A Python + Kafka/event-driven task, or a
   task integrating DDD/TDD/BDD into one workflow, additionally loads
   `python/references/ddd-tdd-bdd-workflow.md`.
6. Any TypeScript/JavaScript task always loads `typescript-code-standards/SKILL.md` first
   (core language standards — type system idiom, async, modules, tooling). If the task
   involves Angular, additionally load `typescript-code-standards/frameworks/angular.md`,
   which assumes the base TypeScript standards and only covers what's Angular-specific. An
   Angular task that touches SCSS/CSS, visual layout, or design tokens must additionally load
   `typescript-code-standards/ui-style/SKILL.md` (visual design system) — it covers a
   different concern and is meant to be applied together with the framework reference, not as
   an alternative. Angular architecture/DDD questions load
   `typescript-code-standards/references/angular-clean-architecture.md` alongside the
   framework reference (see rule 7 below).
7. **Language-specific architecture guidance wins over the generic `software-architecture`
   sub-skill.** When a DDD / SOLID / Clean Architecture / design-pattern question is scoped to
   a language or platform that ships its own architecture guidance, use that guidance and do
   **not** also load the generic `software-architecture` sub-skill — they diverge on concrete
   choices (e.g. where repository interfaces live, whether to have one class per use case,
   function-first vs class-first idiom) and loading both yields contradictory advice.
   Specifically:
   - **Python** → `python/references/ddd-clean-architecture.md`
   - **Go** → `go/SKILL.md` (the consumer declares the port, etc.)
   - **Rust** → `rust/SKILL.md`
   - **R** → `r/SKILL.md` (deliberately adapts/reverses OOP principles for R's functional grain)
   - **Swift** → `swift/SKILL.md` (favors value types, enums-with-associated-values, and
     protocol-witness structs over deep protocol hierarchies — reject porting Java/C#-style
     layered indirection wholesale)
   - **TypeScript + Angular** → `typescript-code-standards/references/angular-clean-architecture.md`
     (plain TypeScript/Node work with no framework has no dedicated architecture guidance of
     its own yet — fall through to the generic `software-architecture` sub-skill for that case)
   - **Oracle PL/SQL** → `database-data-modeling/oracle-plsql/references/clean-architecture.md`
     (bounded contexts as schema boundaries, PL/SQL packages as repository contracts, etc. —
     do not apply the generic skill's Repository/Aggregate guidance verbatim to Oracle)

   Load the generic `software-architecture` sub-skill only for language-agnostic architecture
   questions, or for a language/platform that has no dedicated architecture guidance of its own
   (PostgreSQL, RabbitMQ, JSON Schema, plain TypeScript/Node with no framework).
8. Oracle tasks do **not** default to a legacy version. Load
   `database-data-modeling/oracle-plsql/SKILL.md` for the version-agnostic PL/SQL core, which
   covers most naming/exception-handling/bulk-processing/cursor standards regardless of
   version. Additionally load `frameworks/oracle-11g.md` only when the request or codebase
   explicitly targets a legacy/pre-12c deployment — never as a silent default for unversioned
   work. Additionally load `frameworks/oracle-26ai.md` when the request or codebase signals
   Oracle AI Database features: 26ai, VECTOR columns, vector search, DBMS_VECTOR, RAG, or OCI
   GenAI.
9. For system-level architecture questions (how many services, when to split a monolith,
   bounded contexts), use the top-level `software-architecture-progression` skill instead —
   it governs system topology, while this dispatcher's `software-architecture` sub-skill
   governs code structure within a module. They are complementary; apply
   `software-architecture-progression` first, then this dispatcher's `software-architecture`
   sub-skill.
10. Each language sub-skill carries its own docstring / doc-comment standard (godoc, rustdoc,
    TSDoc, DocC, roxygen2, PL/SQL, PEP 257). The **cross-cutting** discipline for documenting
    production code — when to document, keeping docs in sync with the code (drift), driving the
    right generator — is the top-level `documenting-code` skill. Apply the language sub-skill for
    *how a docstring looks*; `documenting-code` for *whether/what/when and keeping it accurate*.
11. This dispatcher sits in the middle of the delivery lifecycle: it is handed off work from
    `documentation` (once a TRD/SAD/ADR settles *what* to build, this dispatcher governs *how* the
    code is written) and hands off in turn to `testing` for test specification once the code
    standards have been applied, continuing on to deployment — `github-circleci-standards` for CircleCI pipelines, `zeno-stack/zeno-deployment-patterns` for GitHub Actions and for platform-neutral strategy/rollback/readiness.
