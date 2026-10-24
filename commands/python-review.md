---
description: Comprehensive Python code review for PEP 8 compliance, type hints, security, and Pythonic idioms. Invokes the zeno-python-reviewer agent.
---

# /python-review

Delegates to the **zeno-python-reviewer** agent for a focused pass over Python changes.

## Usage

```text
/python-review [file-or-directory]   # default scope: modified .py files via git diff
```

## What it covers

- Static analysis: `ruff`, `mypy`, `pylint`, `black --check`.
- Security: SQL/command injection, unsafe `eval`/`exec`/pickle/YAML, hardcoded credentials.
- Type safety: hints on the public surface, read together with mypy output.
- Idiom: PEP 8 and Pythonic patterns per `code-standards/python`.

## Output format

```text
[SEVERITY] Short issue title
File: path/to/file.py:42
Issue: What is wrong and why it matters.
Fix: Concrete change to make.
```

Severity tiers, the idiom catalog, and version-compat rules live in the skill and agent this
command wraps — they are deliberately not duplicated here.

## Related

- Agent: `zeno-python-reviewer`
- Skill: `code-standards/python` (the single Python authority)
- Command: `/fastapi-review`
