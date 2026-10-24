---
name: zeno-self-hosted-deployment
description: >
  Deployment topology for operator-owned infrastructure — home-lab / LAN servers behind NAT,
  single-host Docker Compose, no orchestrator: pull-vs-push delivery, self-hosted runner
  hardening (fork-PR risk), never building on the production host, artifact promotion and
  rollback without an orchestrator, shared single-host infrastructure, and Compose operational
  traps. Use when the deploy target is a machine you own rather than a cloud environment.
  Trigger on: "deploy to my home server", "self-hosted deployment", "home lab", "LAN server",
  "behind NAT", "self-hosted runner", "Tailscale deploy", "Watchtower", "deploy docker compose
  to my server", "compose project name", or any CD question where the target has no inbound path
  from the internet.
---

# Self-Hosted Deployment Topology

Deployment where the target is operator-owned: a home-lab or LAN machine behind NAT,
single-host (or few-host), running Docker Compose with no orchestrator, often shared between
applications and latency-sensitive. Cloud CD advice silently assumes reachable targets,
environment promotion, and elastic capacity — this skill owns the constraints that appear
when those assumptions fail.

**Assumed topology (stated so the omissions are visible):** one or few Linux hosts you
administer; no inbound ports by default; Docker Compose as the runtime; a git repo as the
source of truth; possibly one host running everything, including latency-sensitive
workloads. For rollout-strategy taxonomy, health-check design, and env-var validation see
`zeno-deployment-patterns`; for pipeline shape, build-once/promote, and secrets governance
see `github-circleci-standards` (CircleCI) or `zeno-stack/zeno-deployment-patterns` (GitHub Actions); for image/Compose mechanics see `zeno-docker-patterns`.

## 1. Delivery mechanism — pull vs push to an unreachable target

Never solve "CI can't reach my server" by port-forwarding SSH to the internet. The two sound
topologies: the target pulls/polls **outbound**, or CI pushes through an overlay/tunnel that
needs no inbound ports. Both GitHub and GitLab self-hosted runners connect outbound-only over
HTTPS long-poll.

| Mechanism | Direction | Attack surface added to host | Fits when |
|---|---|---|---|
| Self-hosted CI runner on/near target | pull (outbound poll) | Runner executes repo-controlled code on the host — biggest surface (§3) | Private repo; full pipeline drives the host |
| CI over SSH through Tailscale/WireGuard | push | One forced-command deploy key + overlay membership | Runner stays cloud-hosted; host exposes only sshd on the overlay |
| Cron/systemd timer: `git pull && docker compose up -d --pull always` | pull (polling) | Read-only git credential + registry token — smallest surface | Few apps; minutes of deploy latency acceptable |
| Webhook listener on host (via tunnel) → compose up | pull (event) | Small authenticated HTTP endpoint | Seconds-latency without a runner |
| PaaS layer (Coolify / Dokploy / Komodo / Portainer) | pull (agent) | A privileged always-on control plane holding the Docker socket — root-equivalent if compromised | Many apps, want a UI; put its UI on the overlay only, never the public internet |
| Watchtower-style registry auto-pull | pull | Unattended untested versions in prod | **Don't** — Watchtower was archived 2025-12; use Diun (notify-only) or Renovate PRs |

Rules that hold across mechanisms:

- **Git is the source of truth.** Never edit compose files directly on the server. Automated
  image updates arrive as Renovate/Dependabot PRs (digest bumps), not silent pulls — an
  unattended `postgres:16`→`17` swap bricks the data directory.
- **Pick one deploy trigger explicitly** — "new commit in git" or "new image in registry" —
  and bridge the other side via PRs. Mixing both un-deliberately produces deploys nobody
  ordered.

## 2. Network access path

| Path | Inbound ports | Trust dependency | Use for |
|---|---|---|---|
| Tailscale | none (NAT traversal, works behind CGNAT) | Tailscale coordination plane | Default for admin/SSH/deploy access |
| Plain WireGuard, self-hosted | one UDP port | none | Same, when you can port-forward and want zero third parties |
| cloudflared tunnel | none | Cloudflare terminates TLS | Publishing *specific web apps* — not a general admin/deploy path |
| Runner-only outbound | none | GitHub/GitLab | Host stays unreachable, period |
| Raw port-forward of SSH/services | yes | none | **Avoid** — the classic homelab compromise vector |

Hybrid is normal: overlay VPN for private admin + deploy, cloudflared only for apps
deliberately published.

**SSH deploy-user hardening (push topologies):** the deploy key gets a forced command, not a
shell:

```text
# ~deploy/.ssh/authorized_keys
restrict,command="/opt/deploy/deploy.sh" ssh-ed25519 AAAA... ci-deploy
```

`restrict` kills forwarding and PTY in one word; `command=` runs the script regardless of
what the client asks for — a leaked key yields your deploy script, not a shell. Dedicated
`deploy` user, ed25519 keys, `PasswordAuthentication no`. The forced script is now your API
surface: whitelist expected `SSH_ORIGINAL_COMMAND` values (e.g. tag-name regex) before
using them. Prefer the script invoking exactly scoped `docker compose` commands over putting
`deploy` in the `docker` group (docker group = root-equivalent).

## 3. Self-hosted runner hardening

GitHub's own security reference: self-hosted runners should **almost never** be attached to
public repositories — any user can open a PR and compromise the environment.

- [ ] Never attach a self-hosted runner to a public repo — fork PR = arbitrary code execution
      on your host. Public repo? Deploy from a GitHub-hosted runner over a tunnel, or mirror
      to a private repo for the deploy workflow.
- [ ] Private repos still carry residual risk: restrict who can trigger the deploy workflow
      (environment protection, `main`-only branch filter).
- [ ] Never `checkout` PR code in a `pull_request_target` workflow — it runs with base-repo
      secrets and a privileged token.
- [ ] Run **ephemeral** (`--ephemeral` / JIT registration): one job per registration.
      Persistent runners accumulate credentials, workspace remnants, and attacker-planted
      backdoors the next job inherits.
- [ ] Scope with labels + runner groups; never share one runner across trust levels.
- [ ] Containerized runner is safer than bare **until you hand it the Docker socket** —
      socket-mount or privileged DinD is root-equivalent on the host. Rising isolation:
      bare unprivileged runner with no docker access (deploy via forced-command SSH to
      localhost) → socket-mounted container (accept only for single-trust private repos) →
      rootless DinD → dedicated VM.
- [ ] No secrets at rest on the runner box — anything in the runner's environment is readable
      by any workflow that can reach it.
- [ ] Egress-restrict the runner where practical (allowlist GitHub, registry, mirrors).
- [ ] The runner is not the production workload: separate OS user, and cgroup limits
      (systemd `CPUQuota=`/`MemoryMax=`) if it shares a latency-sensitive host — though §4's
      no-build rule removes the worst of it.

## 4. Artifact promotion — never build on the production host

Builds spike CPU/IO on the latency-sensitive workload, and the host then needs source,
toolchains, and package-mirror egress it shouldn't have. Build in CI, push to a registry,
host only pulls.

| Getting the image there | Layer dedup | Fits when |
|---|---|---|
| **GHCR** (default) | yes | Repo already on GitHub — the default answer |
| Self-hosted registry (`registry:2`, Harbor) | yes | Air-gapped or egress-constrained; otherwise avoid the extra service to run/back up/TLS |
| `docker save \| ssh host docker load` | no — full image every time | One-off/emergency transfers |
| unregistry (`docker pussh`) | yes (missing layers only) | Registry-less but repeated deploys |

- **Tag with an immutable identifier** (git SHA or semver) — never deploy `latest`; tags are
  mutable pointers even when they look like versions. **Pin by digest**
  (`image: ghcr.io/...@sha256:...`) for strict reproducibility, with Renovate bumping digests
  by PR so pins don't fossilize.
- **Rollback without an orchestrator = re-point the compose file at the previous tag/digest
  and `docker compose up -d`.** Preconditions: registry retention keeps N releases, and the
  host doesn't `docker image prune -a` right after deploy (the prior image is your instant
  rollback cache). Pin tags **in git** so `git revert` *is* the rollback mechanism — the
  strongest reason not to pass tags as CI variables.

## 5. Shared single-host infrastructure

**One Postgres vs many:**

| | One instance, schema-per-app | Instance-per-app |
|---|---|---|
| Isolation | Logical only (GRANT/REVOKE); shared crash domain and upgrade cadence | Full: independent versions, crash domains |
| Overhead | One shared_buffers pool — cheap on a small host | ~100–200 MB+ baseline each |
| Backup | One job; single point of catastrophic loss | Contained blast radius |
| Fits | Many small apps, RAM-constrained, disciplined grants | Conflicting version needs; loads that must not touch each other |

Schema-per-app is **default-deny or it is nothing**:

```sql
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE appdb FROM PUBLIC;
CREATE ROLE app_a LOGIN PASSWORD '...';
CREATE SCHEMA app_a AUTHORIZATION app_a;
ALTER ROLE app_a SET search_path = app_a;
-- app_a gets nothing on app_b's schema unless explicitly granted
```

Each app connects as its own role only; run grants as the schema owner, not the superuser.
Be honest about the limit: this is logical isolation — a Postgres CVE or superuser
compromise crosses it. Query/index depth: `zeno-postgres-patterns`.

**Reverse proxy as the join seam:** one shared Traefik/Caddy in its own compose project on a
pre-created external network; each app's *web-facing service only* joins that network and is
discovered by labels — no proxy restart per app. DB/cache stay on the app's own `default`
network. The external network is the seam, not a flat LAN for everything.

```yaml
# once: docker network create proxy
networks:
  proxy:
    external: true
services:
  web:
    networks: [proxy, default]
    labels:
      - traefik.enable=true
      - traefik.http.routers.web.rule=Host(`app.example.lan`)
```

**Resource limits:** every co-tenant service gets `deploy.resources.limits.{cpus,memory}` —
modern Compose v2 applies them (the "deploy is Swarm-only" advice is outdated; verify with
`docker stats` after first deploy) — so no neighbor can starve the latency-sensitive tenant.

**Backups — consolidation raises criticality from optional to required:**

- [ ] 3-2-1: three copies, two media, one offsite (B2/S3, or a friend's box over the overlay)
- [ ] restic (S3/B2-native) or borg (better compression, SSH targets) — encrypted + deduped
- [ ] Never file-copy a live database volume — dump first (`pg_dumpall` pre-backup hook),
      then back up the dump + named volumes + compose/git dir
- [ ] A backup is untested until restored: automate a restore into a throwaway container with
      a row-count check, reporting by mail/webhook
- [ ] Back up the deploy *inputs* too: compose files (git), encrypted `.env` files, the
      external-network/volume creation steps — bare-metal recovery should be a script, not
      archaeology

## 6. Compose operational traps

- **Pin the project name.** Compose derives it from the directory basename; a CI checkout
  path and an operator's `~/apps/foo` silently become two projects with **forked volumes**.
  Set top-level `name:` in the compose file (precedence: `-p` > `COMPOSE_PROJECT_NAME` >
  `name:` > directory), so every invocation that doesn't explicitly override converges.
- **`down -v` deletes the project's volumes — your data.** Never in a deploy script; routine
  redeploys are `up -d`, not `down` + `up`. Use `--remove-orphans` on `up` after
  renaming/removing services.
- **Env precedence is two separate systems:** `.env` feeds *compose-file interpolation*;
  `env_file:`/`environment:` feed *the container* (inline beats file; shell env beats `.env`
  for interpolation; `${VAR}` does not expand inside env files). Commit `.env.example`; the
  real `.env` lives next to the compose file on the host; never rely on the runner's shell
  env leaking into interpolation.
- **Gate deploys on health:** real `healthcheck:` per service + `docker compose up -d
  --wait` — CI fails when the container never goes healthy instead of reporting success on a
  crash loop. `docker compose pull` (or `pull_policy: always`) first.
- **Low-downtime without an orchestrator:** default `up -d` recreates in place — seconds of
  downtime, usually fine on a LAN. If not: `docker-rollout` (scale ×2, wait healthy, drop
  old — needs a proxy in front, no fixed `container_name`/host-port) or an nginx-upstream
  flip. Don't promise blue-green semantics beyond this without an orchestrator
  (`zeno-deployment-patterns` owns the strategy taxonomy).

## 7. Host patching cadence

- `unattended-upgrades` on for security patches, with `docker-ce`/`containerd.io`
  blacklisted so the engine updates only in a chosen window.
- `"live-restore": true` in `/etc/docker/daemon.json` — containers survive daemon restarts
  (not host reboots; container-DNS can blip while the daemon is down).
- Reboots are deliberate maintenance windows on latency-sensitive hosts:
  `Automatic-Reboot "false"`, watch `/var/run/reboot-required`, every service
  `restart: unless-stopped` so the stack self-heals. Patch after a verified backup, never
  before one.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Port-forwarding SSH/services to the internet so CI can reach the host | Outbound-only runner, or push through Tailscale/WireGuard; cloudflared only for deliberately published web apps |
| Self-hosted runner attached to a public repo | Almost never — fork PRs execute code on your host; use a hosted runner over a tunnel, or a private deploy mirror |
| Persistent runner with the Docker socket, shared across trust levels | Ephemeral/JIT runners, label-scoped; socket-mount accepted only for single-trust private repos |
| Building images on the production host | Build in CI, promote prebuilt images through a registry; the host only pulls |
| Deploying `latest`, or auto-pulling registry changes (Watchtower-style) | Git-pinned SHA/digest tags; Renovate PRs for bumps; Diun for notify-only |
| Editing compose files directly on the server | Git is the source of truth; `git revert` is the rollback mechanism |
| Unpinned compose project name across CI and operator invocations | Top-level `name:` — otherwise volumes silently fork per directory |
| `down -v` in a deploy script | `up -d` (+ `--wait`, `--remove-orphans`); `-v` only in deliberate teardown |
| Schema-per-app Postgres without REVOKE-first grants | Default-deny (`REVOKE ALL ... FROM PUBLIC`), one role per app, owner-run grants |
| File-copying a live DB volume as "backup", never testing restores | Dump-then-backup with restic/borg, 3-2-1, automated restore checks |
| Deploy key with full shell access | `restrict,command=` forced-command key; the script whitelists its inputs |

## Pre-flight checklist — run before delivering any self-hosted deployment change

- [ ] The delivery mechanism was chosen from the decision table, and the deploy trigger (git commit vs registry image) is explicit
- [ ] No inbound ports were opened for CI; admin/deploy access rides an overlay VPN, cloudflared only publishes chosen web apps
- [ ] Any self-hosted runner: private repo only, ephemeral, label-scoped, socket exposure consciously decided, no secrets at rest
- [ ] Any SSH push path uses a `restrict,command=` forced-command deploy key with input whitelisting
- [ ] Images are built in CI and pinned by SHA/digest in git; the previous release's image is retained for instant rollback
- [ ] No build toolchain, source checkout, or package-mirror egress required on the production host
- [ ] Shared Postgres (if any) is default-deny with one role per app; the isolation limit is documented
- [ ] Co-tenant services carry memory/CPU limits, verified with `docker stats` after first deploy
- [ ] Compose file pins `name:`; deploy script uses `up -d --wait` with healthchecks, never `down -v`
- [ ] Backups are 3-2-1, dump-before-backup for databases, with an automated tested restore — and deploy inputs (compose, encrypted `.env`, network/volume bootstrap) are recoverable by script
- [ ] Host patching: unattended security upgrades with the Docker engine excluded; reboots scheduled, after a verified backup
