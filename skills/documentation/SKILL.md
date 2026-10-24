---
name: documentation
description: >
  Software delivery documentation dispatcher. Routes to the correct document standard for the
  artifact being written or reviewed, following the BRD -> PRD -> FRD/NFR -> TRD -> SAB -> SAD
  -> ADR lifecycle. Use whenever creating, reviewing, auditing, or improving any software
  project document. Trigger on: "write a BRD", "PRD", "product requirements", "functional spec",
  "FRD", "TRD", "NFR", "document review", "business requirements", "acceptance criteria",
  "developer handoff", "write an ADR", "architecture decision", "write a SAD", "solution
  architecture", "traceability", "epic", "user story", "feature list", "roadmap", "release
  plan", "prioritize features", "MoSCoW", "RICE", "runbook", "postmortem", "go-live
  checklist", or any request to produce or improve a software delivery document.
---

# Documentation Dispatcher

When a documentation task is requested, identify the document type and load the appropriate
sub-skill before writing or reviewing any content. For the full lifecycle diagram, stage
ownership, governance table, and traceability model, read
[`references/lifecycle.md`](references/lifecycle.md) — load it whenever a task spans
multiple document types, needs the full BRD-to-Operations sequence, or needs the
governance/traceability model. For the ADR template itself, load
`architecture-documentation-and-decision-records/SKILL.md` directly.

## Routing Table

Ordered by lifecycle stage (BRD → PRD → FRD/NFR → TRD (optional) → SAB → SAD → ADR → Feature
Planning → Development Planning), with Developer Handoff, Operations, and Document Review as
artifact types that apply alongside rather than strictly after this main chain:

| Document Type | When to Use | Sub-skill to load |
|---|---|---|
| Business Requirements Document (BRD) | Capturing business intent, project scope, stakeholders, success criteria | `business-requirements-standards/SKILL.md` |
| Product Requirements Document (PRD) | Product vision, personas, user stories, prioritized features, success metrics | `product-requirements-standards/SKILL.md` |
| Functional Requirements / Specification Document (FRD / FSD) | Defining system behavior, user flows, acceptance criteria, use cases | `functional-specification-standards/SKILL.md` |
| Non-Functional Requirements (NFR) | Dedicated performance, availability, security, scalability, compliance, or DR targets | `non-functional-requirements-standards/SKILL.md` |
| Technical Requirements Document (TRD / SRS) | Technically precise, testable, traceable system requirements | `technical-requirements-standards/SKILL.md` |
| Solution Architecture (Blueprint or Formal SAD) | Exploratory blueprint or fully governed SAD with stakeholder approval, security, data, integration, and transition | `solution-architecture-standards/SKILL.md` |
| Architecture Decision Records (ADRs) | Capturing why a decision was made, decision logs, ADR templates — continuous, alongside SAB/SAD/implementation | `architecture-documentation-and-decision-records/SKILL.md` |
| Feature List & Development Plan | Naming/sizing features, a feature-list table, prioritization (MoSCoW/RICE/Kano/Value-vs-Effort), roadmap vs. release plan | `feature-planning-standards/SKILL.md` |
| Epics, Stories, Tasks (Development Planning) | Breaking a SAD component or feature into sprint-ready work; Definition of Ready/Done, story splitting | `development-planning-standards/SKILL.md` |
| Designer-to-Developer Handoff | Packaging design files, tokens, component states, assets for engineering | `developer-handoff-standards/SKILL.md` |
| Runbooks, incident response, postmortems, operational readiness | Operating, supporting, or recovering a system in production — closes the loop back into design | `operations-standards/SKILL.md` |
| Document Review & Improvement | Reviewing, rewriting, or auditing any existing delivery document of any type | `document-writer-reviewer/SKILL.md` |

## Downstream Stages (Outside This Dispatcher)

The lifecycle continues past documentation into other top-level skills in this repo:

| Stage | Skill to load |
|---|---|
| Implementation | `code-standards` (routes further by language/framework) |
| Code Review | `code-standards` (standards) + the `/code-review` command (review process) |
| Testing | `testing` (routes to test specification standards) |
| Deployment | `github-circleci-standards` (CircleCI) / `zeno-stack/zeno-deployment-patterns` (GitHub Actions, strategy, rollback) |
| Documenting production code | `documenting-code` (docstrings / API reference / README / drift) |

**Scope boundary:** this dispatcher owns **delivery documents** (BRD → PRD → FRD → ADR → SAD…).
Documenting *existing production code* — docstrings, API reference, READMEs, keeping docs in sync
with the code (drift) — is the `documenting-code` skill, not this dispatcher.

Development Planning and Operations both live inside this dispatcher
(`development-planning-standards/SKILL.md` and `operations-standards/SKILL.md` in the
Routing Table above), not outside it — both produce documentation artifacts (Epics/Stories,
runbooks/postmortems) even though they sit either side of Implementation in the lifecycle.
See `references/lifecycle.md` for the full stage table, including agile ceremonies and
change management.

## Instructions

1. Identify the document type from the user's request or the artifact being worked on.
2. Load and apply **only** the matching sub-skill above.
3. If the request is to **review** an existing document, load `document-writer-reviewer`
   (cross-document review standards) **together with the matching document-type sub-skill**
   from the Routing Table when the document's type is known — e.g. reviewing an NFR loads both
   `document-writer-reviewer` and `non-functional-requirements-standards`. The reviewer's
   per-type lenses are condensed summaries; the type sub-skill carries the authoritative
   checklists (e.g. NFR verification-method rules), so on any conflict the **type sub-skill
   wins**. Use `document-writer-reviewer` alone only when the document type is unknown or the
   review spans mixed/multiple types.
4. If multiple document types are in scope, apply each sub-skill in sequence to its artifact,
   in lifecycle order where the request spans more than one stage.
5. If the request is about the process itself (e.g. "what's our documentation lifecycle",
   "what order do these documents go in"), read `references/lifecycle.md` and answer from it
   directly rather than loading a specific document-type sub-skill.
6. If the request is to write or review an Epic, Story, or Task, or to check Definition of
   Ready/Done, use `development-planning-standards`. For the surrounding process — agile
   ceremonies (architecture review, sprint planning, design review, code review) or change
   management (an issue triggering an ADR/SAD update) — read `references/lifecycle.md`'s
   dedicated sections and answer from those directly.
