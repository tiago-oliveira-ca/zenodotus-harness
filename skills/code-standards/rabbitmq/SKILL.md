---
name: rabbitmq
description: >
  Production-grade RabbitMQ standards covering exchange types, queue design (quorum/stream),
  message reliability, acknowledgments, dead-letter exchanges, retry patterns, security (TLS,
  vhosts, RBAC), observability, and architectural patterns (Saga, Outbox, CQRS). Use whenever
  writing, reviewing, or designing RabbitMQ messaging code or broker configuration. Trigger
  on: "RabbitMQ", "message queue", "AMQP", "publish a message", "consumer group", "dead
  letter queue", "retry pattern", "exchange setup", "quorum queue", or any messaging
  broker question involving RabbitMQ.
---

# RabbitMQ Code Standards & Best Practices

As an AI assistant, you must adhere strictly to the following RabbitMQ development best practices when generating, reviewing, or refactoring messaging code and broker configuration.

**This skill is broker- and protocol-level, not client-library-specific.** Every rule below
applies identically whether the consumer/producer is written in Python, Java, Go, or Node.js —
only the client-library syntax differs. Code samples use short language-neutral pseudocode to
express the AMQP concept (exchange declarations, queue arguments, ack/nack semantics, message
properties). For a concrete, fully-worked Python implementation using `pika`, see
`frameworks/python-pika.md` — it mirrors this file's section structure section-for-section.

**Kafka work is out of scope here.** This skill is authoritative for AMQP-specific
mechanics (idempotent consumers via `message_id` + a dedup store, manual-ack/DLX retry
topology). For Kafka's own model — per-partition ordering, schema-registry
compatibility, consumer-driven contract testing — see the Kafka event-driven testing
section of `../python/references/ddd-tdd-bdd-workflow.md`.

---

## 1. Naming Conventions

Consistent, descriptive names make broker topology understandable without inspecting code.

| Object | Convention | Example |
|---|---|---|
| Exchanges | `snake_case`, dot-separated domain | `orders.events`, `payments.commands` |
| Queues | `snake_case`, `<service>.<action>` | `inventory.reserve`, `email.notifications` |
| Dead Letter Exchange | `<exchange>.dlx` | `orders.events.dlx` |
| Dead Letter Queue | `<queue>.dlq` | `inventory.reserve.dlq` |
| Retry Queue | `<queue>.retry.<delay>` | `inventory.reserve.retry.30s` |
| Routing Keys | `<domain>.<entity>.<event>` (dot-notation) | `orders.order.created`, `payments.payment.failed` |
| Virtual Hosts | `/<env>/<app>` or `/<team>` | `/production/orders`, `/staging/payments` |
| Consumers | `<service>-<queue>-consumer` | `inventory-reserve-consumer` |

**Key Rules:**

- **All lowercase with dots or underscores** — no camelCase, no spaces.
- **Be explicit** — names must describe the purpose without reading source code.
- **Include the domain** — prefix queue and exchange names with the owning domain/service.
- **Never use the default exchange in production** — always declare and use named exchanges.

---

## 2. Exchange Types

Choose the exchange type that matches your routing semantics exactly.
*(pika implementation: `frameworks/python-pika.md` §2)*

### Direct Exchange — Point-to-Point / Task Distribution

Routes messages to queues whose binding key **exactly** matches the routing key.

```
# ✅ Correct: direct exchange for command dispatch
declare_exchange(name="payments.commands", type=direct, durable=true)
bind_queue(queue="payments.charge", exchange="payments.commands", routing_key="charge")
```

**Use when:** Sending a specific command to one known queue. Task queues where N consumers compete for work.

### Topic Exchange — Event Broadcasting with Selective Routing

Routes messages based on **wildcard pattern matching** on the routing key (`*` = one word, `#` = zero or more).

```
# ✅ Correct: topic exchange for event routing with wildcards
declare_exchange(name="orders.events", type=topic, durable=true)

# Bind: receive all order events
bind_queue(queue="audit.orders", exchange="orders.events", routing_key="orders.#")

# Bind: receive only order.created events
bind_queue(queue="inventory.reserve", exchange="orders.events", routing_key="orders.order.created")
```

**Use when:** Event-driven microservices, pub/sub with service-specific filtering.

### Fanout Exchange — Broadcast

Routes messages to **all bound queues**, ignoring routing keys entirely.

```
# ✅ Correct: fanout for broadcast notifications
declare_exchange(name="cache.invalidation", type=fanout, durable=true)
```

**Use when:** Cache invalidation, real-time notifications, log pipelines. **Avoid** if any selective filtering is needed — use topic instead.

### Headers Exchange — Attribute-Based Routing

Routes based on **message header attributes** rather than routing key.

```
# ✅ Correct: headers exchange for custom metadata routing
bind_queue(
    queue="priority.orders",
    exchange="orders.routing",
    routing_key="",
    arguments={x-match: all, priority: high, region: eu},
)
```

**Use when:** Routing decisions depend on multiple orthogonal attributes; routing key does not capture all required dimensions.

### Exchange-to-Exchange Bindings

Bind exchanges to other exchanges to build complex, reusable routing topologies without duplicating bindings.

```
# ✅ Correct: compose routing topology via e2e bindings
bind_exchange(
    destination="notifications.fanout",
    source="orders.events",
    routing_key="orders.order.created",
)
```

---

## 3. Queue Design

*(pika implementation: `frameworks/python-pika.md` §3)*

### Queue Types

| Type | Use When | Notes |
|---|---|---|
| **Quorum Queue** | Any production workload requiring durability | Modern default; Raft-based replication, data-safe |
| **Classic Queue** | Legacy compatibility only | Being phased out; prefer quorum unless constraints exist |
| **Stream Queue** | High-throughput, replay, multi-consumer fan-out at scale | Append-only log; consumers can re-read from any offset |

```
# ✅ Correct: declare a quorum queue (recommended default)
declare_queue(
    name="inventory.reserve",
    durable=true,
    arguments={
        x-queue-type: quorum,
        x-dead-letter-exchange: "inventory.reserve.dlx",
        x-message-ttl: 86_400_000,     # 24h message TTL in ms
        x-max-length: 100_000,          # cap queue size
    }
)
# Note: x-max-length overflow behavior on QUORUM queues is version-specific
# (drop-head support and defaults changed across RabbitMQ releases).
# Verify the semantics for your broker version before relying on it.

# ✅ Correct: stream queue for replay / high-throughput fan-out
declare_queue(
    name="audit.events",
    durable=true,
    arguments={
        x-queue-type: stream,
        x-max-length-bytes: 10_737_418_240,   # 10 GB stream retention
    }
)

# ❌ Wrong: classic non-durable queue in production — messages lost on restart
declare_queue(name="orders", durable=false)
```

### Queue Configuration Rules

- **Always declare queues as `durable=true`** for any production workload.
- **Always set `x-dead-letter-exchange`** on every workqueue — unprocessable messages must go somewhere inspectable.
- **Set `x-message-ttl`** to prevent unbounded queue growth from stale messages.
- **Set `x-max-length`** or `x-max-length-bytes` to cap queue size and protect broker memory.
- **Keep queues short** — large queues cause RabbitMQ to page messages to disk, severely degrading throughput.
- **Prefer many short queues over one giant queue** — parallelism is easier and failure impact is smaller.
- **Enable Single Active Consumer** when strict per-queue message ordering is required:

```
arguments={x-single-active-consumer: true}
```

---

## 4. Connections & Channels

*(pika implementation: `frameworks/python-pika.md` §4)*

### Core Rules

- **Reuse TCP connections** — opening a new connection per operation incurs a significant handshake cost.
- **One channel per thread/coroutine** — channels are lightweight; multiplex work across one connection via channels.
- **Use separate connections for publishers and consumers** — consumer back-pressure won't stall publishers.
- **Never share a channel across threads** — channels are not thread-safe.

```
# ✅ Correct: one connection, separate channels for pub and sub
connection = open_connection(
    host="rabbitmq",
    credentials=(user="app_user", password=env("RABBITMQ_PASSWORD")),
    heartbeat=60,
    blocked_connection_timeout=300,
    connection_attempts=3,
    retry_delay=5,
)

pub_channel  = connection.open_channel()   # for publishing
cons_channel = connection.open_channel()   # for consuming

# ❌ Wrong: new connection per message publish
function publish_event(event):
    conn = open_connection(...)   # expensive! opens TCP + TLS each time
    conn.open_channel().publish(...)
    conn.close()
```

### Connection Resilience

```
# ✅ Correct: reconnection with exponential backoff
function create_connection(max_retries=5):
    delay = 1
    for attempt in 1..max_retries:
        try:
            return open_connection(host="rabbitmq", heartbeat=60)
        catch ConnectionError:
            if attempt == max_retries:
                raise
            sleep(delay)
            delay = min(delay * 2, 30)    # cap at 30s
```

---

## 5. Message Publishing

*(pika implementation: `frameworks/python-pika.md` §5)*

### Persistent Messages

```
# ✅ Correct: persistent delivery mode — survives broker restart
publish(
    exchange="orders.events",
    routing_key="orders.order.created",
    body=json(event_payload),
    properties={
        delivery_mode: persistent,        # AMQP delivery-mode 2 = persistent
        content_type: "application/json",
        content_encoding: "utf-8",
        message_id: uuid4(),              # unique ID for idempotency
        correlation_id: request_id,       # trace parent
        timestamp: now(),
        headers: {
            event_type: "OrderCreated",
            schema_version: "1.0",
            source_service: "orders-service",
        },
    },
)

# ❌ Wrong: non-persistent (transient) message in a durable queue offers no guarantees
properties={delivery_mode: transient}   # AMQP delivery-mode 1 = data lost on restart
```

### Publisher Confirms

Always enable publisher confirms in production to guarantee messages reached the broker:

```
# ✅ Correct: publisher confirms for at-least-once delivery guarantee
channel.enable_publisher_confirms()

try:
    channel.publish(
        exchange="orders.events",
        routing_key="orders.order.created",
        body=payload,
        properties={delivery_mode: persistent},
        mandatory=true,   # broker returns unroutable messages instead of silently dropping
    )
catch UnroutableError:
    log.error("Message returned — no queue bound to routing key!")
    # handle unroutable message (alert, store to outbox, etc.)
catch NackError:
    log.error("Broker NACKed the message — retry or alert!")
```

### Message Size

- **Keep messages small** (< 128 KB). For large payloads, store the data externally (S3, database) and publish a reference.
- **Use `content_type`** to declare serialization format explicitly (`application/json`, `application/protobuf`).
- **Include `message_id`** on every message for idempotency and deduplication tracking.
- **Include `correlation_id`** (trace/request ID) on every message for distributed tracing.

---

## 6. Consumer Best Practices

*(pika implementation: `frameworks/python-pika.md` §6)*

### Manual Acknowledgment

**Always use manual ack** in production. Auto-ack drops messages on consumer crash.

```
# ✅ Correct: manual ack — acknowledge only after successful processing
function on_message(message):
    try:
        event = json_parse(message.body)
        process_event(event)              # idempotent business logic
        message.ack()

    catch TransientError as exc:
        log.warning("Transient failure, requeueing", error=exc)
        message.nack(requeue=true)   # retry via requeue (only for genuinely transient errors)

    catch PermanentError as exc:
        log.error("Permanent failure, dead-lettering", error=exc)
        message.nack(requeue=false)  # → DLX / DLQ for inspection

consume(queue="inventory.reserve", handler=on_message, auto_ack=false)  # ❌ Never auto-ack=true in production

# ❌ Wrong: auto-ack drops messages on consumer crash mid-processing
consume(queue="inventory.reserve", handler=process, auto_ack=true)
```

### Prefetch Count (QoS)

```
# ✅ Correct: set prefetch before consuming
channel.set_qos(prefetch_count=10)   # consumer-level, recommended

# Rules:
# prefetch_count=1  → slow processors / many consumers / strict fairness
# prefetch_count=10-50 → balanced; good starting point
# prefetch_count=100+ → fast processors / few consumers / maximize throughput
# prefetch_count=0 → DANGEROUS: unlimited — can OOM consumer on restart flood
```

**Prefetch tuning guide:**

| Scenario | Recommended `prefetch_count` |
|---|---|
| Slow, variable processing (DB writes, HTTP calls) | 1–5 |
| Balanced workloads | 10–20 |
| Fast processing (in-memory transforms) | 100–500 |
| Single consumer, high throughput | 500–1000 |

**Never** set `prefetch_count=0` (unlimited) — all unacknowledged messages redelivered if consumer crashes.

### Idempotency

Every consumer **must** be idempotent — the same message may be delivered more than once (at-least-once delivery).

```
# ✅ Correct: idempotent handler using message_id deduplication
function process_event(message):
    message_id = message.properties.message_id
    if dedup_store.contains("processed_messages", message_id):
        log.info("Duplicate message ignored", message_id=message_id)
        message.ack()
        return

    with db.transaction():
        apply_business_logic(json_parse(message.body))
        dedup_store.add("processed_messages", message_id, ttl=86400)   # 24h TTL

    message.ack()
```

---

## 7. Dead Letter Exchanges & Retry Pattern

*(pika implementation: `frameworks/python-pika.md` §7)*

### Dead Letter Exchange Setup

Every production queue must have a DLX configured from declaration time:

```
# ✅ Correct: DLX / DLQ topology declaration
function declare_queue_with_dlx(queue_name, exchange_name, routing_key, retry_delay_ms=30_000):
    dlx_exchange = queue_name + ".dlx"
    dlq_name     = queue_name + ".dlq"
    retry_queue  = queue_name + ".retry." + (retry_delay_ms / 1000) + "s"

    # 1. Dead Letter Exchange
    declare_exchange(name=dlx_exchange, type=direct, durable=true)

    # 2. Dead Letter Queue (permanent failure / manual inspection)
    declare_queue(name=dlq_name, durable=true, arguments={x-queue-type: quorum})
    bind_queue(queue=dlq_name, exchange=dlx_exchange, routing_key="dead")

    # 3. Retry queue with TTL → re-routes back to main exchange on expiry
    declare_queue(name=retry_queue, durable=true, arguments={
        x-queue-type: quorum,
        x-message-ttl: retry_delay_ms,
        x-dead-letter-exchange: exchange_name,   # re-inject to main exchange
        x-dead-letter-routing-key: routing_key,
    })
    bind_queue(queue=retry_queue, exchange=dlx_exchange, routing_key="retry")

    # 4. Main queue with DLX pointing to retry exchange
    declare_queue(name=queue_name, durable=true, arguments={
        x-queue-type: quorum,
        x-dead-letter-exchange: dlx_exchange,
        x-dead-letter-routing-key: "retry",      # first failure → retry queue
        x-message-ttl: 86_400_000,
        x-max-length: 100_000,
    })
```

### Exponential Backoff Retry with x-death Header

The `x-death` header is populated by the broker itself (AMQP protocol-level behavior) every
time a message is dead-lettered — it is an array of death records, each with a `count` field,
and is available to a consumer in any client library via the message's headers.

```
# ✅ Correct: exponential backoff using x-death count header
RETRY_DELAYS_MS = [5_000, 30_000, 120_000, 600_000]   # 5s, 30s, 2m, 10m
MAX_RETRIES = length(RETRY_DELAYS_MS)

function on_message(message):
    death_count = get_death_count(message.properties.headers)

    try:
        process_message(json_parse(message.body))
        message.ack()

    catch Exception as exc:
        if death_count >= MAX_RETRIES:
            log.error("Max retries exceeded, dead-lettering", deaths=death_count)
            message.nack(requeue=false)
            # → goes to DLQ with routing_key="dead"
            return

        delay = RETRY_DELAYS_MS[death_count]
        log.warning("Processing failed, retrying", attempt=death_count + 1, delay_ms=delay)
        message.nack(requeue=false)
        # → goes to retry queue (TTL = delay) → re-injected to main queue

function get_death_count(headers):
    if headers is empty or "x-death" not in headers:
        return 0
    return sum(record.count for record in headers["x-death"])
```

### DLQ Monitoring & Reprocessing

```
# ✅ Correct: alert on DLQ growth, provide reprocess tooling
# Monitor DLQ depth: if >0 for >5 minutes → PagerDuty alert

# Manual reprocess: use a dynamic shovel to move DLQ messages back to the
# main exchange (requires the rabbitmq_shovel plugin)
rabbitmqctl set_parameter shovel reprocess-inventory-dlq \
  '{"src-uri": "amqp://", "src-queue": "inventory.reserve.dlq",
    "dest-uri": "amqp://", "dest-exchange": "inventory.events",
    "dest-exchange-key": "inventory.reserve.retry",
    "src-delete-after": "queue-length"}'
# Alternatively: a dedicated reprocessor consumer that reads the DLQ,
# inspects x-death headers, and republishes with backoff.
```

---

## 8. Security

Full detail (vhost layout, least-privilege RBAC, deleting `guest`, TLS/mTLS configuration,
secrets management) lives in `references/operations.md` — load it before configuring
broker security or reviewing a production topology. Orientation: one vhost per
environment × application; per-service users with regex-scoped configure/write/read
permissions; delete the default `guest` user; TLS-only (5671) with mTLS for
service-to-service connections; credentials from a secrets manager, never hardcoded.

---

## 9. High Availability & Clustering

Full detail (cluster topology, quorum-queue arguments, load balancing) lives in
`references/operations.md` — load it before designing an HA deployment. Orientation:
minimum 3 nodes with `cluster_partition_handling = pause_minority`; quorum queues
(`x-queue-type: quorum`) for HA — classic mirrored queues are deprecated and removed in
4.x; front the cluster with a load balancer and spread connections across nodes.

---

## 10. Architectural Patterns

### Competing Consumers (Work Queue)

Scale processing horizontally by connecting multiple consumers to the same queue. RabbitMQ distributes messages round-robin.

```
Publisher → Direct Exchange → work.queue → Consumer 1
                                        → Consumer 2
                                        → Consumer 3
```

**Rules:** Set `prefetch_count` to control fair dispatch. Use quorum queues for HA. Each consumer must be idempotent.

### Pub/Sub with Topic Exchange

```
Publisher → Topic Exchange (orders.events)
               ├─ routing: orders.# → audit.orders queue → Audit Service
               ├─ routing: orders.order.created → inventory.reserve queue → Inventory Service
               └─ routing: orders.order.created → email.notifications queue → Email Service
```

### Outbox Pattern (Guaranteed Delivery)

Prevent losing events when the database commits but the publish call fails.

> For the database-agnostic version of this pattern (not RabbitMQ-specific), see
> `code-standards/software-architecture/references/design-patterns.md`'s Outbox Pattern section.

*(pika implementation: `frameworks/python-pika.md` §10)*

```
# ✅ Correct: transactional outbox — write to DB and outbox atomically
with db.transaction():
    order = create_order(payload)
    db.execute(
        "INSERT INTO outbox (id, aggregate_type, event_type, payload, status) "
        "VALUES (:id, :agg, :evt, :payload, :status)",
        id=uuid4(), agg="Order", evt="OrderCreated",
        payload=json(order), status="PENDING"
    )

# Background relay process polls outbox and publishes:
function relay_outbox():
    rows = db.query("SELECT * FROM outbox WHERE status='PENDING' LIMIT 100 FOR UPDATE SKIP LOCKED")
    for row in rows:
        publish(
            exchange="orders.events",
            routing_key="orders." + lower(row.event_type),
            body=row.payload,
            properties={delivery_mode: persistent, message_id: row.id},
        )
        db.execute("UPDATE outbox SET status='PUBLISHED' WHERE id=:id", id=row.id)
```

### Saga Pattern (Distributed Transactions)

Orchestrate multi-service workflows via compensating transactions:

```
OrderService  →  orders.events (order.created)
                 ↓
InventoryService (reserve stock)
  → success: inventory.events (stock.reserved) → PaymentService
  → failure: inventory.events (stock.failed)   → OrderService (compensate: cancel order)
```

**Rules:** Every saga step must be idempotent and define a compensating action. Include a `correlation_id` on all messages to correlate saga steps.

### CQRS + Event Sourcing

```
Command → Command Handler → DB (write model) + publishes domain events
Domain events → Topic Exchange → read model projectors (Update query-side DB)
                               → other bounded context consumers
```

---

## 11. Observability & Monitoring

Full detail (core plugins, Prometheus scrape config, the alert-threshold table, management
API queries, OpenTelemetry trace propagation, logging standards) lives in
`references/operations.md` — load it before wiring monitoring or tracing. Orientation:
enable `rabbitmq_prometheus` + `rabbitmq_management` on every deployment; alert on queue
depth, zero consumers, DLQ depth > 0, memory watermark, and free disk; propagate trace
context through message headers; structured-log every message lifecycle event.

---

## 12. Configuration & Tuning

The deep tuning sub-block of the `rabbitmq.conf` production template — networking/listener
setup, memory and disk watermarks, credit-based flow control, and heartbeat — lives in
`references/operations.md`; load it before tuning a production broker. Orientation:
TLS-only listeners, flow control triggered at 60% RAM, 2× free-disk headroom,
`heartbeat = 60`. Day-to-day configuration (limits, management, logging) stays below.

### `rabbitmq.conf` Production Template

```ini
## Queue / Message limits
max_message_size = 134217728    # 128 MB hard limit

## Management
management.load_definitions = /etc/rabbitmq/definitions.json   # load topology on boot

## Logging
log.file.level = warning
log.console = true
log.console.level = info
log.console.formatter = json
```

### Topology-as-Code (Definitions)

Declare all exchanges, queues, bindings, users, and vhosts in a versioned `definitions.json`. Load it at broker startup to ensure consistent, reproducible topology:

```json
{
  "vhosts": [{ "name": "/production/orders" }],
  "users": [{
    "name": "orders_service",
    "password_hash": "<bcrypt-hash>",
    "tags": ""
  }],
  "permissions": [{
    "user": "orders_service",
    "vhost": "/production/orders",
    "configure": "^(orders|inventory)\\.",
    "write": "^orders\\.events$",
    "read": "^inventory\\..*$"
  }],
  "exchanges": [{
    "name": "orders.events",
    "vhost": "/production/orders",
    "type": "topic",
    "durable": true,
    "auto_delete": false
  }],
  "queues": [{
    "name": "inventory.reserve",
    "vhost": "/production/orders",
    "durable": true,
    "arguments": {
      "x-queue-type": "quorum",
      "x-dead-letter-exchange": "inventory.reserve.dlx",
      "x-message-ttl": 86400000,
      "x-max-length": 100000
    }
  }],
  "bindings": [{
    "source": "orders.events",
    "vhost": "/production/orders",
    "destination": "inventory.reserve",
    "destination_type": "queue",
    "routing_key": "orders.order.created"
  }]
}
```

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| Using the default exchange in production | Always declare and use named exchanges |
| camelCase or spaces in exchange/queue names | All lowercase with dots or underscores, domain-prefixed |
| Fanout exchange when selective filtering is needed | Use a topic exchange |
| Classic non-durable queue in production | Durable quorum queue (`x-queue-type: quorum`) |
| Classic mirrored queues (`x-ha-policy`) | Quorum queues — mirrored queues are deprecated, removed in 4.x |
| Queue declared without a dead-letter exchange | Set `x-dead-letter-exchange` on every workqueue |
| Unbounded queue growth | Set `x-message-ttl` and `x-max-length` / `x-max-length-bytes` |
| New connection per message publish | Reuse TCP connections; multiplex via channels |
| Sharing a channel across threads | One channel per thread/coroutine — channels are not thread-safe |
| Transient messages (delivery-mode 1) in a durable queue | Persistent delivery mode (2) on every production message |
| Publishing without confirms | Enable publisher confirms and `mandatory=true` |
| Auto-ack on consumers | Manual ack only after successful processing |
| `prefetch_count=0` (unlimited) | Set an explicit prefetch per consumer channel |
| Default `guest` user or `.*` permissions in production | Delete `guest`; per-service users with least-privilege regexes |
| Plaintext AMQP (5672) or hardcoded credentials in production | TLS-only (5671); credentials from environment / secrets manager |

---

## Pre-flight checklist — run before delivering any RabbitMQ topology or messaging code

Every PR or deployment touching RabbitMQ configuration must pass:

- [ ] All exchanges and queues declared as `durable=true`.
- [ ] All queues use `x-queue-type: quorum` (not classic mirrored).
- [ ] Every queue has `x-dead-letter-exchange` configured.
- [ ] All queues have `x-max-length` or `x-message-ttl` set.
- [ ] Auto-ack disabled on all consumers; manual ack used.
- [ ] `prefetch_count` set per consumer channel (not 0).
- [ ] All consumers are idempotent (tested with duplicate delivery).
- [ ] Publisher confirms enabled on all production publishers.
- [ ] All messages use persistent delivery mode.
- [ ] `guest` user deleted or restricted to localhost.
- [ ] Per-service users with least-privilege permissions.
- [ ] TLS enabled; plaintext listener disabled.
- [ ] `rabbitmq_prometheus` plugin enabled; metrics scraped.
- [ ] DLQ alerting configured (alert when depth > 0).
- [ ] Topology declared as code (`definitions.json`) in version control.
- [ ] Retry topology tested end-to-end in staging.
