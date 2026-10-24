Concrete pika/Python implementations of the broker-level standards in `../SKILL.md` — read that
file first. Section numbers below mirror `../SKILL.md`'s numbering so you can cross-reference
"the concept is in SKILL.md §X, the pika code for it is in this file's §X."

---

## §2. Exchange Types

### Direct Exchange — Point-to-Point / Task Distribution

```python
# ✅ Correct: direct exchange for command dispatch
channel.exchange_declare(
    exchange='payments.commands',
    exchange_type='direct',
    durable=True,
)
channel.queue_bind(
    queue='payments.charge',
    exchange='payments.commands',
    routing_key='charge',
)
```

### Topic Exchange — Event Broadcasting with Selective Routing

```python
# ✅ Correct: topic exchange for event routing with wildcards
channel.exchange_declare(
    exchange='orders.events',
    exchange_type='topic',
    durable=True,
)
# Bind: receive all order events
channel.queue_bind(
    queue='audit.orders',
    exchange='orders.events',
    routing_key='orders.#',           # any word after orders.*
)
# Bind: receive only order.created events
channel.queue_bind(
    queue='inventory.reserve',
    exchange='orders.events',
    routing_key='orders.order.created',
)
```

### Fanout Exchange — Broadcast

```python
# ✅ Correct: fanout for broadcast notifications
channel.exchange_declare(
    exchange='cache.invalidation',
    exchange_type='fanout',
    durable=True,
)
```

### Headers Exchange — Attribute-Based Routing

```python
# ✅ Correct: headers exchange for custom metadata routing
channel.queue_bind(
    queue='priority.orders',
    exchange='orders.routing',
    routing_key='',
    arguments={'x-match': 'all', 'priority': 'high', 'region': 'eu'},
)
```

### Exchange-to-Exchange Bindings

```python
# ✅ Correct: compose routing topology via e2e bindings
channel.exchange_bind(
    destination='notifications.fanout',
    source='orders.events',
    routing_key='orders.order.created',
)
```

---

## §3. Queue Design

```python
# ✅ Correct: declare a quorum queue (recommended default)
channel.queue_declare(
    queue='inventory.reserve',
    durable=True,
    arguments={
        'x-queue-type': 'quorum',
        'x-dead-letter-exchange': 'inventory.reserve.dlx',
        'x-message-ttl': 86_400_000,   # 24h message TTL in ms
        'x-max-length': 100_000,        # cap queue size
    }
)
# Note: x-max-length overflow behavior on QUORUM queues is version-specific
# (drop-head support and defaults changed across RabbitMQ releases).
# Verify the semantics for your broker version before relying on it.

# ✅ Correct: stream queue for replay / high-throughput fan-out
channel.queue_declare(
    queue='audit.events',
    durable=True,
    arguments={
        'x-queue-type': 'stream',
        'x-max-length-bytes': 10_737_418_240,   # 10 GB stream retention
    }
)

# ❌ Wrong: classic non-durable queue in production — messages lost on restart
channel.queue_declare(queue='orders', durable=False)
```

Single Active Consumer:

```python
arguments={'x-single-active-consumer': True}
```

---

## §4. Connections & Channels

```python
# ✅ Correct: one connection, separate channels for pub and sub
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq',
    credentials=pika.PlainCredentials('app_user', os.environ['RABBITMQ_PASSWORD']),
    heartbeat=60,
    blocked_connection_timeout=300,
    connection_attempts=3,
    retry_delay=5,
))

pub_channel  = connection.channel()   # for publishing
cons_channel = connection.channel()   # for consuming

# ❌ Wrong: new connection per message publish
def publish_event(event):
    conn = pika.BlockingConnection(...)   # expensive! opens TCP + TLS each time
    conn.channel().basic_publish(...)
    conn.close()
```

### Connection Resilience

```python
# ✅ Correct: reconnection with exponential backoff
import time
import pika

def create_connection(max_retries=5):
    delay = 1
    for attempt in range(max_retries):
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(
                host='rabbitmq',
                heartbeat=60,
            ))
        except pika.exceptions.AMQPConnectionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 30)    # cap at 30s
```

---

## §5. Message Publishing

### Persistent Messages

```python
# ✅ Correct: persistent delivery mode — survives broker restart
channel.basic_publish(
    exchange='orders.events',
    routing_key='orders.order.created',
    body=json.dumps(event_payload).encode(),
    properties=pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent,   # 2 = persistent
        content_type='application/json',
        content_encoding='utf-8',
        message_id=str(uuid.uuid4()),          # unique ID for idempotency
        correlation_id=str(request_id),        # trace parent
        timestamp=int(time.time()),
        headers={
            'event_type': 'OrderCreated',
            'schema_version': '1.0',
            'source_service': 'orders-service',
        },
    ),
)

# ❌ Wrong: non-persistent (transient) message in a durable queue offers no guarantees
properties=pika.BasicProperties(delivery_mode=1)   # transient = data lost on restart
```

### Publisher Confirms

```python
# ✅ Correct: publisher confirms for at-least-once delivery guarantee
channel.confirm_delivery()

try:
    channel.basic_publish(
        exchange='orders.events',
        routing_key='orders.order.created',
        body=payload,
        properties=pika.BasicProperties(delivery_mode=2),
        mandatory=True,   # broker returns unroutable messages instead of silently dropping
    )
except pika.exceptions.UnroutableError:
    logger.error('Message returned — no queue bound to routing key!')
    # handle unroutable message (alert, store to outbox, etc.)
except pika.exceptions.NackError:
    logger.error('Broker NACKed the message — retry or alert!')
```

---

## §6. Consumer Best Practices

### Manual Acknowledgment

```python
# ✅ Correct: manual ack — acknowledge only after successful processing
def on_message(channel, method, properties, body):
    try:
        event = json.loads(body)
        process_event(event)                          # idempotent business logic
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except TransientError as exc:
        logger.warning('Transient failure, requeueing', exc_info=exc)
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,    # retry via requeue (only for genuinely transient errors)
        )

    except PermanentError as exc:
        logger.error('Permanent failure, dead-lettering', exc_info=exc)
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,   # → DLX / DLQ for inspection
        )

channel.basic_consume(
    queue='inventory.reserve',
    on_message_callback=on_message,
    auto_ack=False,          # ❌ Never True in production
)

# ❌ Wrong: auto-ack drops messages on consumer crash mid-processing
channel.basic_consume(queue='inventory.reserve', on_message_callback=process, auto_ack=True)
```

### Prefetch Count (QoS)

```python
# ✅ Correct: set prefetch before consuming
channel.basic_qos(prefetch_count=10)   # consumer-level, recommended
```

### Idempotency

```python
# ✅ Correct: idempotent handler using message_id deduplication
def process_event(channel, method, properties, body):
    message_id = properties.message_id
    if redis_client.sismember('processed_messages', message_id):
        logger.info('Duplicate message ignored', message_id=message_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    with db.transaction():
        apply_business_logic(json.loads(body))
        redis_client.sadd('processed_messages', message_id)
        redis_client.expire('processed_messages', 86400)   # 24h TTL

    channel.basic_ack(delivery_tag=method.delivery_tag)
```

---

## §7. Dead Letter Exchanges & Retry Pattern

### Dead Letter Exchange Setup

```python
# ✅ Correct: DLX / DLQ topology declaration
def declare_queue_with_dlx(channel, queue_name, exchange_name, routing_key, retry_delay_ms=30_000):
    dlx_exchange = f'{queue_name}.dlx'
    dlq_name     = f'{queue_name}.dlq'
    retry_queue  = f'{queue_name}.retry.{retry_delay_ms // 1000}s'

    # 1. Dead Letter Exchange
    channel.exchange_declare(exchange=dlx_exchange, exchange_type='direct', durable=True)

    # 2. Dead Letter Queue (permanent failure / manual inspection)
    channel.queue_declare(queue=dlq_name, durable=True,
                          arguments={'x-queue-type': 'quorum'})
    channel.queue_bind(queue=dlq_name, exchange=dlx_exchange, routing_key='dead')

    # 3. Retry queue with TTL → re-routes back to main exchange on expiry
    channel.queue_declare(queue=retry_queue, durable=True, arguments={
        'x-queue-type': 'quorum',
        'x-message-ttl': retry_delay_ms,
        'x-dead-letter-exchange': exchange_name,   # re-inject to main exchange
        'x-dead-letter-routing-key': routing_key,
    })
    channel.queue_bind(queue=retry_queue, exchange=dlx_exchange, routing_key='retry')

    # 4. Main queue with DLX pointing to retry exchange
    channel.queue_declare(queue=queue_name, durable=True, arguments={
        'x-queue-type': 'quorum',
        'x-dead-letter-exchange': dlx_exchange,
        'x-dead-letter-routing-key': 'retry',      # first failure → retry queue
        'x-message-ttl': 86_400_000,
        'x-max-length': 100_000,
    })
```

### Exponential Backoff Retry with x-death Header

```python
# ✅ Correct: exponential backoff using x-death count header
import json

RETRY_DELAYS_MS = [5_000, 30_000, 120_000, 600_000]   # 5s, 30s, 2m, 10m
MAX_RETRIES = len(RETRY_DELAYS_MS)

def on_message(channel, method, properties, body):
    death_count = get_death_count(properties.headers)

    try:
        process_message(json.loads(body))
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        if death_count >= MAX_RETRIES:
            logger.error('Max retries exceeded, dead-lettering', deaths=death_count)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            # → goes to DLQ with routing_key='dead'
            return

        delay = RETRY_DELAYS_MS[death_count]
        logger.warning('Processing failed, retrying', attempt=death_count + 1, delay_ms=delay)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        # → goes to retry queue (TTL = delay) → re-injected to main queue

def get_death_count(headers: dict | None) -> int:
    if not headers or 'x-death' not in headers:
        return 0
    return sum(d.get('count', 1) for d in headers['x-death'])
```

---

## §8. Security — Secrets Management

```python
# ✅ Correct: read credentials from environment / secrets manager
import os
credentials = pika.PlainCredentials(
    username=os.environ['RABBITMQ_USER'],
    password=os.environ['RABBITMQ_PASSWORD'],   # injected by Vault / K8s secret
)

# ❌ Wrong: hardcoded credentials
credentials = pika.PlainCredentials('admin', 'admin')
```

---

## §9. High Availability & Clustering — Quorum Queues

```python
# ✅ Always use quorum queues for HA data safety
channel.queue_declare(
    queue='payments.charge',
    durable=True,
    arguments={
        'x-queue-type': 'quorum',
        'x-quorum-initial-group-size': 3,    # replicate to all 3 nodes
    }
)

# ❌ Wrong: classic mirrored queues — deprecated, removed in RabbitMQ 4.x
arguments={'x-ha-policy': 'all'}
```

---

## §10. Architectural Patterns — Outbox Pattern Relay

```python
# ✅ Correct: transactional outbox — write to DB and outbox atomically
with db.transaction():
    order = create_order(payload)
    db.execute(
        'INSERT INTO outbox (id, aggregate_type, event_type, payload, status) '
        'VALUES (:id, :agg, :evt, :payload, :status)',
        id=uuid4(), agg='Order', evt='OrderCreated',
        payload=json.dumps(order.to_dict()), status='PENDING'
    )

# Background relay process polls outbox and publishes:
def relay_outbox():
    rows = db.query("SELECT * FROM outbox WHERE status='PENDING' LIMIT 100 FOR UPDATE SKIP LOCKED")
    for row in rows:
        channel.basic_publish(
            exchange='orders.events',
            routing_key=f'orders.{row.event_type.lower()}',
            body=row.payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
                message_id=str(row.id),
            ),
        )
        db.execute("UPDATE outbox SET status='PUBLISHED' WHERE id=:id", id=row.id)
```

---

## §11. Observability & Monitoring

### OpenTelemetry Tracing

```python
from opentelemetry import trace
from opentelemetry.propagate import inject

tracer = trace.get_tracer(__name__)

# ✅ Publisher: inject trace context into message headers
def publish_event(channel, event):
    headers = {}
    with tracer.start_as_current_span('rabbitmq.publish'):
        inject(headers)   # adds traceparent, tracestate to headers dict
        channel.basic_publish(
            exchange='orders.events',
            routing_key='orders.order.created',
            body=json.dumps(event).encode(),
            properties=pika.BasicProperties(
                delivery_mode=2,
                message_id=str(uuid.uuid4()),
                headers=headers,
            ),
        )

# ✅ Consumer: extract and continue trace
from opentelemetry.propagate import extract

def on_message(channel, method, properties, body):
    context = extract(properties.headers or {})
    with tracer.start_as_current_span('rabbitmq.consume', context=context):
        process_event(json.loads(body))
        channel.basic_ack(delivery_tag=method.delivery_tag)
```

### Logging Standards

```python
# ✅ Structured log on every message lifecycle event
import structlog

log = structlog.get_logger()

def on_message(channel, method, properties, body):
    log.info(
        'message.received',
        queue=method.routing_key,
        message_id=properties.message_id,
        correlation_id=properties.correlation_id,
        delivery_tag=method.delivery_tag,
        redelivered=method.redelivered,
    )
```
