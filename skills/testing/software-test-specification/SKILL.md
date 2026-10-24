---
name: software-test-specification
description: >
  Comprehensive standards for writing Software Test Specification (STS) documents following
  IEEE 829 and ISO/IEC/IEEE 29119. Use this skill whenever you need to create, review, or
  improve test specifications — including Test Design Specifications (TDS), Test Case
  Specifications (TCS), and Test Procedure Specifications (TPS). Trigger on: "STS", "TDS",
  "TCS", "TPS", "write test cases", "test specification", "requirements traceability matrix",
  "RTM", "risk-based testing", "exit criteria", "test procedure", "test environment", "CI/CD
  test integration", "IEEE 829", "document how to test this feature", or non-functional testing
  (accessibility, security, performance).
---

# Software Test Specification (STS) Standards

A **Software Test Specification (STS)** defines *what* will be tested and *how*. It ties requirements to detailed test designs, cases, and procedures, enabling systematic, repeatable testing with clear accountability. These standards follow **IEEE Std 829** and **ISO/IEC/IEEE 29119**.

---

## 0. Test Type Decision Matrix

Before writing test cases, determine the correct test level and type:

| Test Level | Scope | Written By | When to Use |
|---|---|---|---|
| **Unit** | Single function/class | Developer | Validate business logic, pure functions, algorithms |
| **Integration** | Module interactions | Developer / QA | Test DB calls, API clients, message consumers |
| **System** | Full application | QA | End-to-end flows through the deployed system |
| **Acceptance (UAT)** | Business scenarios | Business analyst / end-user | Validate against BRD objectives and success criteria |

| Test Type | Purpose | Coverage Goal |
|---|---|---|
| **Functional** | Does the system do what it should? | Happy path + edge cases |
| **Regression** | Did a change break existing behavior? | Previously passing cases |
| **Performance / Load** | Does it handle expected load? | P95/P99 latency thresholds |
| **Security** | Are vulnerabilities present? | OWASP Top 10, auth, injection |
| **Accessibility** | Is it usable by everyone? | WCAG 2.2 AA success criteria |
| **Exploratory** | Discover unknown unknowns | Risk-based, unscripted sessions |
| **Smoke** | Is the build basically working? | Critical path only, fast |

Include the relevant test types in the STS scope section. Do not write separate STSes for each type unless the scale or audience requires it.

---

## 1. Purpose and Scope

An STS answers: **what features are tested, how they are tested, and what constitutes pass/fail.**

> **"Test plan" requests.** This skill produces a **test specification** (TDS/TCS/TPS), not a
> standalone IEEE 829 *Test Plan* document. The planning content a test plan needs is covered
> here across sections — scope/objectives (§1), test environment (§4.2), risk-based
> prioritisation (§5), exit criteria (§6), and schedule via CI/CD integration (§9) — so assemble
> a lightweight test plan from those. A separate master Test Plan document (org-level resourcing,
> staffing, multi-project schedule) is out of scope for this skill.

Every STS must define:
- **In-scope features/modules** — functions and behaviors explicitly covered.
- **Out-of-scope features** — items explicitly excluded (prevents scope creep).
- **Test objectives** — linked to requirement IDs or user story IDs.
- **Assumptions** — e.g., "Supported browsers: the current and previous major release of Chrome and Firefox."

**Checklist:**
- [ ] Scope explicitly lists in-scope and out-of-scope items.
- [ ] Objectives align to requirement IDs.
- [ ] Assumptions (data, environment, user roles) are listed.

---

## 2. STS Document Structure

Per IEEE 829 / ISO 29119, a complete Test Specification comprises three documents:

### 2.1 Test Design Specification (TDS)
Answers **what** to test and defines the high-level approach for each feature set.

Key fields: `Test Design ID`, `Feature/Feature Set`, `Test Approach`, `Pass/Fail Criteria`, `Linked Test Case IDs`, `Assumptions/Risks`.

### 2.2 Test Case Specification (TCS)
Answers **with what data** — inputs, outputs, and constraints for each test.

Key fields: `Test Case ID`, `Objective (Req. ID)`, `Preconditions`, `Steps`, `Expected Result`, `Priority (High/Med/Low)`, `Type (Functional/NFR/Regression)`.

**Example:**

| Test Case ID | Objective (Req.) | Preconditions | Steps | Expected Result |
|---|---|---|---|---|
| TC-LOGIN-001 | Valid login (REQ-123) | User account exists | 1. Open login. 2. Enter valid credentials. 3. Submit. | Dashboard loads. |
| TC-LOGIN-002 | Invalid login error (REQ-124) | — | 1. Open login. 2. Enter wrong password. 3. Submit. | Error "Invalid credentials" shown. |

### 2.3 Test Procedure Specification (TPS)
Answers **how** to execute — step-by-step instructions for environment setup and test execution.

Key fields: `Procedure ID`, `Related Test Case IDs`, `Preconditions/Setup`, `Steps`, `Data Requirements`, `Environment Requirements`, `Post-conditions`.

**Example:**

| Procedure ID | Related TCs | Setup | Procedure Steps | Post-conditions |
|---|---|---|---|---|
| TP-LOGIN-MANUAL | TC-LOGIN-001, 002 | DB seeded with test user data. | 1. Launch browser on test server. 2. Navigate to `/login`. 3. Execute steps per each TC. | Log actual results. |

> See `references/examples.md` for extended example tables.

**Checklist:**
- [ ] All testable features appear in the TDS.
- [ ] Each test case has a unique ID, purpose, steps, and expected result.
- [ ] Each procedure references TCS IDs and required environment/data.
- [ ] Pass/fail criteria are defined per feature.

---

## 3. Traceability to Requirements

Maintain a **Requirements Traceability Matrix (RTM)** to prove every requirement is tested and every test maps to a requirement.

**RTM minimum fields:**

| Req. ID | Req. Description | Linked TC IDs | Execution Status | Defects Found |
|---|---|---|---|---|
| REQ-123 | Valid user login | TC-LOGIN-001 | Pass | — |
| REQ-124 | Invalid login error message | TC-LOGIN-002 | Fail | BUG-045 |

**Checklist:**
- [ ] Every requirement has ≥1 linked test case (forward traceability).
- [ ] Every test case maps back to a valid requirement (backward traceability).
- [ ] Test cases include the `Req. ID` field.
- [ ] Orphan requirements or orphan test cases are reviewed and resolved.
- [ ] RTM is updated after each test execution cycle and defect triage.

---

## 4. Test Data and Environment Management

### 4.1 Test Data
Document the data needed before writing procedures — vague data requirements are a common source of false passes.

- List data types needed (valid inputs, invalid inputs, edge cases, large datasets).
- Specify how data is created or sourced (seeded scripts, anonymized prod exports).
- Note anonymization requirements for PII/PHI (PCI/HIPAA compliance).
- Define data readiness criteria (e.g., "inventory DB seeded with ≥100 SKUs").

### 4.2 Test Environment
Specify the target environment precisely so any tester can reproduce it.

- Hardware, OS versions, network topology.
- Application version under test (build number/tag).
- External dependencies (APIs, databases, message queues) with versions.
- Use version-controlled IaC (Docker Compose, Terraform, K8s manifests) for reproducible provisioning.

**Checklist:**
- [ ] Data needs (range, format, dependencies) documented per test case.
- [ ] Sensitive data masked or replaced (never use production PII in test environments).
- [ ] Environment specified by name/ID and version (e.g., "QA Staging: v2.3").
- [ ] Environment provisioning is scripted and version-controlled.

---

## 5. Test Prioritization and Risk-Based Testing

Prioritize test effort by **risk = likelihood × impact**, not by feature list order.

**Risk identification steps:**
1. Brainstorm technical and business risks (e.g., "payment processing failure," "data breach").
2. Rate each risk by likelihood (High/Med/Low) and impact (High/Med/Low).
3. Tag test cases with a corresponding priority label.
4. Schedule high-priority test cases to run first and with automation.

**Checklist:**
- [ ] Risks are documented (risk register or test plan section).
- [ ] Each feature/requirement is rated by risk/severity.
- [ ] Test cases include a `Priority` field (High/Med/Low).
- [ ] Test execution order starts with High-priority cases.
- [ ] Risk priorities are revisited when requirements or code change.

---

## 6. Metrics and Exit Criteria

Testing ends when objective criteria are met — not when time runs out.

**Common exit criteria:**
- All planned test cases executed.
- No open Critical or High severity defects (or all explicitly deferred with sign-off).
- ≥X% functional test pass rate (agree the threshold with stakeholders).
- Code coverage ≥Y% (if applicable).
- Performance benchmarks met (response times, load profiles).
- Security scan: no Critical OWASP findings.

**Metrics to track continuously:**
- Test case pass/fail rate by feature and priority.
- Defect trend (open, closed, re-opened per sprint).
- Requirements coverage % (how many Req. IDs have ≥1 executed TC).

**Checklist:**
- [ ] Exit criteria are explicit and agreed with stakeholders before testing starts.
- [ ] Coverage targets (functional and/or code) are defined.
- [ ] Performance and security benchmarks (if in scope) are specified.
- [ ] Metrics are collected automatically via CI or test management tool.
- [ ] Criteria are updated if scope changes.

---

## 7. Review and Approval Workflow

1. **Draft** — QA author creates TDS/TCS/TPS.
2. **Peer Review** — QA Lead, Dev Lead, Product Owner review for completeness and correctness.
3. **Revise** — Incorporate feedback; track all comments.
4. **Approval/Baseline** — Formal sign-off before test execution begins.
5. **Re-review** — Required after any significant requirement change.

**Checklist:**
- [ ] Reviewers (QA, dev, product) identified for each document.
- [ ] Review checklist used (traceability, completeness, clarity, correct expected results).
- [ ] All review comments tracked and resolved.
- [ ] Document has a version history and approval record.
- [ ] STS is baselined before test execution begins.

---

## 8. Versioning and Change Control

Treat the STS as a configuration-managed artifact.

- Begin each document with a **Revision History** table: `Version | Date | Author | Summary of Changes | Approver`.
- Store master copies in a CM system (Git, Confluence, SharePoint) with backups.
- Archive outdated versions as read-only.
- When a requirement changes, raise a change request, update affected TDS/TCS/TPS, and re-execute regression tests for changed areas.

**Checklist:**
- [ ] Version ID and date on every document revision.
- [ ] Change-log table maintained.
- [ ] Outdated versions archived (not deleted).
- [ ] Requirement change triggers test case review and update.

---

## 9. Automation and CI/CD Integration

For pipeline design itself (workflows, jobs, secrets, environment promotion), apply the
top-level `github-circleci-standards` skill (CircleCI) or `zeno-stack/zeno-deployment-patterns` (GitHub Actions, platform-neutral strategy); this section covers how test documentation
maps onto whatever pipeline exists.

Tag each test case as `Automated` or `Manual` in the TCS. For automated tests:

- Specify framework/tool (e.g., Pytest, Selenium, Playwright, JMeter) and script location.
- Document CI/CD trigger (e.g., "All automated regression tests run on every PR merge to `main`").
- Ensure CI environment matches STS environment spec (same OS, DB version, container image).
- Map CI test results (JUnit XML / NUnit XML) back to STS test case IDs in your test management tool.

**Checklist:**
- [ ] Automated tests linked to corresponding TCS entries.
- [ ] CI/CD pipeline steps for running tests are documented.
- [ ] CI environment matches the STS environment specification.
- [ ] Test result reports flow into the RTM / test management tool.
- [ ] Script maintenance plan is in place (update STS when scripts change).

---

## 10. Non-Functional Testing

Non-functional tests must appear in the STS — they are not an afterthought. The targets
these tests verify come from the NFR document — source them from
`../../documentation/non-functional-requirements-standards/SKILL.md` artifacts rather
than inventing thresholds in the test spec.

### 10.1 Accessibility
- Include test cases for WCAG 2.2 AA compliance (keyboard navigation, screen-reader compatibility, color contrast ratios, alt-text).
- Reference: Section 508, EN 301 549, WCAG 2.2 (the current W3C Recommendation).

### 10.2 Security
- Add test cases for OWASP Top 10 risks relevant to the feature (SQL injection, XSS, broken auth, etc.).
- Include security acceptance criteria in exit criteria (e.g., "No Critical OWASP findings").

### 10.3 Performance
- Define load profiles (concurrent users, transactions per second) and acceptable response times.
- Specify tools (e.g., JMeter, k6, Locust) and test data volumes.

**Checklist:**
- [ ] Accessibility test cases included for each UI feature (keyboard, screen-reader, contrast).
- [ ] Security test cases defined for high-risk areas (auth, input fields, APIs).
- [ ] Performance test plan (load profiles, tools, thresholds) documented.
- [ ] Non-functional requirements with quantitative targets appear in the STS.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Outdated test cases after requirement changes | Version control + change request process (§8) |
| Missing traceability | Enforce Req. ID field in TCS template |
| Vague test steps ("verify the page works") | Require explicit expected result for every step |
| Skipping non-functional tests | Include NFR section in TDS checklist |
| Over-engineered procedures | Balance detail vs. readability — aim for any qualified tester to follow |

---

## Reference Files

- `references/examples.md` — Extended test case and procedure table examples.
- `references/tools-comparison.md` — Comparison of STS tools: TestRail, Xray, Azure DevOps, Confluence, PractiTest.

---

## Pre-flight checklist — run before delivering any STS

Before delivering a test specification (TDS/TCS/TPS or a full STS), verify:

- [ ] **Right test type**: the artifact matches the §0 decision matrix for the level being specified.
- [ ] **Structure**: TDS, TCS, and TPS are distinguished (§2); each test case has ID, preconditions, steps, and an explicit expected result per step.
- [ ] **Traceability**: every test case carries a requirement ID; the RTM links requirements → cases both ways (§3).
- [ ] **Data & environment**: test data source and environment are specified, with no secrets committed (§4).
- [ ] **Risk-based prioritisation**: cases are prioritised by risk, not written uniformly (§5).
- [ ] **Exit criteria**: measurable pass/coverage/defect thresholds are stated (§6), not left implicit.
- [ ] **Non-functional coverage**: accessibility, security, and performance are addressed or explicitly scoped out (§10).
- [ ] **CI/CD hook**: automation and pipeline integration are specified where applicable (§9).
- [ ] **Version control**: change-control and versioning approach is stated so cases don't drift from requirements (§8).
