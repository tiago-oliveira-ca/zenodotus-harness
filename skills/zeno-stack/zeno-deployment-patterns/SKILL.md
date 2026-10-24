---
name: zeno-deployment-patterns
description: >
  Deployment strategy (rolling, blue-green, canary), CI/CD pipeline structure, health
  check endpoints, environment configuration, rollback strategy, and a production
  readiness checklist for shipping web applications. Use when setting up a CI/CD
  pipeline, choosing a rollout strategy, adding a health check, or preparing for a
  production release. For the container image being shipped see zeno-docker-patterns;
  for running it on Kubernetes see zeno-kubernetes-patterns; for operator-owned/NAT'd
  targets (home-lab, single-host Compose) see zeno-self-hosted-deployment. Trigger on: "set up CI/CD",
  "which deployment strategy", "blue-green deployment", "canary release", "add a health
  check endpoint", "rollback strategy", "production readiness checklist", "twelve-factor
  config", "environment variable validation".
---

# Deployment Patterns

How to ship a change to production: rollout strategy, the CI/CD pipeline around it,
health checks, config, and rollback. For the image itself, see `zeno-docker-patterns`;
for running it under an orchestrator, see `zeno-kubernetes-patterns`. This skill assumes a
reachable, cloud-shaped target — when the deploy target is operator-owned (home-lab / LAN
host behind NAT, single-host Compose), the topology constraints live in
`zeno-self-hosted-deployment`; apply that skill alongside this one's strategy taxonomy.

**Production-readiness split** (CLAUDE.md lane row): this skill owns the *mechanics* — health checks, rollback strategy, deploy topology, environment config. Judging whether a system is launch-ready is `zeno-stack/zeno-production-audit`; writing the runbook or go-live checklist is `documentation/operations-standards`.

## When to reach for this skill

- Setting up a CI/CD pipeline
- Choosing a rollout strategy for a release
- Implementing health check or readiness endpoints
- Preparing for a production release
- Configuring environment-specific settings

**Split with `github-circleci-standards`:** that skill owns the CircleCI house pipeline standard (and Astronomer/Airflow); this leaf owns GitHub Actions mechanics and platform-neutral strategy/rollback/readiness — per CLAUDE.md's CI/CD lane row.

## Deployment strategies

**Rolling (default)** — instances update gradually; old and new versions run side by
side during the rollout.

```
Instance 1: v1 → v2          Instance 1: v2
Instance 2: v1        ...    Instance 2: v1 → v2    ...    all instances on v2
Instance 3: v1                Instance 3: v1
```

Zero downtime, gradual — but requires the two versions to be backward-compatible with
each other for the duration of the rollout. Use for standard, compatible changes.

**Blue-green** — two identical environments; traffic switches atomically from one to
the other.

```
Blue (v1) ← traffic       →       Blue (v1) idle (standby)
Green (v2) idle                    Green (v2) ← traffic
```

Instant rollback (flip back to blue), clean cutover — at the cost of running 2x
infrastructure during the deployment. Use for critical services with zero tolerance for
a bad rollout.

**Canary** — a small percentage of traffic goes to the new version first, then ramps up
as metrics stay healthy.

```
v1: 95%, v2: 5%  →  v1: 50%, v2: 50%  →  v2: 100%
```

Catches problems on real traffic before a full rollout, but needs traffic-splitting
infrastructure and active monitoring to be worth the complexity. Use for high-traffic
services or risky changes.

## CI/CD pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: coverage, path: coverage/ }

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}
```

**Stage progression:**

```
PR opened:       lint → typecheck → unit tests → integration tests → preview deploy
Merged to main:  lint → typecheck → unit/integration tests → build image →
                 deploy staging → smoke tests → deploy production
```

## Health checks

```typescript
// Liveness — cheap, no dependency checks
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

// Readiness / diagnostics — checks the dependencies that determine if this
// instance can actually serve traffic
app.get("/health/detailed", async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    redis: await checkRedis(),
    externalApi: await checkExternalApi(),
  };
  const allHealthy = Object.values(checks).every(c => c.status === "ok");
  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? "ok" : "degraded",
    version: process.env.APP_VERSION || "unknown",
    uptime: process.uptime(),
    checks,
  });
});

async function checkDatabase(): Promise<HealthCheck> {
  try {
    await db.query("SELECT 1");
    return { status: "ok" };
  } catch {
    return { status: "error", message: "Database unreachable" };
  }
}
```

Keep the liveness endpoint (`/health`) cheap and dependency-free — it decides whether
the process gets restarted, not whether it's ready for traffic. Put dependency checks
behind a separate readiness/detailed endpoint instead. See `zeno-kubernetes-patterns`
for how these map onto `livenessProbe` / `readinessProbe` / `startupProbe`.

## Environment configuration

Twelve-factor: all config through environment variables, never hardcoded:

```bash
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
API_KEY=${API_KEY}     # injected by the secrets manager, never committed
NODE_ENV=production
```

Validate configuration at startup so a misconfigured deploy fails immediately instead
of failing on the first request that needs the missing value:

```typescript
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "staging", "production"]),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
});

export const env = envSchema.parse(process.env);   // throws at boot, not mid-request
```

## Rollback

```bash
kubectl rollout undo deployment/app                          # K8s: previous image
vercel rollback                                               # Vercel: previous deployment
npx prisma migrate resolve --rolled-back <migration-name>     # DB: mark reversed
```

Rollback checklist:

- [ ] Previous image/artifact is available and tagged
- [ ] Database migrations for this release are backward-compatible (no destructive changes)
- [ ] Feature flags can disable new behavior without a redeploy
- [ ] Alerts are configured for error-rate spikes so a bad rollout is caught fast
- [ ] Rollback path has actually been tested in staging, not just documented

## Production readiness checklist

**Application**
- [ ] All tests pass (unit, integration, E2E)
- [ ] No hardcoded secrets in code or config files
- [ ] Error handling covers the realistic edge cases, not just the happy path
- [ ] Logging is structured (JSON) and contains no PII
- [ ] Health check endpoint returns a meaningful status, not just 200 always

**Infrastructure**
- [ ] Image builds reproducibly (pinned versions, no floating tags)
- [ ] Environment variables are documented and validated at startup
- [ ] Resource limits are set (CPU, memory)
- [ ] Horizontal scaling is configured (min/max instances)
- [ ] TLS is enabled on every public endpoint

**Monitoring**
- [ ] Application metrics are exported (request rate, latency, error rate)
- [ ] Alerts fire on error rate exceeding a defined threshold
- [ ] Logs are aggregated and searchable
- [ ] Uptime monitoring watches the health endpoint from outside the cluster

**Security**
- [ ] Dependencies are scanned for known CVEs
- [ ] CORS is scoped to allowed origins only
- [ ] Public endpoints are rate-limited — see `zeno-redis-patterns#rate-limiting` for
      the correct (shared-store) implementation; an in-process limiter fails across
      replicas and resets on every deploy
- [ ] AuthN/AuthZ is verified on every route that needs it
- [ ] Security headers are set (CSP, HSTS, X-Frame-Options)

**Operations**
- [ ] Rollback plan is documented and has actually been exercised
- [ ] Database migrations were tested against production-sized data
- [ ] A runbook exists for the most likely failure scenarios
- [ ] On-call rotation and escalation path are defined

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Deploying without a rollback plan | Tag the previous artifact, document and test the rollback path before shipping |
| Health check that always returns 200 | Check real dependencies (DB, cache) and return 503 when they're down |
| Config hardcoded instead of environment-driven | Twelve-factor: all config via env vars, validated at startup |
| In-process rate limiter (memory store) on a public endpoint | Redis-backed limiter — see `zeno-redis-patterns#rate-limiting` |
| Schema migration bundled with the same deploy that needs it to already exist | Expand-contract the migration ahead of the code that depends on it |
| Canary/blue-green chosen without the infrastructure to support it | Rolling deployment unless traffic-splitting or dual-environment infra already exists |
| Skipping staging and deploying straight to production | Pipeline stages: test → build → staging → smoke test → production |

## Pre-flight checklist — run before delivering any production deployment

- [ ] Rollout strategy matches the risk of the change (rolling/blue-green/canary)
- [ ] CI pipeline runs lint, typecheck, and tests before any build or deploy step
- [ ] Health check endpoint reflects real dependency status, not just liveness
- [ ] Environment variables are validated at startup, not discovered missing mid-request
- [ ] Public endpoints are rate-limited via a shared store (`zeno-redis-patterns#rate-limiting`), not in-process memory
- [ ] Rollback path is documented and has been tested, not just assumed to work
- [ ] Production readiness checklist above is satisfied before go-live
