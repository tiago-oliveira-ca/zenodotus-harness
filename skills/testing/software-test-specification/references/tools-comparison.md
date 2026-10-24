# STS Tools Comparison

Use this reference when recommending or configuring a test management tool for an STS workflow.

---

## Comparison Table

| Tool | Type | Key STS Features | Strengths | Weaknesses |
|---|---|---|---|---|
| **TestRail** | Commercial SaaS | Test runs, cases (ID, title, preconditions, steps, expected), sections, custom fields, API. | Robust reports and metrics; requirement/test linkage; widely adopted; API for CI integration. | License cost; UI learning curve. |
| **Xray for Jira** | Jira Plugin | Test Case, Test Set, Test Plan issue types; preconditions; BDD/Gherkin support; automation results import. | Fully integrated with Jira; bidirectional traceability with Jira issues; supports Cucumber/Gherkin. | Requires Jira; complex schema; additional license cost. |
| **Azure Test Plans** | Cloud (Microsoft) | Requirement link, test case steps (Action/Expected), attachments, parameterization, test suites. | Integrated with Azure Boards and Repos; built-in tracking; supports manual and automated tests. | Complex setup; limited customization outside Microsoft ecosystem. |
| **Confluence Test Plan** | Wiki (Atlassian) | Free-form page template: scope, objectives, strategy, environment, test case tables, risk, exit criteria. | Collaborative, real-time editing; easy linking with Jira issues; low barrier to start. | Less formal; harder to enforce templates; no built-in metrics dashboard. |
| **PractiTest** | Commercial SaaS | Requirements, Test Sets, Test Cases, high customizability, live traceability matrix, visual dashboards. | Visual dashboards; live RTM; multiple project support; strong custom field support. | Commercial cost; UI can be overwhelming; custom field setup required. |

---

## Selection Guidance

| Context | Recommended Tool |
|---|---|
| Team already uses Jira | Xray for Jira |
| Team already uses Azure DevOps | Azure Test Plans |
| Regulated domain needing formal RTM | TestRail or PractiTest |
| Lightweight / startup / early-stage | Confluence Test Plan |
| Large enterprise, multiple projects | PractiTest |

---

## Minimum Fields to Configure in Any Tool

Regardless of the tool, ensure the following fields exist on every test case:

- `Test Case ID` (unique, auto-generated or manual)
- `Title / Objective`
- `Linked Requirement ID(s)` (for RTM)
- `Preconditions`
- `Steps` (numbered)
- `Expected Result`
- `Priority` (High / Med / Low)
- `Type` (Functional / Non-Functional / Regression / Smoke)
- `Automation Status` (Manual / Automated)
- `Script Location` (if Automated)
- `Execution Status` (Not Run / Pass / Fail / Blocked / Skip)
- `Defects Found` (linked bug IDs)
