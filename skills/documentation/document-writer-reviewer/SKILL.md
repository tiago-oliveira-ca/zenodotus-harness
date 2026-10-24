---
name: document-writer-reviewer
description: >
  Review, rewrite, and normalize software delivery documents — BRDs, PRDs, FSDs/FRDs, NFRs,
  TRDs, ADRs, SADs, Epics/Stories, runbooks/postmortems, and developer handoff packages. Use
  when a document is incomplete, inconsistent, weakly structured, or needs to be upgraded
  into a cleaner, more traceable artifact. Trigger on: "review this document", "improve this
  doc", "rewrite this spec", "make this cleaner", "this needs polish", "review my BRD / PRD /
  FSD / NFR / TRD / ADR / SAD / epic / runbook", "audit this document", "what's missing from
  this spec", or any request to evaluate and strengthen a software delivery document.
---

# Document Writer Reviewer

Use this skill to turn raw notes, uneven drafts, or weakly governed delivery documents into
cleaner artifacts that teams can review, approve, and execute against.

## Core Goal

Produce documentation that is:

- structurally coherent
- explicit about scope, ownership, and status
- traceable across business, functional, technical, testing, architectural, and operational layers
- precise enough to guide implementation or governance review

## Artifact Router

Choose the review lens based on the document type:

- **BRD**: Business value, scope boundaries, objectives, success measures, stakeholders
- **PRD**: Product vision, personas, user stories, prioritized features, success metrics
- **FSD / FRD**: User behaviors, flows, edge cases, functional requirements, acceptance
  criteria
- **NFR**: Measurable performance, availability, security, scalability, compliance, and DR
  targets with verification methods
- **TRD / SRS**: Technical constraints, interfaces, environments, verification methods,
  traceable requirement statements
- **ADR**: Context, options, decision, status, and consequences
- **SAD / Blueprint**: System structure, NFR coverage, integration, data, security,
  infrastructure, rollout
- **Epic / Story / Task**: Traceability to a SAD component and requirement, acceptance
  criteria, Definition of Ready/Done, right-sized scope (INVEST)
- **Runbook / Postmortem**: Executable procedures, alert-to-action mapping, escalation paths,
  blameless root cause, owned action items
- **Developer Handoff**: Design assets, tokens, states, implementation notes, QA checks

If the artifact type is unclear, infer it from scope and audience, then state that choice.

## Review Workflow

1. Identify the artifact type, audience, and intended use.
2. Preserve the original intent, but remove ambiguity, redundancy, and structural drift.
3. Normalize the document into a clear section hierarchy with document control where needed.
4. Tighten language so requirements and decisions are testable, traceable, and attributable.
5. Call out missing information, unresolved assumptions, or governance gaps explicitly.
6. Mark content you add beyond the supplied material as **[Recommended Enhancement]**.

## Writing Rules

- Use `shall` for mandatory requirements and `should` for recommendations.
- Replace vague language such as `fast`, `secure`, `robust`, or `user-friendly` with
  measurable criteria or named standards.
- Keep business rationale separate from technical design and operational procedure.
- Prefer tables, IDs, checklists, and clear headings over long narrative blocks when they
  improve execution clarity.
- Preserve traceability between related artifacts when IDs or links already exist.
- Execute every runnable command a document embeds before delivery, or mark it explicitly
  `TODO-VERIFY: unexecuted` — a copied "verify with:" command is a claim, not a fact, and its
  embedded commands are part of the document's testable surface. When the same command appears
  in multiple files, flag the duplication as a maintenance risk.

## Shared Quality Checks

Review every document for these cross-cutting concerns:

- **Governance**: version, status, ownership, approval path, auditability
- **Traceability**: business need to requirement to design to test where applicable
- **Precision**: one requirement or decision per statement where possible
- **Actionability**: implementation, validation, or approval steps are clear
- **Completeness**: assumptions, dependencies, risks, and exceptions are not hidden

## Issue Severity Classification

When surfacing review findings, classify each issue so readers know what to fix first:

| Severity | Label | Definition | Example |
|---|---|---|---|
| **Critical** | `[CRITICAL]` | Blocks approval or creates compliance/legal risk | No approval path, undefined scope, regulation missed |
| **Major** | `[MAJOR]` | Significant gap that will cause rework or ambiguity in delivery | Missing acceptance criteria, orphan requirement, untraceable decision |
| **Minor** | `[MINOR]` | Structural or clarity issue that reduces quality but is fixable quickly | Vague wording, inconsistent terminology, missing ID |
| **Enhancement** | `[Recommended Enhancement]` | Content added beyond original material that would improve the document | Missing risk section, suggested success metric |

Surface Critical and Major issues before Minor ones. Never bury blockers in a list of nits.

## Output Expectations

When rewriting or reviewing:

- identify the document type
- surface the highest-risk gaps first using severity labels
- keep edits implementation-ready rather than academic
- use the most appropriate structure for the artifact instead of forcing one generic template

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Vague language (`fast`, `secure`, `robust`, `user-friendly`) | Measurable criteria or named standards |
| Multiple requirements or decisions packed into one statement | One requirement or decision per statement |
| Business rationale mixed into technical design or operational procedure | Keep the three layers separate |
| Long narrative blocks where execution clarity matters | Tables, IDs, checklists, and clear headings |
| Blockers buried in a list of nits | Surface Critical and Major issues before Minor ones |
| Silently adding content beyond the supplied material | Mark additions as **[Recommended Enhancement]** |
| Forcing one generic template onto every artifact | Use the most appropriate structure for the artifact type |
| Rewriting away the original intent | Preserve intent; remove only ambiguity, redundancy, and structural drift |
| Leaving the artifact type ambiguous | Infer it from scope and audience, then state that choice |
| Hiding assumptions, dependencies, or risks | Call out missing information and governance gaps explicitly |
| Delivering a doc with unexecuted embedded commands | Run each runnable command during authoring, or mark it `TODO-VERIFY: unexecuted` |

## Pre-flight checklist — run before delivering any document review

- [ ] Scope, audience, and document purpose are explicit
- [ ] Terminology is consistent and undefined acronyms are resolved
- [ ] Requirements or decisions are atomic and testable where applicable
- [ ] Ownership, status, and approval expectations are clear
- [ ] Missing dependencies, assumptions, or risks are called out directly
- [ ] The document is suitable for repository `docs/` storage or formal review
- [ ] Every embedded runnable command was executed during authoring or carries an explicit `TODO-VERIFY` marker
