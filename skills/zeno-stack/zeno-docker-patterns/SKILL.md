---
name: zeno-docker-patterns
description: >
  Docker and Docker Compose patterns for local development environments, multi-stage
  Dockerfiles, container networking, volume strategy, and container hardening. Use when
  setting up Compose for local dev, writing or reviewing a Dockerfile, debugging
  container networking or volume issues, or migrating a project to a containerized
  workflow. For production rollout of a container (CI/CD, health checks, rollback) see
  zeno-deployment-patterns; for running that container on Kubernetes see
  zeno-kubernetes-patterns. Trigger on: "set up docker compose", "write a Dockerfile",
  "multi-stage build", "container networking issue", "docker volume", "harden this
  container", "dockerignore", "why can't containers reach each other".
---

# Docker Patterns

Docker and Docker Compose for containerized local development — orchestration,
networking, volumes, and image hardening. For the CI/CD pipeline that builds and ships
these images, see `zeno-deployment-patterns`; for running them under an orchestrator,
see `zeno-kubernetes-patterns`.

## When to reach for this skill

- Setting up Docker Compose for local development
- Designing a multi-container local architecture
- Troubleshooting container networking or volume issues
- Reviewing a Dockerfile for security or image size
- Moving a project from local-only dev to a containerized workflow

## Compose for local development

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: dev                     # dev stage of a multi-stage Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - .:/app                        # bind mount for hot reload
      - /app/node_modules             # anonymous volume — preserves container deps
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app_dev
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

**Override files** split dev-only convenience from an explicit production compose:

```yaml
# docker-compose.override.yml — auto-loaded, dev-only settings
services:
  app:
    environment:
      - DEBUG=app:*
    ports:
      - "9229:9229"   # Node.js debugger

# docker-compose.prod.yml — loaded explicitly
services:
  app:
    build:
      target: production
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
```

```bash
docker compose up                                            # dev, auto-loads override
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d   # prod
```

## Multi-stage Dockerfile

Separate dependency install, dev, build, and production stages so the shipped image
carries only what production needs:

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

## Networking

Services on the same Compose network resolve each other by service name — no manual
DNS or hardcoded IPs:

```
postgres://postgres:postgres@db:5432/app_dev   # "db" is the postgres service name
redis://redis:6379/0                            # "redis" is the redis service name
```

Segment networks so only the services that need to talk to each other can:

```yaml
services:
  frontend:
    networks: [frontend-net]
  api:
    networks: [frontend-net, backend-net]
  db:
    networks: [backend-net]      # unreachable from frontend

networks:
  frontend-net:
  backend-net:
```

Bind exposed ports to localhost in dev, and omit `ports:` entirely for anything that
only needs to be reachable inside the Docker network in production:

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"   # host-only, not exposed to the network
```

## Volumes

```yaml
volumes:
  pgdata:              # named volume — persists across restarts, Docker-managed

services:
  app:
    volumes:
      - .:/app                   # bind mount — source code, for hot reload
      - /app/node_modules        # anonymous volume — protects deps from the bind mount
      - /app/.next                # anonymous volume — protects the build cache
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
```

## Container hardening

```dockerfile
# Pin a specific tag — never :latest
FROM node:22.12-alpine3.20

# Run as a non-root user
RUN addgroup -g 1001 -S app && adduser -S app -u 1001
USER app
```

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE   # only if binding to a port below 1024
```

**Secrets** — environment variables sourced from a gitignored `.env`, or Docker
secrets in Swarm mode; never hardcoded into an image layer:

```yaml
services:
  app:
    env_file:
      - .env              # never committed
    environment:
      - API_KEY            # inherited from host environment

secrets:
  db_password:
    file: ./secrets/db_password.txt
services:
  db:
    secrets: [db_password]

# NEVER: ENV API_KEY=sk-proj-xxxxx baked into the image
```

**`.dockerignore`** keeps build context small and secrets out of the image:

```
node_modules
.git
.env
.env.*
dist
coverage
*.log
docker-compose*.yml
Dockerfile*
tests/
```

## Debugging

```bash
docker compose logs -f app                    # follow logs
docker compose exec app sh                     # shell into a running container
docker compose exec db psql -U postgres         # connect to postgres directly
docker compose ps                               # running services
docker stats                                    # resource usage
docker compose up --build                       # rebuild images
docker compose down -v                          # stop + remove containers AND volumes (destructive)

docker compose exec app nslookup db             # DNS resolution inside the network
docker compose exec app wget -qO- http://api:3000/health   # connectivity check
docker network inspect <project>_default        # inspect the Compose network
```

**Build-time DNS failures** ("Temporary failure in name resolution" from pip/npm/apt during
`docker compose build`): bisect bridge vs host networking with the same image before touching
daemon config —

```bash
docker run --rm <image> getent hosts pypi.org                  # default bridge network
docker run --rm --network host <image> getent hosts pypi.org   # host network
```

Bridge fails while host succeeds means the default bridge build network can't reach DNS (a
daemon/iptables issue, common on hardened deploy hosts) — not a registry or proxy problem.
Escape hatch: `build: { network: host }` on the Compose service. It is build-time only, and it
masks the underlying bridge DNS breakage rather than fixing it — note that in the compose file.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Docker Compose as a production orchestrator | Use Kubernetes, ECS, or Swarm for production multi-container workloads (see `zeno-kubernetes-patterns`) |
| Container data with no volume | Containers are ephemeral — mount a named volume for anything that must survive a restart |
| Running the container process as root | Create and switch to a non-root user in the Dockerfile |
| `:latest` image tag | Pin a specific version tag for reproducible builds |
| One giant container running every service | One process per container; split concerns |
| Secrets committed in `docker-compose.yml` | `.env` (gitignored) or Docker/Compose secrets |
| Single `COPY . .` before installing dependencies | Copy dependency manifests first so Docker's layer cache survives unrelated code changes |

## Pre-flight checklist — run before delivering any Docker or Compose change

- [ ] Dockerfile uses a pinned tag, never `:latest`
- [ ] Production stage runs as a non-root user
- [ ] Dependency files are copied and installed before the rest of the source (layer caching)
- [ ] `.dockerignore` excludes `node_modules`, `.git`, `.env`, and build artifacts
- [ ] Any data that must survive a restart is on a named volume, not container-local disk
- [ ] Secrets come from `.env` or a secrets manager, never a hardcoded `ENV` in the image
- [ ] `HEALTHCHECK` is defined for services other tooling depends on being ready
- [ ] Production compose/Dockerfile stage is separate from the dev stage, not shared by accident
