---
description: Review a FastAPI application for architecture, async correctness, dependency injection, Pydantic schemas, security, performance, and testability.
---

# /fastapi-review

Delegates to the `zeno-fastapi-reviewer` agent for a focused pass over a FastAPI codebase.

## Usage

```text
/fastapi-review [file-or-directory]
```

## What it covers

- App factory structure, router boundaries, middleware, and exception handlers.
- Separation between Pydantic request and response schemas.
- Dependency injection for database sessions, auth, pagination, and settings.
- Async correctness in database access and outbound HTTP calls.
- CORS, auth, rate limiting, logging, and secret handling.
- OpenAPI metadata and documented response models.
- Test client setup and dependency overrides.

## Output format

```text
[SEVERITY] Short issue title
File: path/to/file.py:42
Issue: What is wrong and why it matters.
Fix: Concrete change to make.
```

## Related

- Agent: `zeno-fastapi-reviewer`
- Skill: `code-standards/python/frameworks/fastapi.md`
- Command: `/python-review`
- Skill: `zeno-stack/zeno-security-review`
