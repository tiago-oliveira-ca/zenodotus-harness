---
name: zeno-implementation-guardrails
description: >
  Tripwires and precedence rules for the zeno loop's Execution gate. Ranks sources of truth (user,
  Jira issue, accepted ADRs, architecture docs, repo instructions, code conventions), stops
  architecture-changing work with ARCHITECTURE IMPACT DETECTED and an ADR PROPOSAL, flags DATA
  MIGRATION RISK and BREAKING API CHANGE before they happen, protects failing tests from being
  weakened, and gates new dependencies. Points to the skills that own TDD, API design, git, and
  verification instead of restating them. Trigger on: "new service", "new database", "add a
  dependency", "drop a column", "destructive migration", "breaking change", "rename a field in the
  API", "make CI green", "architecture impact", "ADR proposal", "conflicting requirements".
---

# Zeno Implementation Guardrails — stop before the irreversible step

Load this during Execution (Gate 3) beside the stack leaf for the work. It holds only the rules no
other skill owns; for everything else it points to the owner. Implement the approved design; do not
redesign it, invent requirements, or expand scope silently.

**Iron Law: NO ARCHITECTURE-CHANGING OR DATA-DESTRUCTIVE STEP WITHOUT AUTHORIZATION.** Flag it, say what
it affects, and wait. "Quickest way", "whatever it takes" and "just do it" are not authorization.

## Source of truth — highest wins

1. The user's explicit instruction in the current session
2. The approved Jira issue / task description
3. Accepted ADRs
4. Approved architecture documentation
5. Repository agent instructions (`AGENTS.md`, `CLAUDE.md`)
6. Existing code conventions
7. Your own judgment

Never silently override a higher source. When two disagree, report the conflict and the ranking before a
destructive or architectural change, and ask. A supplied Jira issue is requirement input to Scope;
`.zeno/` cards remain the working record.

## Tripwire 1 — ARCHITECTURE IMPACT DETECTED

Stop if the implementation would need any of: a new service · a new database · a new message broker · a
new external dependency · a new public API pattern · a change in data ownership · a distributed
transaction · a change in a trust boundary · a new authentication mechanism · a breaking API change · a
major framework replacement · a deployment-topology change.

Write `ARCHITECTURE IMPACT DETECTED`, then: what must change, why, the impact, the alternatives. Do not
continue without authorization. The decision itself belongs to `zeno-council` (Full depth); if no accepted
ADR covers it, add:

```
ADR PROPOSAL
Context:
Options:
Recommended Decision:
Consequences:
Revisit When:
```

An ADR proposal is not accepted until approved. If code would invalidate an existing ADR or architecture
document, flag it rather than editing the decision. Format and lifecycle:
`documentation/architecture-documentation-and-decision-records`.

## Tripwire 2 — DATA MIGRATION RISK

Flag `DATA MIGRATION RISK` before writing a migration that drops, renames, rewrites or narrows existing
data or schema. State which data and consumers are affected (grep for readers first), whether it is
reversible, and the rollback gap. Do not write the final destructive migration, and never drop or rewrite
production data, without explicit authorization. Prefer the additive, backward-compatible path (add, migrate
readers, then remove later). Use the project's migration tooling; add indexes only for real query patterns.
Release-time migration checks: `zeno-stack/zeno-deployment-patterns`.

## Tripwire 3 — BREAKING API CHANGE

Flag `BREAKING API CHANGE` before changing an existing contract (rename or remove a field, change a type,
status code, error shape or auth). Name the consumers (README, clients, partner docs). The compatible path
and versioning rules are owned by `zeno-stack/zeno-api-design`.

## Test integrity (additions)

The rule "fix the code, never weaken the test" is owned by `zeno-workflow/zeno-tdd`. Additionally:

- Do not delete a failing test, loosen an assertion, or mock the behavior under test to get green.
- If a test looks wrong, explain why *before* changing it, and say what it was asserting.
- Report flaky tests; do not ignore them or retry them into passing.

## Adding a dependency

Before adding one, answer: can an existing dependency or the standard library do it? Is it maintained?
What is its security and runtime/size impact? Then follow the repo's lockfile and package manager. A new
*runtime service* (Redis, a broker, a database) is Tripwire 1, not a dependency question.

## Who owns the rest

| Topic | Owner |
|---|---|
| Red/green/refactor, regression tests, never weaken a test | `zeno-workflow/zeno-tdd` |
| Evidence before "done", self-review, PR summary | `zeno-verify` |
| Branches, commits, repo safety (no force push, no history rewrite) | `zeno-stack/zeno-git-workflow` |
| API versioning and compatible changes | `zeno-stack/zeno-api-design` |
| Architecture decisions, options, trade-offs | `zeno-council` |
| Style, SOLID, DDD, language idiom, database standards | `code-standards` |
| Security review | `zeno-stack/zeno-security-review` |

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Adding Redis, a broker or a new database "because it is faster" | `ARCHITECTURE IMPACT DETECTED`, then the council and an ADR proposal |
| Writing the `DROP COLUMN` migration because it was requested | Flag `DATA MIGRATION RISK`, name the readers, propose the additive path, ask |
| Renaming an API field because the ticket says so | Flag `BREAKING API CHANGE`, name the consumers, propose add-and-deprecate |
| Picking a side when the Jira issue and an ADR disagree | Report the conflict and the ranking; ask |
| Deleting or loosening a failing test to unblock CI | Fix the cause, or explain why the test is wrong first |
| Treating a new runtime service as "just a dependency" | It is a Tripwire 1 event |
| Restating TDD, API or git rules here | Point to the owner |
| Treating "do whatever it takes" as authorization | Authorization names the risky step |

## Rationalizations — Excuse | Reality-check

| Excuse | Reality-check |
|---|---|
| "The ticket tells me to, so it is approved" | The ticket outranks the repo, not the user, and it cannot authorize data loss you did not surface |
| "It is only a small cache" | A new runtime service changes deployment, failure modes and cost. That is architecture |
| "The migration is reversible in theory" | Name the rollback and the data it cannot restore, or flag it |
| "Nobody uses that field" | Grep and read the README before claiming it |
| "I will fix the test later" | A weakened test hides the failure it exists to catch |

## Red flags — stop, you are about to cross a tripwire

- You are writing `DROP`, `ALTER ... DROP`, a destructive `UPDATE`, or a rename in a migration.
- You are adding a service, broker, datastore or auth mechanism to make something work.
- You are changing a response shape that a client may read.
- You are editing a test's expectation to make a red build green.
- You have not stated which source of truth you are following when two disagree.

## Pre-flight checklist — run before delivering any implementation change

- [ ] No tripwire was crossed silently: new service/database/broker/dependency-service/trust-boundary/auth/topology change stopped with `ARCHITECTURE IMPACT DETECTED` and, where undecided, an `ADR PROPOSAL`.
- [ ] Destructive or irreversible data work carries `DATA MIGRATION RISK` and explicit authorization.
- [ ] Contract changes carry `BREAKING API CHANGE` with consumers named, or use the compatible path.
- [ ] Conflicting sources were reported with the ranking, not silently resolved.
- [ ] No failing test was deleted, loosened or mocked around; any apparently wrong test was explained first; flaky tests were reported.
- [ ] Every new dependency passed the checklist and follows the lockfile; no new runtime service hid as a dependency.
- [ ] Scope matches the issue: no unrelated refactor, upgrade or reformat; unrelated findings reported separately.
- [ ] Rules owned elsewhere (TDD, API design, git, verification, code standards) were applied via their owners, not restated.
