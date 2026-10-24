# STS Example Tables

Use these as starting templates. Adapt column names and IDs to your project conventions.

---

## Test Design Specification (TDS) — Feature Entry

| Field | Value |
|---|---|
| **Test Design ID** | TDS-AUTH-001 |
| **Feature Set** | User Authentication |
| **Test Approach** | Functional testing with black-box input/output verification. Security testing via OWASP checklist. |
| **Pass/Fail Criteria** | All linked TCs pass; no High/Critical security findings. |
| **Linked Test Case IDs** | TC-LOGIN-001, TC-LOGIN-002, TC-LOGOUT-001, TC-SESSION-001 |
| **Risks** | Credential exposure, session fixation, brute-force attacks. |
| **Assumptions** | User DB seeded with 10 test accounts; SMTP mock enabled. |

---

## Test Case Specification (TCS) — Full Example

| Field | TC-LOGIN-001 | TC-LOGIN-002 | TC-LOGIN-003 |
|---|---|---|---|
| **Test Case ID** | TC-LOGIN-001 | TC-LOGIN-002 | TC-LOGIN-003 |
| **Objective (Req.)** | Verify valid login (REQ-123) | Verify invalid login error (REQ-124) | Verify account lock after 5 failed attempts (REQ-125) |
| **Priority** | High | High | High |
| **Type** | Functional | Functional | Security |
| **Preconditions** | User account exists; password = `Test@1234` | No preconditions | User account exists |
| **Steps** | 1. Navigate to `/login`. 2. Enter valid username/password. 3. Click Submit. | 1. Navigate to `/login`. 2. Enter valid username, wrong password. 3. Click Submit. | 1. Navigate to `/login`. 2. Enter valid username, wrong password 5 times. |
| **Expected Result** | User redirected to `/dashboard`. Session cookie set. | Error message "Invalid credentials" displayed. No session created. | Account locked. Error "Too many attempts. Account locked." shown. Email alert sent to user. |
| **Automation Status** | Automated (Playwright) | Automated (Playwright) | Automated (Playwright) |
| **Script Location** | `tests/auth/test_login.py::test_valid_login` | `tests/auth/test_login.py::test_invalid_password` | `tests/auth/test_login.py::test_account_lockout` |

---

## Test Procedure Specification (TPS) — Manual Execution

| Field | Value |
|---|---|
| **Procedure ID** | TP-AUTH-MANUAL-001 |
| **Related TCs** | TC-LOGIN-001, TC-LOGIN-002, TC-LOGIN-003 |
| **Setup / Pre-steps** | 1. Deploy build `v2.3.1` to QA Staging. 2. Seed DB: run `scripts/seed_test_users.py`. 3. Clear browser cookies and cache. |
| **Procedure Steps** | 1. Launch the current major release of Chrome on QA Staging (`https://staging.app/login`). 2. Execute TC-LOGIN-001 steps; record actual result. 3. Clear cookies. 4. Execute TC-LOGIN-002 steps; record actual result. 5. Clear cookies. 6. Execute TC-LOGIN-003 steps; record actual result. |
| **Post-conditions / Notes** | Log actual results in TestRail Run `TRUN-2026-Q1-AUTH`. Open defects in Jira for any failures. |

---

## Requirements Traceability Matrix (RTM) — Example

| Req. ID | Req. Description | Test Case IDs | Execution Status | Defects |
|---|---|---|---|---|
| REQ-123 | Valid user login redirects to dashboard | TC-LOGIN-001 | Pass | — |
| REQ-124 | Invalid credentials show error message | TC-LOGIN-002 | Pass | — |
| REQ-125 | Account locks after 5 failed login attempts | TC-LOGIN-003 | Fail | BUG-047 |
| REQ-126 | Password reset via email | TC-PWD-001, TC-PWD-002 | Not Run | — |

---

## Risk Register — Example

| Risk ID | Risk Description | Category | Likelihood | Impact | Priority | Mitigation |
|---|---|---|---|---|---|---|
| RISK-001 | Payment processing failure | Business | Low | Critical | High | Dedicated payment smoke tests in every release. |
| RISK-002 | Session token exposed in URL | Security | Medium | High | High | Security TC covers OWASP A7; penetration test pre-release. |
| RISK-003 | Report generation slow under load | Performance | Medium | Medium | Medium | JMeter load test with 200 concurrent users. |
| RISK-004 | Admin UI broken in Firefox | Compatibility | Low | Low | Low | Manual cross-browser smoke test on major releases only. |

---

## Exit Criteria — Example

| Criterion | Target | Status |
|---|---|---|
| All planned test cases executed | 100% | — |
| Test case pass rate | ≥ 95% overall | — |
| Critical/High defects open | 0 (or explicitly deferred with PM sign-off) | — |
| Medium defects open | ≤ 3, all documented | — |
| Requirements coverage | 100% of in-scope Req. IDs have ≥1 Pass TC | — |
| Performance: API P95 response time | ≤ 200 ms under 500 concurrent users | — |
| Security: Critical OWASP findings | 0 | — |
| Accessibility: WCAG 2.2 AA | No Critical violations | — |
