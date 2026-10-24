---
name: zeno-github-ops
description: >
  GitHub repository operations via the gh CLI — issue triage, PR review readiness, CI/CD
  failure investigation, release management, and Dependabot/secret-scanning monitoring.
  Use for GitHub operational tasks beyond simple git commands: triaging a backlog, checking
  merge readiness, debugging a failing workflow run, cutting a release, or reviewing
  security alerts. Trigger on: "triage issues", "review PRs", "check CI status", "why did
  CI fail", "merge readiness", "cut a release", "generate a changelog", "stale issues",
  "stale PRs", "dependabot alerts", "secret scanning alerts", "gh CLI", or any GitHub
  operational task involving issues, PRs, workflow runs, releases, or contributors.
---

# GitHub Operations

Operating a GitHub repository day to day — issue triage, PR review readiness, CI failure
investigation, releases, and security monitoring — all via the `gh` CLI rather than the
web UI, so it's scriptable and repeatable. This is GitHub only; reviewing a Jira backlog's
structure belongs to `zeno-stack/zeno-jira-structure-review`.

## Prerequisites

`gh` CLI installed and authenticated (`gh auth login`) against the target repository.

## Issue Triage

Classify each issue by **type** (bug, feature-request, question, documentation,
enhancement, duplicate, invalid, good-first-issue) and **priority** (critical:
breaking/security, high: significant impact, medium: nice-to-have, low: cosmetic).

Workflow:
1. Read title, body, and comments.
2. Check for duplicates by keyword search.
3. Apply labels.
4. Questions → draft and post a response.
5. Bugs missing repro steps → ask for them before triaging priority.
6. Duplicates → comment with a link to the original, label `duplicate`.

```bash
gh issue list --search "keyword" --state all --limit 20      # duplicate check
gh issue edit <number> --add-label "bug,high-priority"
gh issue comment <number> --body "Thanks for reporting. Could you share reproduction steps?"
```

## PR Review Readiness

1. `gh pr checks <number>` — CI status.
2. `gh pr view <number> --json mergeable` — mergeable state.
3. Age and last activity — flag PRs idle >5 days with no review.
4. Community PRs specifically: confirm tests exist and conventions are followed before
   requesting changes on style alone.

## Staleness Policy

- Issues with no activity in 14+ days: label `stale`, comment asking for an update.
- PRs with no activity in 7+ days: comment asking if still active.
- Auto-close stale issues after 30 days of continued silence, labeled `closed-stale`.

```bash
gh issue list --label "stale" --state open
gh pr list --json number,title,updatedAt --jq '.[] | select(.updatedAt < "2026-03-01")'
```

## CI/CD Failure Investigation

1. `gh run view <run-id> --log-failed` — pull the failing step's logs.
2. Identify the failing step precisely; don't guess from the run summary alone.
3. Distinguish flaky-test noise from a real failure — a real failure gets root-caused (see
   `zeno-debug` for the investigation discipline), a flaky one gets noted as a pattern for
   later, not silently re-run into green.

```bash
gh run list --status failure --limit 10
gh run view <run-id> --log-failed
gh run rerun <run-id> --failed
```

Re-running a failure without reading the log first is the most common way CI flakiness goes
untracked — always read `--log-failed` before deciding it's flaky.

## Release Management

1. Confirm CI is green on `main`.
2. `gh pr list --state merged --base main --search "merged:>2026-03-01"` — unreleased
   changes since the last tag.
3. Generate the changelog from merged PR titles.
4. Cut the release.

```bash
gh release create v1.2.0 --title "v1.2.0" --generate-notes
gh release create v1.3.0-rc1 --prerelease --title "v1.3.0 Release Candidate 1"
```

## Security Monitoring

```bash
gh api repos/{owner}/{repo}/dependabot/alerts --jq '.[].security_advisory.summary'
gh api repos/{owner}/{repo}/secret-scanning/alerts --jq '.[].state'
gh pr list --label "dependencies" --json number,title
```

Review and auto-merge safe dependency bumps; flag critical/high-severity alerts
immediately rather than batching them into a weekly pass; check for new Dependabot alerts
at least weekly.

## Quality Gate

Before calling a GitHub-ops task complete:

- Every triaged issue has an accurate label.
- No PR older than 7 days sits without a review or comment.
- Every CI failure was investigated (log read), not just blindly re-run.
- Releases ship with an accurate changelog.
- Security alerts are acknowledged and tracked, not just visible in the dashboard.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Re-running a failed CI job without reading the log | `gh run view <run-id> --log-failed` first, root-cause before retrying |
| Labeling issues without reading the full thread/comments | Read title + body + comments before classifying |
| Letting PRs sit unreviewed past 5-7 days silently | Track staleness explicitly and comment/ping |
| Auto-closing stale issues immediately | 14-day stale label, then a further 30-day silence before close |
| Releasing with a hand-typed changelog | Generate from merged PR titles / `--generate-notes` |
| Treating a Dependabot alert as informational | Triage severity immediately; auto-merge only safe bumps |
| Requesting style changes on a community PR before checking it has tests | Confirm tests + conventions first |

## Pre-flight checklist — run before delivering any GitHub-ops result

- [ ] Every issue touched has a correct type + priority label
- [ ] No PR older than 7 days is unreviewed and uncommented
- [ ] Every CI failure was root-caused via logs, not assumed flaky
- [ ] Release changelog reflects actual merged PRs since the last tag
- [ ] Dependabot / secret-scanning alerts were checked and any critical/high items flagged
- [ ] `gh auth status` confirms the correct repo/account before destructive operations (merge, release, close)
