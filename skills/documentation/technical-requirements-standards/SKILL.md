---
name: technical-requirements-standards
description: >
  Standards for Technical Requirements Documents (TRD) and Software Requirements
  Specifications (SRS). Use when specifying what a system must do in technically precise,
  testable, and traceable terms. Trigger on: "write a TRD", "technical requirements",
  "software requirements", "system requirements", "SRS", "interface specifications",
  "what the system shall do", or any requirement document that needs verification methods,
  traceability IDs, and testable acceptance criteria. For a dedicated document covering
  performance, availability, security, scalability, compliance, or DR targets, use
  non-functional-requirements-standards instead.
---

# Technical Requirements Standards

Use this skill when defining or reviewing technical requirements that engineering teams must
implement and verify. A TRD or SRS should be specific enough to build and test against,
without collapsing into solution code or architecture rationale.

## Core Boundaries

- **BRD / PRD** define business or product intent
- **FSD / FRD** defines detailed functional behavior
- **NFR** defines dedicated quality-attribute targets (performance, availability, security,
  scalability, compliance, DR) — use that skill when NFRs need their own document
- **TRD / SRS** define the technical requirements, interfaces, constraints, and verification
  expectations
- **ADR / SAD** define technical decisions and architecture structure

## Required Inputs

- Source business or product requirements
- Technical context, assumptions, and dependencies
- Interface and data expectations
- Target platforms, constraints, and compliance obligations
- Verification expectations and downstream testing needs

## Recommended Structure

1. **Document Control**
2. **Purpose and Scope**
3. **System Overview**
4. **Assumptions, Dependencies, and Constraints**
5. **Specific Requirements**
6. **Interfaces and Data Requirements**
7. **Verification and Traceability**
8. **Approval and Change Control**

## Writing Rules

- Use `shall` for mandatory requirements.
- Give every requirement a unique identifier.
- Keep statements atomic, clear, active, and objectively verifiable.
- Avoid hidden design choices unless the design constraint itself is a requirement.
- Use measurable criteria instead of vague quality adjectives.

## Verification and Traceability

Every requirement should identify or support:

- upward traceability to business or product need
- downward traceability to design, implementation, and tests
- a verification method such as test, analysis, demonstration, or inspection

### Verification Method Selection

| Method | When to Use | Example |
|---|---|---|
| **Test** | Behavior can be exercised programmatically or manually | "shall authenticate in ≤ 200ms" → load test |
| **Analysis** | Behavior is proven through calculation or modelling | Memory capacity, bandwidth estimate |
| **Demonstration** | Behavior is shown by operating the system | UI accessibility, installation procedure |
| **Inspection** | Behavior is verified by examining code/config/document | Code review, config audit, license check |

### Requirement Quality Checklist

Each individual requirement should be:

| Quality | Test | Bad | Good |
|---|---|---|---|
| **Unambiguous** | One interpretation only | "fast response" | "response ≤ 200ms at P95" |
| **Testable** | Pass/fail verifiable | "good security" | "shall pass OWASP Top 10 scan with no critical findings" |
| **Atomic** | One statement, one thing | "login and log out" | Separate TR-001 and TR-002 |
| **Traceable** | Links to source need | Orphan requirement | TR-042 carries `Trace: BR-007` |
| **Consistent** | No contradiction with others | Conflicting timeouts | Reconcile in constraints section |

## House IDs and traceability

TRD requirements use the house ID grammar from `../references/lifecycle.md`: `TR-NNN`,
sequential, zero-padded to 3 (`TR-004`). Every TR carries a `Trace:` line to its upstream
`BR-NNN`/`PRD-NNN`/`FR-NNN` source (Engineering-imposed requirements with no business parent
follow lifecycle.md's rule for those); NFRs folded inline into a TRD keep `TR-NNN` IDs here or
graduate to `NFR-NNN` in a dedicated NFR document — never both. "What implements TR-004?" must
be answerable by `grep -rn "TR-004"`.

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Design choice stated as a requirement | "The system shall use Redis" | State the need ("shall respond in ≤50ms"); let architecture pick the mechanism unless the technology itself is the constraint |
| Vague quality adjective | "The system shall be reliable" | Give a measurable target — that belongs in an NFR, not a loose TRD line |
| Untraceable requirement | TR-014 has no link to a BRD/PRD/FSD source | Every requirement traces upward to a business or product need |
| No verification method | Requirement with no way to prove it's met | Assign test, analysis, demonstration, or inspection per requirement |
| Compound requirement | "The system shall authenticate and log every request" | Split into atomic, independently verifiable requirements |
| Requirements frozen too early | Baselined before interfaces/dependencies are known, causing rework | Baseline only after peer and stakeholder review confirms scope is stable |

## Review Workflow

1. Validate scope and technical context.
2. Check each requirement for clarity, uniqueness, and testability.
3. Confirm assumptions, interfaces, and constraints are explicit.
4. Verify traceability and verification approach.
5. Baseline the document only after peer and stakeholder review.

## Pre-flight checklist — run before delivering any TRD

- [ ] Mandatory requirements use `shall`
- [ ] Every requirement has a unique ID
- [ ] Assumptions, dependencies, and constraints are explicit
- [ ] Interface and data requirements are not hidden in prose
- [ ] Verification method and traceability are addressed
- [ ] Approval and change-control expectations are clear
