---
name: testing
description: >
  Software testing documentation dispatcher. Use when creating, reviewing, or improving
  test specifications and test documentation. Trigger on: "write test cases", "create a
  test plan", "test specification", "STS", "TDS", "TCS", "TPS", "test procedure",
  "define exit criteria", "requirements traceability matrix", "RTM", "risk-based testing",
  "test environment", "non-functional testing", "accessibility testing", "security testing",
  "performance testing", "CI/CD test integration", "document how to test this feature",
  "IEEE 829", or any task producing or reviewing software test documentation.
---

# Testing Dispatcher

When a test documentation task is requested, load the appropriate sub-skill.

## Routing Table

| Task Type | When to Use | Sub-skill to load |
|---|---|---|
| Software Test Specification (STS) | Writing or reviewing test specs, test cases, test procedures, RTMs, exit criteria, IEEE 829 / ISO 29119 standards | `software-test-specification/SKILL.md` |

## Instructions

1. Load `software-test-specification/SKILL.md` for all test documentation tasks. This
   dispatcher currently routes 1:1 — the broad trigger surface in the description
   (risk-based testing, RTM, non-functional testing, CI/CD integration) all funnels to
   that one sub-skill, which covers those areas in its sections. The dispatcher is kept
   as a scaffold for future test-doc sub-skills.
2. For test *requirements* (the performance/security/availability targets a test
   verifies), the source artifact lives in the documentation tree:
   `../documentation/non-functional-requirements-standards/SKILL.md`.
3. This dispatcher covers test *documentation* artifacts only (STS/TDS/TCS/TPS, RTMs,
   exit criteria). For TDD/BDD development *practice* in Python — Canon TDD,
   classicist/mockist, Gherkin authorship, Kafka event-driven testing — see
   `../code-standards/python/references/ddd-tdd-bdd-workflow.md`
   instead; it is not a test-documentation skill and does not route through here.
4. For test **code** and execution — actually writing and running tests, as opposed to
   test-planning documents — this dispatcher does not own that lane. Load the relevant
   `zeno-stack` testing-execution leaf instead: `zeno-stack/zeno-python-testing`,
   `zeno-stack/zeno-react-testing`, `zeno-stack/zeno-e2e-testing`, or
   `zeno-stack/zeno-browser-qa`.
