---
name: solution-architecture-standards
description: >
  Standards for Solution Architecture artifacts at either formality level — lightweight
  Blueprints (SAB) for early-phase or exploratory work, and fully governed Solution
  Architecture Documents (SAD) with stakeholder approval paths. Use when documenting solution
  structure, major components, constraints, and architecture-level behavior. Trigger on:
  "architecture overview", "solution blueprint", "high-level design", "sketch the
  architecture", "quick architecture doc", "rough architecture", "early-phase design", "write
  a SAD", "solution architecture document", "formal architecture document", "architecture
  review", "document the system architecture", "architecture sign-off", or when stakeholder
  approval of architecture is required.
---

# Solution Architecture Standards

Use this skill when the task is to create, review, refine, or validate a solution
architecture artifact — whether a lightweight blueprint or a fully governed SAD. Keep the
artifact architecture-focused: it should explain system structure, data and integration
flows, quality attributes, infrastructure shape, and rollout considerations without
collapsing into code commentary or operational runbooks.

## Choosing the Formality Level

Both tiers share the same structure and rigor below. Pick the tier the task actually needs:

- **Blueprint (SAB — Solution Architecture Blueprint, lightweight)**: earlier-phase or
  exploratory work, no stakeholder sign-off required yet, structure without full governance
  overhead.
- **Formal SAD**: stakeholder approval path required, regulated or high-criticality system,
  full governance needed before implementation starts.

A blueprint that gains stakeholder sign-off requirements should evolve into a Formal SAD in
place — don't fork a second document.

## Core Boundaries

- **Blueprint / SAD**: Describes the solution structure, major components, constraints, and
  architecture-level behavior.
- **ADRs**: Capture why a specific architectural decision was made. Reference them from the
  blueprint or SAD instead of repeating all decision rationale inline.
- **Runbooks**: Explain how to operate, deploy, recover, or support the system.
- **API Contracts and Detailed Specs**: Hold interface schemas, protocol details, and
  low-level design specifics.

If the request needs class design, endpoint-by-endpoint contracts, or step-by-step
operational guidance, link those artifacts instead of embedding them in full.

## Audience and Level of Detail

Write for multiple audiences without mixing abstraction levels:

- Executives and managers need a clear summary of purpose, scope, and solution shape.
- Architects and engineers need component boundaries, integration patterns, data flows, and
  quality attribute coverage.
- Operations, QA, and compliance readers need deployment, security, resilience, and control
  expectations at the architecture level.

Avoid class-by-class internals, full schemas, or large code examples. Non-functional
requirements are first-class architecture inputs and must be visible, not buried.

## Required Inputs

Gather or infer these before drafting:

- Business goals, scope, stakeholders, and constraints
- Functional requirements and key use cases
- Non-functional requirements such as performance, reliability, availability, scalability,
  security, compliance, and operability
- Existing architecture or current-state baseline
- Integration points, external dependencies, and data movement
- Platform, deployment, and infrastructure constraints
- Related ADRs, tickets, runbooks, diagrams, and interface documents

If critical inputs are missing, call out the gap explicitly rather than guessing.

## Recommended Structure

Adapt depth to project size, but cover these concerns explicitly:

1. **Document Control**: Version, date, authors, approvals, and change history. For a Formal
   SAD, this must include the stakeholder approval path; a blueprint may omit formal sign-off.
2. **Executive Summary**: Purpose, scope, business context, and intended audience.
3. **Architecture Vision / Overview**: Big-picture solution context and architecture
   approach.
4. **Requirements and Constraints**: Functional drivers, assumptions, dependencies, and
   technical constraints.
5. **Non-Functional Requirements**: Performance, scalability, reliability, security,
   compliance, observability, and how the architecture addresses them.
6. **Current and Target Architecture**: As-is and to-be views when migration, replacement,
   or modernization is involved.
7. **Solution Design**: Major services, modules, responsibilities, and interactions.
8. **Data and Integration Architecture**: Interfaces, events, APIs, data domains, data
   movement, and storage shape. For a Formal SAD, split this into separate **Data
   Architecture** and **Integration Architecture** sections for governance granularity.
9. **Security Architecture**: Authentication, authorization, encryption, trust boundaries,
   secrets, and compliance controls.
10. **Infrastructure and Deployment**: Hosting model, environments, network shape, CI/CD,
    and operational platform dependencies.
11. **Implementation / Transition Strategy**: Rollout phases, migration steps, sequencing,
    and rollback posture.
12. **Risks and Mitigations**: Material technical and delivery risks with responses.
13. **Appendices and References**: Glossary, assumptions, ADR links, runbooks, API specs,
    detailed diagrams, and related tickets.

## Diagram Guidance

Diagrams are part of the artifact, not decoration. Any diagram this skill produces must be
built with `../../puml-diagrams/SKILL.md` — load it before writing any diagram code.

- Use **C4 Context** and **C4 Container** diagrams as the baseline views.
- Add **component**, **deployment**, **sequence**, or **data flow** diagrams only where they
  materially improve understanding.
- Use **PlantUML**, per `../../puml-diagrams/SKILL.md`, as the default diagrams-as-code
  format for this repo. Only deviate (e.g. Mermaid, Structurizr) if the project already has
  an established diagramming toolchain in place.
- Store diagram source files in version control alongside the document.
- Avoid screenshots and hand-maintained images when a text-based source is practical.

## Authoring Workflow

Follow this sequence when generating or reviewing either tier:

1. Define the document scope, audience, formality tier, and architecture problem being
   addressed.
2. Gather requirements, NFRs, constraints, baseline context, and linked artifacts.
3. Draft the outline at the correct abstraction level before filling sections.
4. Map functional requirements and NFRs to architecture choices and call out gaps.
5. Add diagrams that explain context, containers, data flow, deployment, and trust
   boundaries.
6. Cross-link ADRs, tickets, runbooks, and interface documentation.
7. Review for consistency, completeness, staleness, and traceability.

## Governance and Lifecycle

- Store the document in version control near the codebase, usually under
  `docs/architecture/`.
- Use clear file names such as `SAD_v1.0.md` or a stable document name with version
  information in the document itself.
- Treat the document as living. Update it in place as the solution evolves and maintain
  document control and change history.
- Review changes through pull requests and require technical peer review; a Formal SAD
  additionally requires stakeholder sign-off before baseline.
- Mark obsolete sections clearly instead of leaving stale guidance in place.
- Archive retired or major superseded versions in a discoverable location.
- Treat ADRs differently: if a decision changes, create a new ADR and supersede the old one
  instead of rewriting history.

## Automation Expectations

Where the project supports it, include the document in docs-as-code automation:

- Markdown linting and link validation
- Diagram generation or verification for diagrams-as-code sources
- Static documentation publishing with tools such as MkDocs, Docusaurus, or similar
- Template or metadata consistency checks where standards exist

The goal is to keep architecture documentation current through normal engineering workflow,
not occasional cleanup drives.

## Review Signals

When evaluating quality or documentation health, look for:

- Freshness relative to recent code and architecture changes
- Coverage of major decisions via linked ADRs
- Evidence of use in pull requests, tickets, or onboarding material
- Clear ownership and a visible review cadence

## Suggested Repo Layout

```text
project-root/
├─ docs/
│  ├─ architecture/
│  │   ├─ SAD_v1.0.md
│  │   ├─ overview.md
│  │   ├─ components/
│  │   └─ diagrams/
│  ├─ decisions/
│  │   ├─ 0001-example.md
│  │   └─ index.md
│  ├─ runbooks/
│  ├─ api/
│  └─ README.md
└─ README.md
```

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Documentation theater | Long documents that consume authoring effort without informing any decision | Cut to what stakeholders actually need to decide or build; delete filler sections |
| Stale diagrams or prose | Readers trust an architecture that no longer exists | Review diagrams and prose on the same cadence as the code they describe |
| Overdetail | Turns the document into low-level design, burying the architecture-level decision | Link out to code, API specs, or class diagrams instead of embedding them |
| Fragmented storage across unlinked repos, drives, or wikis | No single source of truth; copies silently drift apart | Store in version control alongside the codebase, per Suggested Repo Layout |
| Unowned documents | Never reviewed, goes stale without anyone noticing | Assign an owner and review cadence, per the Governance and Lifecycle section |
| Unlinked artifacts | Readers manually rediscover rationale that already exists elsewhere | Cross-link ADRs, tickets, runbooks, and interface docs directly |
| Forking a second document | Two competing sources of truth for the same architecture | Promote the blueprint to a Formal SAD in place instead of starting a new file |

## Pre-flight checklist — run before delivering any solution architecture document

- [ ] The document clearly distinguishes its content from ADRs, runbooks, and API specs
- [ ] The intended audience and formality tier (Blueprint vs Formal SAD) are clear
- [ ] Functional requirements and NFRs are both visible and mapped to the architecture
- [ ] Current and target architecture are distinguished where transformation is in scope
- [ ] Security, data, integration, infrastructure, and deployment are addressed explicitly
- [ ] Diagrams use a standard notation and are maintained as versioned source artifacts
- [ ] Document control, version history, and linked references are present
- [ ] If this is a Formal SAD, the stakeholder approval path is documented
- [ ] Risks, assumptions, dependencies, and transition concerns are not omitted
- [ ] Outdated or superseded content is marked, updated, or archived
