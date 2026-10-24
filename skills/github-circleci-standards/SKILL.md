---
name: github-circleci-standards
description: >
  Standards for GitHub repository governance and CircleCI CI/CD pipelines (the house CI),
  including Astronomer/Airflow deployment patterns. Use when designing, reviewing, or
  implementing CircleCI pipelines, branch protection, repo secrets management, or
  multi-environment promotion on CircleCI. GitHub *Actions* pipeline mechanics and
  platform-neutral deployment strategy/rollback/readiness belong to
  zeno-stack/zeno-deployment-patterns. Trigger on: "CircleCI config", "CircleCI pipeline",
  "branch strategy", "branch protection", "repo secrets management", "environment promotion",
  "Astronomer deploy", "Airflow deployment".
---

# GitHub & CircleCI CI/CD Standards

Use this skill when designing or reviewing GitHub and CircleCI delivery workflows, especially
where multi-environment promotion, secrets governance, or Astronomer/Airflow deployment is
in scope. This skill's assumptions are cloud-shaped (reachable targets, environment
promotion, approval gates); when the deploy target is an operator-owned host behind NAT,
pair it with `zeno-stack/zeno-self-hosted-deployment`, which owns the topology side
(pull-vs-push delivery, runner hardening, single-host shared infrastructure).

**Scope note:** CircleCI is the house CI — every pipeline mechanic here is CircleCI-specific (plus Astronomer/Airflow deployment). For **GitHub Actions** pipeline mechanics, and for platform-neutral strategy (rolling/blue-green/canary, rollback, production readiness), the owner is `zeno-stack/zeno-deployment-patterns` — per CLAUDE.md's CI/CD lane row.

## Core Principles

- Build once and promote the same artifact through environments
- Separate GitHub governance from CircleCI execution concerns
- Require manual approval for sensitive environment promotion
- Keep configuration and secrets environment-specific and out of source code
- Make every deployment traceable to a commit, PR, and build artifact

## Governance Model

- No environment should auto-promote into sensitive stages without explicit approval.
- DEV and STAGE may be gated manually depending on risk posture.
- Production should require:
  - a valid change reference if the organization uses one
  - explicit manual approval
  - evidence that required validations passed

Approvers are responsible for checking scope, approval status, and deployment readiness.

## Configuration and Secrets

- Use environment variables or templates for environment-specific values.
- Use GitHub environments and secrets for governance-scoped data.
- Use CircleCI contexts for reusable secret sets with least-privilege access.
- Do not hard-code credentials, URLs, or environment-only behavior in pipeline logic.

## Pipeline Structure

Prefer a clear progression such as:

`build -> test -> package -> deploy -> smoke-test`

Use `requires` to enforce ordering. For complex repos, use dynamic config or path-based
workflow selection only when it reduces noise without hiding risk.

## Environment Promotion

- Promote immutable artifacts rather than rebuilding per environment.
- Add manual `approval` jobs before staging or production deployments where required.
- Run smoke tests after deployment to catch broken releases early.
- Restrict deployment branches per environment.

## Astronomer and Airflow Patterns

When the repo deploys Airflow through Astronomer:

- validate DAG syntax before deployment
- distinguish DAG-only deploys from full-image deploys when safe to do so
- run tests for custom operators, hooks, or shared libraries before release
- keep Astro CLI installation and auth handling explicit in CI

## Branch Strategy

Use a branching model that matches team size and deployment frequency:

| Model | Best For | Branch Flow |
|---|---|---|
| **GitHub Flow** | High-frequency deploys, small teams | `feature → main → deploy` |
| **Git Flow** | Release-gated projects, larger teams | `feature → develop → release → main` |
| **Trunk-Based** | CI/CD with feature flags, very high frequency | `short-lived branches → main` |

Branch protection rules for `main` and `develop` should require:
- at least one approving review
- all CI checks to pass
- no direct pushes (force-push disabled)
- linear history or merge commits depending on team preference

## Pipeline Caching

Cache dependencies to speed up pipeline jobs without sacrificing correctness:

- Cache by a lock-file checksum, not a branch name: `{{ checksum "package-lock.json" }}`
- Use a fallback key so first-run cache misses still get a partial hit
- Separate dependency cache from build artifact cache
- Invalidate caches explicitly when dependency lock files change

```yaml
# CircleCI cache example
- restore_cache:
    keys:
      - deps-v1-{{ checksum "requirements.txt" }}
      - deps-v1-  # fallback partial key
- run: pip install -r requirements.txt
- save_cache:
    key: deps-v1-{{ checksum "requirements.txt" }}
    paths: [~/.cache/pip]
```

## Rollback and Recovery

Every deployment should have a defined rollback path before it is deployed:

- **Immutable artifacts**: re-deploy the previous tag or artifact version
- **Database migrations**: write backward-compatible migrations; never destructive changes in the same release
- **Feature flags**: prefer flags over code rollbacks for fast recovery
- **Rollback trigger**: document whether rollback is automatic (on smoke-test failure) or manual
- Maintain a deployment log with commit SHA, artifact version, approver, and timestamp

```yaml
# CircleCI rollback job pattern
rollback:
  steps:
    - run: ./deploy.sh ${PREVIOUS_IMAGE_TAG}
    - run: ./smoke-test.sh
  when: on_fail  # trigger on failure of downstream step
```

## Review Workflow

1. Identify environments, approval points, and artifact flow.
2. Check build/test/package/deploy ordering.
3. Verify secrets and environment configuration boundaries.
4. Confirm promotion, rollback, and smoke-test behavior.
5. Review auditability, notifications, and access restrictions.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Rebuilding the artifact per environment | Build once, promote the same immutable artifact |
| Auto-promotion into sensitive environments | Manual `approval` jobs gating staging/production |
| Credentials, URLs, or env behavior hard-coded in pipeline logic | Env vars, GitHub environments/secrets, CircleCI contexts (least privilege) |
| Caching by branch name | Cache keyed on lock-file checksum with a fallback partial key |
| Destructive DB migration in the same release | Backward-compatible migrations; destructive changes deferred |
| Deploying with no defined rollback path | Rollback path documented (and tested) before deployment |
| Direct pushes / force-push to protected branches | Branch protection: reviews required, CI checks pass, no direct pushes |
| Untraceable deployments | Deployment log with commit SHA, artifact version, approver, timestamp |
| Astronomer deploys without DAG validation | Validate DAG syntax and test custom operators before release |

## Pre-flight checklist — run before delivering any CI/CD pipeline config

- [ ] Branch protection and review controls exist where expected
- [ ] Secrets are scoped correctly to GitHub environments or CircleCI contexts
- [ ] The pipeline promotes a single built artifact through environments
- [ ] Manual gates exist for sensitive deployments
- [ ] Post-deploy validation or smoke tests are defined
- [ ] Pipeline logs and notifications support audit and troubleshooting
- [ ] Branch strategy is defined and enforced via protection rules
- [ ] Dependency caching uses lock-file checksums for correctness
- [ ] A rollback path is documented and tested for every environment
