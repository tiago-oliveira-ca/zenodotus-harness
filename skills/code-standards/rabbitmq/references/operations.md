# RabbitMQ — Operations

Extracted from `../SKILL.md`: Security (§8), High Availability & Clustering (§9),
Observability & Monitoring (§11), and the deep tuning sub-block of Configuration &
Tuning (§12). Section numbers match the stubs in `SKILL.md`, so §-references
resolve here.

---

## 8. Security

### Virtual Hosts (vhosts)

```bash
# ✅ Correct: separate vhost per environment AND per application/team
rabbitmqctl add_vhost /production/orders
rabbitmqctl add_vhost /staging/orders
rabbitmqctl add_vhost /production/payments

# ❌ Wrong: sharing the default vhost for all applications in production
```

**vhost Rules:**

- One vhost per (environment × application) at minimum.
- Dedicated users per vhost; never share users across vhosts.
- Use descriptive names — `/<env>/<service>` convention.

### Authentication & Permissions (RBAC)

```bash
# ✅ Correct: create least-privilege user per service
rabbitmqctl add_user orders_service 'strong-random-password'
rabbitmqctl set_permissions -p /production/orders orders_service \
    'orders\.(events|commands)' \  # configure: create these exchanges/queues only
    'orders\.events'              \ # write: publish to orders.events only
    'inventory\..*|audit\..*'      # read: consume from these queues only

# ❌ Wrong: application user with .* (all access) in production
rabbitmqctl set_permissions -p / app_user '.*' '.*' '.*'

# ❌ Wrong: using default guest user in production
```

**Permission format:** `configure`, `write`, `read` — all accept regular expressions.

### Delete / Disable the Default `guest` User

```bash
# ✅ Required on every production deployment
rabbitmqctl delete_user guest

# Or at minimum restrict to localhost-only:
# rabbitmqctl set_permissions -p / guest '' '' ''
```

### TLS / mTLS

```ini
# rabbitmq.conf — ✅ Production TLS configuration

# Disable plaintext AMQP (only TLS allowed in production)
listeners.tcp = none
listeners.ssl.default = 5671

ssl_options.cacertfile = /etc/ssl/certs/ca.crt
ssl_options.certfile   = /etc/ssl/certs/server.crt
ssl_options.keyfile    = /etc/ssl/private/server.key
ssl_options.verify     = verify_peer         # verify client cert (mTLS)
ssl_options.fail_if_no_peer_cert = true      # reject clients without cert

# TLS versions — disable old protocols
ssl_options.versions.1 = tlsv1.3
ssl_options.versions.2 = tlsv1.2

# Management UI — HTTPS only
management.ssl.port       = 15671
management.ssl.certfile   = /etc/ssl/certs/server.crt
management.ssl.keyfile    = /etc/ssl/private/server.key

# Inter-node TLS (clustering)
cluster_ssl.enabled = true
```

**TLS Rules:**

- **Disable plaintext AMQP (`5672`)** in production; all traffic through `5671` (TLS).
- Use **mTLS** (`verify_peer`) for automated service-to-service connections.
- Use **TLS 1.2 and 1.3 only**; disable TLS 1.0 and 1.1.
- Automate certificate rotation (Let's Encrypt, Vault PKI).
- Store private keys with `chmod 400` and owned only by the RabbitMQ process user.

### Secrets Management

*(pika implementation: `../frameworks/python-pika.md` §8)*

```
# ✅ Correct: read credentials from environment / secrets manager
credentials = (
    username = env("RABBITMQ_USER"),
    password = env("RABBITMQ_PASSWORD"),   # injected by Vault / K8s secret
)

# ❌ Wrong: hardcoded credentials
credentials = (username="admin", password="admin")
```

---

## 9. High Availability & Clustering

### Cluster Topology

```bash
# ✅ Minimum: 3 nodes for quorum queues (Raft requires odd number for majority)
rabbitmqctl join_cluster rabbit@node1
rabbitmqctl join_cluster rabbit@node2
# Result: 3-node cluster — survives 1 node failure
```

```ini
# rabbitmq.conf — cluster name and node settings
cluster_name = prod-orders-cluster
cluster_partition_handling = pause_minority   # safe default for split-brain
```

### Quorum Queues for HA

```
# ✅ Always use quorum queues for HA data safety
declare_queue(
    name="payments.charge",
    durable=true,
    arguments={
        x-queue-type: quorum,
        x-quorum-initial-group-size: 3,    # replicate to all 3 nodes
    }
)

# ❌ Wrong: classic mirrored queues — deprecated, removed in RabbitMQ 4.x
arguments={x-ha-policy: all}
```

### Load Balancing

- Put a **load balancer** (HAProxy, AWS ALB, nginx) in front of the cluster for AMQP and management connections.
- **Distribute connections** across nodes — one node receiving all connections negates clustering benefits.
- **Separate connections per application component**: use different LB backends for publishers vs. consumers if traffic warrants it.

---

## 11. Observability & Monitoring

### Enable Core Plugins

```bash
# ✅ Enable on every deployment
rabbitmq-plugins enable rabbitmq_prometheus    # port 15692 — Prometheus scrape endpoint
rabbitmq-plugins enable rabbitmq_management   # port 15672/15671 — HTTP API + UI
rabbitmq-plugins enable rabbitmq_shovel       # message movement between queues/clusters
rabbitmq-plugins enable rabbitmq_federation   # connect distributed clusters
```

### Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq-node1:15692', 'rabbitmq-node2:15692', 'rabbitmq-node3:15692']
    metrics_path: /metrics
    scrape_interval: 15s
```

### Key Metrics to Alert On

| Metric | Alert Threshold | Meaning |
|---|---|---|
| `rabbitmq_queue_messages` | > configured max-length | Queue backing up; consumer lag |
| `rabbitmq_queue_messages_unacknowledged` | > `prefetch_count × consumers × 2` | Consumer stalled or crashed |
| `rabbitmq_queue_consumers` | = 0 for active queue | Consumer process down |
| `rabbitmq_queue_messages` on DLQ | > 0 | Processing failures occurring |
| `rabbitmq_node_mem_used` | > 70% of `vm_memory_high_watermark` | Memory pressure; flow control imminent |
| `rabbitmq_node_disk_free` | < `disk_free_limit` | Disk alarm; broker blocks publishers |
| `rabbitmq_connections` | Sudden drop | Connection storm or broker restart |
| `rabbitmq_global_messages_acknowledged_total` rate | Sudden drop | Consumer throughput degradation |

### RabbitMQ Management API Queries

```bash
# List all queues with depth and consumer count
curl -u admin:$PASS https://rabbitmq:15671/api/queues/%2F | \
  jq '.[] | {name, messages, consumers, state}'

# Specific queue stats
curl -u admin:$PASS https://rabbitmq:15671/api/queues/%2Fproduction%2Forders/inventory.reserve

# Connections
curl -u admin:$PASS https://rabbitmq:15671/api/connections | jq '.[].name'
```

### OpenTelemetry Tracing

Propagate trace context through message headers for end-to-end distributed tracing.
*(pika implementation: `../frameworks/python-pika.md` §11)*

```
# ✅ Publisher: inject trace context into message headers
function publish_event(event):
    headers = {}
    with tracer.start_span("rabbitmq.publish"):
        otel.inject(headers)   # adds traceparent, tracestate to headers
        publish(
            exchange="orders.events",
            routing_key="orders.order.created",
            body=json(event),
            properties={delivery_mode: persistent, message_id: uuid4(), headers: headers},
        )

# ✅ Consumer: extract and continue trace
function on_message(message):
    context = otel.extract(message.properties.headers or {})
    with tracer.start_span("rabbitmq.consume", context=context):
        process_event(json_parse(message.body))
        message.ack()
```

### Logging Standards

```
# ✅ Structured log on every message lifecycle event
function on_message(message):
    log.info(
        "message.received",
        queue=message.routing_key,
        message_id=message.properties.message_id,
        correlation_id=message.properties.correlation_id,
        delivery_tag=message.delivery_tag,
        redelivered=message.redelivered,
    )
```

---

## 12. Configuration & Tuning — deep tuning sub-block

The networking, memory/disk, flow-control, and heartbeat tuning lines of the
`rabbitmq.conf` production template (the day-to-day limits/management/logging lines
stay in `SKILL.md` §12):

```ini
## Networking
listeners.tcp = none          # disable plaintext in production
listeners.ssl.default = 5671

## Memory and Disk
vm_memory_high_watermark.relative = 0.6       # trigger flow control at 60% RAM
vm_memory_high_watermark_paging_ratio = 0.75  # start paging at 75% of watermark
disk_free_limit.relative = 2.0                # need 2× current data as free disk

## Flow Control
credit_flow_default_credit = {400, 200}       # {initial_credit, more_credit}

## Heartbeat (prevents zombie connections)
heartbeat = 60
```
