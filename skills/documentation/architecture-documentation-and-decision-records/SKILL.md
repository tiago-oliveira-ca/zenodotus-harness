---
name: architecture-documentation-and-decision-records
description: >
  Standards and workflow for Architecture Decision Records (ADRs) and architecture
  documentation. Use when creating, reviewing, or organizing ADRs, capturing
  architecture-significant decisions, maintaining overview docs, or linking diagrams and
  supporting artifacts. Trigger on: "write an ADR", "architecture decision", "why did we
  choose X", "document this decision", "should we write an ADR", "record this choice",
  "decision log", "ADR template", "architecture overview doc", or any task involving
  documenting system-level technical decisions and their rationale.
---

# Architecture Documentation and Decision Records

Use this skill when the task is to create, review, or organize architecture documentation
and ADRs. Keep documentation layered, current, and traceable so future readers can
understand both the system shape and the reasons behind significant decisions.

## Core Boundaries

- **Architecture documentation** explains the current system views and supporting context.
- **ADRs** capture individual architecture-significant decisions and their rationale.
- **Runbooks** describe how to operate and support the system — use
  `../operations-standards/SKILL.md` for runbook, incident response, and postmortem
  standards; this skill only covers the boundary, not runbook content.
- **API specs** describe interface details, not architecture rationale.

## Required Inputs

- The decision that needs to be made, or was already made informally
- Context and constraints that forced the decision — technical, business, team, or timeline
- Options considered, with their pros and cons
- Deciders or stakeholders whose sign-off matters
- The SAD/Blueprint component this decision affects, and any prior ADR it supersedes

## Document Types

Maintain documentation at the right level for the audience:

- **Context / overview** for stakeholders and onboarding
- **Container / module views** for engineers understanding system boundaries
- **Component or sequence views** only where they materially improve understanding
- **ADRs** for significant decisions such as framework, datastore, deployment, or pattern
  choices

## ADR Writing Rules

Write an ADR when a decision is architecturally significant. Do not use ADRs for trivial
implementation choices.

A standard ADR should include:

- **Title**: human-readable decision statement such as `Use Docker for service packaging`
- **Filename**: unique file name such as `0001-use-docker.md`
- **Date**
- **Status**
- **Context / Decision Drivers**
- **Considered Options**
- **Decision**
- **Consequences**

Keep ADRs short, focused, and centered on one decision.

## ADR Template

Use this template when creating a new ADR:

```markdown
# ADR-NNNN: [Short title — state the decision, not just the topic]

- **Date**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Rejected | Superseded by ADR-XXXX | Deprecated
- **Deciders**: [Names or roles]
- **Supersedes**: [ADR-XXXX if applicable]

## Context

[What situation, constraint, or problem forced this decision?
What forces are in play — technical, business, team, timeline?]

## Considered Options

| Option | Pros | Cons |
|---|---|---|
| Option A | ... | ... |
| Option B | ... | ... |
| Option C | ... | ... |

## Decision

We chose **[Option X]** because [brief rationale tying back to the context and forces].

## Consequences

**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative / Trade-offs:**
- [Risk or cost 1]
- [Risk or cost 2]

**Follow-up actions:**
- [ ] [Next step or linked ticket]
```

## Decision Threshold — When to Write an ADR

| Scope | Write an ADR? |
|---|---|
| Framework or language selection | Yes |
| Data store choice | Yes |
| Auth/security approach | Yes |
| Major integration pattern | Yes |
| API contract or protocol choice | Yes |
| Deployment platform change | Yes |
| Naming convention update | No |
| Minor refactor with no boundary change | No |
| Bug fix | No |

## ADR Lifecycle

- ADRs are immutable once accepted except for status updates or explicit supersession links.
- If a decision changes, write a new ADR and supersede the old one.
- Use statuses deliberately:
  - `Proposed`: under review
  - `Accepted`: approved decision of record
  - `Rejected`: considered but not adopted
  - `Superseded`: replaced by a newer ADR
  - `Deprecated`: no longer relevant due to system evolution

## Architecture Documentation Workflow

1. Capture the architecture problem or decision as soon as it becomes material.
2. Draft the minimum useful architecture view or ADR.
3. Link related diagrams, tickets, and existing ADRs.
4. Review changes via pull request like code.
5. Update non-ADR docs whenever the architecture changes.

## Storage and Layout

Keep architecture artifacts in version control near the codebase.

```text
project-root/
├─ docs/
│  ├─ architecture/
│  │   ├─ overview.md
│  │   ├─ context.md
│  │   ├─ containers.md
│  │   └─ diagrams/
│  ├─ decisions/
│  │   ├─ 0001-example.md
│  │   └─ index.md
│  ├─ runbooks/
│  └─ README.md
```

## Tooling and Automation

- Any diagram needed for architecture documentation or an ADR must be built with
  `../../puml-diagrams/SKILL.md` — load it before writing diagram code. Only deviate
  (Mermaid, Structurizr) if the project already has an established diagramming toolchain in
  place.
- Use markdown linting and link checks in CI where practical
- Publish architecture docs if the team benefits from a browsable docs site

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Logging trivial decisions as ADRs | Buries real decisions in noise; the Decision Threshold table gets ignored | Apply the Decision Threshold table before creating a new ADR |
| Bundling multiple decisions into one ADR | Can't supersede or reference one decision without dragging in the others | One decision per ADR; split before writing |
| Letting diagrams or overview docs drift from the system | Docs describe an architecture that no longer exists | Update non-ADR docs whenever the architecture changes, same as any other code change |
| Scattering architecture knowledge across unlinked tools or folders | No one can find the decision or context when they need it | Keep architecture artifacts in version control near the codebase, per Storage and Layout |
| Skipping peer review or ownership for documentation | Undetected errors and no accountable owner when the doc goes stale | Review ADRs and architecture docs via pull request like code |

## Pre-flight checklist — run before delivering any ADR or architecture document

- [ ] The document type matches the audience and purpose
- [ ] ADR titles are human-readable and filenames are distinct identifiers
- [ ] ADR status reflects the real lifecycle state
- [ ] Decisions, diagrams, and related tickets are cross-linked
- [ ] Non-ADR architecture docs represent the current system or are clearly marked outdated
