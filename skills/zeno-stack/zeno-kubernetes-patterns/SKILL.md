---
name: zeno-kubernetes-patterns
description: >
  Production-grade Kubernetes workload patterns — Deployments, probes, Services and
  Ingress, ConfigMaps/Secrets, resource requests/limits, RBAC, HPA/PDB, Jobs/CronJobs,
  and kubectl debugging for CrashLoopBackOff, OOMKilled, and pending pods. Use when
  writing or reviewing K8s manifests, configuring autoscaling or RBAC, or diagnosing a
  broken workload. For the container images these manifests deploy see
  zeno-docker-patterns; for the pipeline that builds and promotes them see
  zeno-deployment-patterns. Trigger on: "write a Kubernetes Deployment", "configure
  liveness and readiness probes", "set up RBAC", "HPA", "PodDisruptionBudget",
  "CrashLoopBackOff", "OOMKilled", "pending pod", "Kubernetes Secret", "kubectl
  rollout".
---

# Kubernetes Patterns

Copy-pasteable, production-grade YAML and `kubectl` commands for deploying, managing,
and debugging workloads reliably. For the image being deployed, see
`zeno-docker-patterns`; for the pipeline that builds and ships it here, see
`zeno-deployment-patterns`.

## When to reach for this skill

- Writing manifests (Deployments, Services, Ingress, Jobs)
- Configuring resource requests/limits or liveness/readiness/startup probes
- Setting up RBAC, namespaces, or ServiceAccounts
- Managing ConfigMaps and Secrets
- Debugging `CrashLoopBackOff`, `OOMKilled`, a pending pod, or an image-pull failure
- Configuring HPA or a PodDisruptionBudget

## Deployment — production template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: my-namespace
  labels:
    app: my-app
    version: "1.0.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0    # never drop below the desired replica count
  template:
    metadata:
      labels:
        app: my-app
        version: "1.0.0"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      terminationGracePeriodSeconds: 30
      containers:
        - name: my-app
          image: ghcr.io/org/my-app:1.0.0   # never :latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: [ALL]
          startupProbe:
            httpGet: { path: /health, port: 8080 }
            failureThreshold: 30
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /health, port: 8080 }
            periodSeconds: 30
            failureThreshold: 3
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 2
          envFrom:
            - configMapRef: { name: my-app-config }
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef: { name: my-app-secrets, key: db-password }
          volumeMounts:
            - name: tmp
              mountPath: /tmp        # writable dir needed when readOnlyRootFilesystem: true
      volumes:
        - name: tmp
          emptyDir: {}
```

## Probes

| Probe | Failure action | Use for |
|---|---|---|
| `startupProbe` | Kills the container if it's slow to start | Slow-starting apps (JVM, Python) |
| `livenessProbe` | Restarts the container | Deadlock / hung-process detection |
| `readinessProbe` | Removes the pod from Service endpoints | Temporary unavailability (DB reconnect, warmup) |

```yaml
# startupProbe covers slow startup; liveness/readiness only kick in once it succeeds
startupProbe:
  httpGet: { path: /health, port: 8080 }
  failureThreshold: 30   # 30 * 5s = 150s max startup time
  periodSeconds: 5
livenessProbe:
  httpGet: { path: /health, port: 8080 }
  periodSeconds: 30
  failureThreshold: 3    # 3 * 30s = 90s before a restart
readinessProbe:
  httpGet: { path: /ready, port: 8080 }   # separate endpoint: checks DB, cache, etc.
  periodSeconds: 10
  failureThreshold: 2
```

```yaml
# WRONG: an arbitrary initialDelaySeconds instead of a startupProbe is a race condition
livenessProbe:
  httpGet: { path: /health, port: 8080 }
  initialDelaySeconds: 60
```

## Services and Ingress

```yaml
# ClusterIP (default) — internal-only
apiVersion: v1
kind: Service
metadata: { name: my-app, namespace: my-namespace }
spec:
  selector: { app: my-app }
  ports: [{ port: 80, targetPort: 8080 }]
  type: ClusterIP
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  namespace: my-namespace
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [myapp.example.com]
      secretName: my-app-tls
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service: { name: my-app, port: { number: 80 } }
```

## ConfigMaps and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: my-app-config, namespace: my-namespace }
data:
  LOG_LEVEL: "info"
  app.yaml: |
    server:
      port: 8080
```

```bash
kubectl create secret generic my-app-secrets \
  --from-literal=db-password='s3cr3t' \
  --namespace=my-namespace \
  --dry-run=client -o yaml | kubectl apply -f -
```

Raw Kubernetes Secrets are only base64-encoded, not encrypted at rest unless the
cluster has encryption configured — use Sealed Secrets or External Secrets Operator for
anything production-sensitive.

## Resource requests and limits

```yaml
resources:
  requests:       # scheduler uses this to place the pod
    cpu: "100m"
    memory: "128Mi"
  limits:         # container is throttled/killed above this
    cpu: "500m"
    memory: "256Mi"
```

| Workload type | CPU request | Memory request | Notes |
|---|---|---|---|
| Web API | 100–250m | 128–256Mi | Set limits 2–4x requests |
| Worker/consumer | 250–500m | 256–512Mi | Memory limit = request, for predictable eviction |
| JVM app | 500m–1 | 512Mi–2Gi | Leave headroom above `-Xmx` for JVM overhead |
| Sidecar | 10–50m | 32–64Mi | Keep minimal |

```yaml
# WRONG: no resources block — unpredictable scheduling, uncontrolled OOM risk
containers:
  - { name: app, image: myapp:latest }

# WRONG: limits with no requests — requests silently default to the limits values,
# which over-reserves cluster capacity
resources:
  limits: { cpu: "2", memory: "1Gi" }
```

## RBAC

**Most apps don't call the Kubernetes API** — disable token automounting so there's
nothing to leak or misuse:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: my-app-sa, namespace: my-namespace }
automountServiceAccountToken: false
```

**Apps that do call the API** (operators, controllers, config watchers) get a token and
only the permissions they actually need:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: my-app-role, namespace: my-namespace }
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["my-app-secrets"]   # scoped to one named secret
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: my-app-rolebinding, namespace: my-namespace }
subjects:
  - kind: ServiceAccount
    name: my-app-sa
    namespace: my-namespace
roleRef: { kind: Role, apiGroup: rbac.authorization.k8s.io, name: my-app-role }
```

Use a namespaced `Role`, not a `ClusterRole`, unless the app genuinely needs
cluster-wide access — and never bind an application ServiceAccount to `cluster-admin`.

## HPA and PodDisruptionBudget

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: my-app-hpa, namespace: my-namespace }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: my-app }
  minReplicas: 2      # always at least 2 for HA
  maxReplicas: 10
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
```

HPA calculates utilization as `current / request`, so it requires `resources.requests`
to be set on every container it targets.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: my-app-pdb, namespace: my-namespace }
spec:
  minAvailable: 2   # or maxUnavailable — minAvailable: 0 defeats the purpose entirely
  selector: { matchLabels: { app: my-app } }
```

## Jobs and CronJobs

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: db-migrate, namespace: my-namespace }
spec:
  backoffLimit: 3
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: OnFailure    # never Always for a Job — causes an infinite loop
      containers:
        - name: migrate
          image: ghcr.io/org/my-app:1.0.0
          command: ["python", "manage.py", "migrate"]
          resources: { requests: { cpu: "100m", memory: "256Mi" } }
```

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: cleanup-job, namespace: my-namespace }
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid   # don't start a new run while the previous is still going
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: cleanup
              image: ghcr.io/org/cleanup:1.0.0
              resources: { requests: { cpu: "50m", memory: "64Mi" } }
```

## kubectl debugging cheatsheet

```bash
kubectl get pods -n my-namespace -o wide
kubectl describe pod <pod-name> -n my-namespace     # events and state details
kubectl logs <pod-name> -n my-namespace --previous  # logs from a crashed container
kubectl exec -it <pod-name> -n my-namespace -- sh
kubectl top pods -n my-namespace

kubectl rollout status deployment/my-app -n my-namespace
kubectl rollout undo deployment/my-app -n my-namespace              # rollback
kubectl rollout undo deployment/my-app --to-revision=2 -n my-namespace

kubectl get events -n my-namespace --sort-by='.lastTimestamp'
kubectl apply -f deployment.yaml --dry-run=server   # validate against the live cluster
```

**Diagnosing:**

```bash
# CrashLoopBackOff — check the crash logs and exit code / OOMKilled
kubectl logs <pod-name> --previous -n my-namespace
kubectl describe pod <pod-name> -n my-namespace

# ImagePullBackOff — check Events: wrong tag, missing imagePullSecret, private registry
kubectl describe pod <pod-name> -n my-namespace

# Pending pod — check Events: insufficient resources, node selector, taint mismatch
kubectl describe pod <pod-name> -n my-namespace

# OOMKilled — check Last State, then raise memory limits or find the leak
kubectl describe pod <pod-name> -n my-namespace | grep -A5 "Last State"
```

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `:latest` image tag | Pin an immutable tag (semver or `@sha256:...`) |
| No `securityContext` (defaults to root) | `runAsNonRoot: true` with an explicit `runAsUser` |
| No `resources` block | Always set both requests and limits |
| Plaintext secret in a ConfigMap | Use a `Secret`, and Sealed Secrets/ESO for real encryption |
| `ClusterRole: cluster-admin` bound to an app ServiceAccount | Namespaced `Role` scoped to only the verbs/resources needed |
| `PodDisruptionBudget.minAvailable: 0` | A value that actually protects availability during drains |
| `restartPolicy: Always` on a Job | `OnFailure` or `Never` |
| `initialDelaySeconds` used to cover a slow startup | A `startupProbe` sized to the real startup time |

## Pre-flight checklist — run before delivering any Kubernetes manifest

- [ ] Image tag is pinned, never `:latest`
- [ ] `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]` are all set
- [ ] Resource requests AND limits are set on every container
- [ ] All three probe types are configured where startup time is non-trivial
- [ ] ServiceAccount is dedicated to this app, not `default`, and `automountServiceAccountToken` is `false` unless the app calls the K8s API
- [ ] RBAC (if needed) uses a namespaced `Role`, least-privilege, never `cluster-admin`
- [ ] `minReplicas: 2+` and a `PodDisruptionBudget` exist for any production-critical workload
- [ ] Secrets are never stored as plaintext in a ConfigMap
