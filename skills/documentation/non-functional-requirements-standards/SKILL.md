---
name: non-functional-requirements-standards
description: >
  Standards for Non-Functional Requirements (NFR) documents covering performance, availability,
  security, scalability, compliance, and disaster recovery — dedicated, measurable, testable
  quality targets separate from what the system does. Trigger on: "write NFRs", "non-functional
  requirements", "quality attributes", "performance requirements", "SLA", "SLO", "disaster
  recovery requirements", "compliance requirements", "scalability requirements", or any document
  defining measurable system-wide constraints. For NFRs folded inline into a broader TRD, use
  technical-requirements-standards; use this skill when NFRs need dedicated depth — regulated
  systems, formal SLAs, multi-team RTO/RPO.
---

# Non-Functional Requirements Standards

Use this skill when defining or reviewing the quality attributes a system must meet — how
well it performs, not what it does. NFRs should be measurable and verifiable, never vague
adjectives.

## Core Boundaries

- **FSD / FRD** defines what the system does — functional behavior.
- **NFR** defines how well the system must do it — quality attributes and constraints.
- **TRD** defines the technical requirements that implement both, and may reference NFRs.
- **SAD** defines the architecture that realizes NFR targets (e.g. multi-region for
  availability, encryption at rest for security).
- **STS** (testing tree: `../../testing/software-test-specification/SKILL.md`, §10)
  defines the non-functional *tests* that verify these targets — every measurable NFR
  here should be traceable to a verification entry there.

## Required Inputs

- Business criticality tier of the system or feature
- Compliance or regulatory regime (e.g. SOC2, HIPAA, PCI-DSS, GDPR)
- Expected load, growth projections, and peak traffic patterns
- Existing SLAs/SLOs and any contractual obligations
- RTO/RPO targets and data sensitivity classification

## Recommended NFR Structure

1. **Document Control**: version, authors, dates, status, approvals
2. **Purpose and Scope**
3. **Performance**: latency, throughput, resource limits
4. **Availability and Reliability**: uptime targets, failover expectations
5. **Security**: authentication, authorization, data protection, audit requirements
6. **Scalability**: growth targets, horizontal/vertical scaling expectations
7. **Compliance**: applicable regulations and certification requirements
8. **Disaster Recovery**: RTO, RPO, backup and restore expectations
9. **Verification and Traceability**

## Writing Rules

- Every NFR must be a measurable, testable target — never a vague adjective like "fast",
  "secure", or "scalable" on its own.
- Assign a verification method per requirement (load test, audit, chaos drill, penetration
  test, synthetic monitor).
- Tie every NFR to a business driver, contractual SLA, or regulatory citation — an NFR with
  no rationale invites scope negotiation later.
- Version targets explicitly; NFR targets change as scale and criticality grow.
- Separate "must meet at launch" from "must scale to by year N" targets.

## Quality Attribute Targets

Every NFR should pass this test before inclusion:

| Category | Bad Example | Good Example |
|---|---|---|
| **Performance** | "The system should be fast" | "P95 latency ≤ 200ms at 500 RPS sustained" |
| **Availability** | "The system should be highly available" | "99.95% uptime monthly, measured via external synthetic monitor" |
| **Security** | "The system should be secure" | "Passes OWASP ASVS Level 2; zero critical findings in quarterly pentest" |
| **Scalability** | "The system should scale well" | "Handles 3x current peak load with autoscaling completing within 5 minutes" |
| **Compliance** | "The system should be compliant" | "Passes SOC2 Type II annual audit with zero material findings" |
| **Disaster Recovery** | "The system should be able to recover" | "RTO ≤ 4 hours, RPO ≤ 15 minutes for tier-1 services" |

## Anti-pattern quick reference

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Adjective without a number | Untestable, unenforceable | Attach a measurable threshold and measurement method |
| NFRs buried in a TRD appendix without an owner | Ignored during design and review | Give NFRs a clearly-owned section (inline in a TRD is fine) or a dedicated document — the problem is missing ownership/visibility, not the location |
| One target for all environments | Prod target applied to staging load tests | State environment-specific targets where they differ |
| No verification method | No one knows how to prove compliance | Assign test, analysis, demonstration, or inspection per NFR |
| Security treated as a feature, not a constraint | Bolted on late, inconsistently applied | Document security NFRs alongside performance/availability, not separately |
| Missing DR targets | Recovery expectations discovered during an incident | Always specify RTO/RPO per criticality tier before launch |

## Review Workflow

1. Confirm business criticality tier and applicable compliance regime.
2. Check every NFR has a numeric or binary, testable target.
3. Confirm each NFR has an assigned verification method.
4. Validate RTO/RPO and security targets are explicit, not assumed.
5. Trace each NFR to a business driver, SLA, or regulation.

## Pre-flight checklist — run before delivering any NFR document

- [ ] Every NFR has a measurable target, not a vague adjective
- [ ] Every NFR has a verification method
- [ ] Performance, availability, security, scalability, compliance, and DR are all addressed
- [ ] RTO/RPO targets are explicit for the system's criticality tier
- [ ] Each NFR traces to a business driver, SLA, or regulatory requirement
- [ ] Environment-specific targets are called out where they differ from production
