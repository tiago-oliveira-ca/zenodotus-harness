---
name: zeno-redis-patterns
description: >
  Redis patterns for caching, distributed locks, pub/sub, and connection management —
  and the canonical, single-source-of-truth implementation for production rate limiting
  (fixed-window and sliding-window, Redis-backed). Use whenever adding a cache layer,
  building distributed coordination, throttling an API, or reviewing whether a rate
  limiter is safe for a multi-replica deployment. Any skill needing rate-limiting
  guidance should point here rather than reimplementing it. Trigger on: "add caching",
  "cache this endpoint", "rate limit this API", "throttle requests", "distributed lock",
  "Redis pattern", "session storage", "pub/sub", "Redis streams", "cache invalidation",
  "connection pooling for Redis", "Redis cluster", "prevent thundering herd".
---

# Redis Patterns

Redis is an in-memory data structure store — strings, hashes, lists, sets, sorted sets,
streams. Individual commands are atomic on a single instance; multi-step workflows need
Lua scripts, `MULTI`/`EXEC`, or a pipeline to stay atomic. Clients talk RESP over TCP;
always use a connection pool, never a fresh connection per request.

## When to reach for this skill

- Adding a cache layer in front of a database or slow computation
- Throttling or rate-limiting a public or internal API
- Coordinating work across processes or replicas (locks, leader election)
- Storing sessions, short-lived tokens, or leaderboards
- Fanning out events via Pub/Sub or Streams
- Configuring Redis for production: pooling, eviction, clustering, HA

## Data structure cheat sheet

| Use case | Structure | Example key |
|---|---|---|
| Simple cache | String | `product:123` |
| User session | Hash | `session:abc` |
| Leaderboard | Sorted Set | `scores:weekly` |
| Unique visitors | Set | `visitors:2024-01-01` |
| Activity feed | List | `feed:user:456` |
| Event stream | Stream | `events:orders` |
| Counters / rate limits | String (`INCR`) or Sorted Set | `ratelimit:user:123` |
| Approximate unique count | HyperLogLog | `hll:pageviews` |

## Caching patterns

**Cache-aside (lazy loading)** — read path checks cache first, falls through to the
source of truth on miss, then populates the cache:

```python
def get_product(product_id: int):
    cache_key = f"product:{product_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    product = db.query("SELECT * FROM products WHERE id = %s", product_id)
    r.setex(cache_key, 3600, json.dumps(product))  # TTL: 1 hour
    return product
```

**Write-through** — update the source of truth, then immediately overwrite the cache
entry in the same request, for stronger consistency than cache-aside:

```python
def update_product(product_id: int, data: dict):
    db.execute("UPDATE products SET ... WHERE id = %s", product_id)
    r.setex(f"product:{product_id}", 3600, json.dumps(data))
```

**Tag-based invalidation** — group related keys under a set so a category change can
invalidate every cached entry that depends on it:

```python
def cache_product(product_id: int, category_id: int, data: dict):
    key, tag = f"product:{product_id}", f"tag:category:{category_id}"
    pipe = r.pipeline(transaction=True)
    pipe.setex(key, 3600, json.dumps(data))
    pipe.sadd(tag, key)
    pipe.expire(tag, 3600)
    pipe.execute()

def invalidate_category(category_id: int):
    tag = f"tag:category:{category_id}"
    keys = r.smembers(tag)
    if keys:
        r.delete(*keys)
    r.delete(tag)
```

**Cache miss stampede prevention** — take a lock around the fetch so a cold cache
under concurrent load triggers one recomputation, not N:

```python
def get_with_lock(key: str, fetch_fn, ttl: int = 300):
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    with local_lock_for(key):          # in-process only — see note below
        cached = r.get(key)            # re-check after acquiring
        if cached:
            return json.loads(cached)
        value = fetch_fn()
        r.setex(key, ttl, json.dumps(value))
        return value
```

> An in-process lock only protects a single process. For multi-process or multi-replica
> deployments, replace it with the distributed lock below — the same constraint that
> makes in-process rate limiting wrong (next section) applies here too.

## Rate Limiting

**This section is the canonical implementation for production rate limiting in this
repo.** Any skill that needs to throttle an API — including `zeno-security-review` —
should link here (`zeno-redis-patterns#rate-limiting`) instead of reimplementing its own
limiter.

**Do not use an in-process limiter (e.g. `express-rate-limit` with its default memory
store) for a production API.** It fails in three specific ways:

| Failure mode | Why it happens |
|---|---|
| Resets on every deploy | Counters live in process memory; a restart zeroes them |
| Doesn't work across replicas | Each replica has its own counter, so N replicas silently multiply the effective limit by N |
| Fails open under memory pressure | No shared state to fall back to, so a crashed/restarted process temporarily allows unlimited traffic |

A rate limiter must live in a store shared by every replica and outlive process
restarts — that means Redis (or an equivalent shared store), never local memory.

**Fixed window** — simple, cheap, allows brief bursts at window boundaries:

```python
def is_rate_limited(user_id: int, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}:{int(time.time()) // window}"
    pipe = r.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, window)
    count, _ = pipe.execute()
    return count > limit
```

**Sliding window (Lua, atomic)** — accurate per-user throttling with no boundary burst:

```lua
-- sliding_window.lua
-- BOTH keys are declared in KEYS. A script must never construct a key name it did not
-- receive: under Redis Cluster an undeclared key can hash to a different slot than the
-- declared one and the call is rejected (CROSSSLOT), so the script works on a single node
-- and fails in the topology you actually deploy. Pass the two keys in the same hash tag —
-- e.g. rl:{user:42} and rl:{user:42}:seq — so they are guaranteed co-located.
local key = KEYS[1]
local seq_key = KEYS[2]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local ttl = math.ceil(window / 1000)

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)

if count < limit then
    local seq = redis.call('INCR', seq_key)
    redis.call('EXPIRE', seq_key, ttl)
    redis.call('ZADD', key, now, now .. '-' .. seq)
    redis.call('EXPIRE', key, ttl)
    return 1
end
return 0
```

Invoke with both keys, hash-tagged so Cluster co-locates them:

```python
# numkeys=2, then the two keys, then the args
allowed = client.eval(
    SLIDING_WINDOW_LUA, 2,
    f"rl:{{{user_id}}}", f"rl:{{{user_id}}}:seq",
    int(time.time() * 1000), window_ms, limit,
)
```

```python
sliding_window = r.register_script(open('sliding_window.lua').read())

def allow_request(user_id: int) -> bool:
    key = f"ratelimit:sliding:{user_id}"
    now = int(time.time() * 1000)
    return bool(sliding_window(keys=[key], args=[now, 60000, 100]))
```

Use fixed-window for low-traffic endpoints where occasional boundary bursts are
tolerable; use sliding-window when you need an accurate per-user cap.

## Distributed locks

**Single-node lock (`SET NX PX` + token-checked release):**

```python
def acquire_lock(resource: str, ttl_ms: int = 5000) -> str | None:
    token = str(uuid.uuid4())
    acquired = r.set(f"lock:{resource}", token, px=ttl_ms, nx=True)
    return token if acquired else None

def release_lock(resource: str, token: str) -> bool:
    release_script = """
    if redis.call('get', KEYS[1]) == ARGV[1] then
        return redis.call('del', KEYS[1])
    else
        return 0
    end
    """
    return bool(r.eval(release_script, 1, f"lock:{resource}", token))

token = acquire_lock("order:payment:123")
if token:
    try:
        process_payment()
    finally:
        release_lock("order:payment:123", token)
```

The release script checks the token before deleting — without it, a process could
release a lock it no longer holds (e.g. after its own TTL expired and someone else
acquired it). For multi-node Redis deployments, use `redlock-py`, which implements the
full Redlock algorithm rather than a single-instance approximation.

## Pub/Sub and Streams

**Pub/Sub** — fire-and-forget broadcast, no delivery guarantee, no replay:

```python
def publish_event(channel: str, payload: dict):
    r.publish(channel, json.dumps(payload))

def subscribe_events(channel: str):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    for message in pubsub.listen():
        if message['type'] == 'message':
            handle(json.loads(message['data']))
```

**Streams** — durable, consumer-group based, at-least-once delivery, replayable:

```python
def emit(stream: str, event: dict):
    r.xadd(stream, event, maxlen=10000)

try:
    r.xgroup_create('events:orders', 'processor', id='0', mkstream=True)
except Exception:
    pass  # group already exists

def consume(stream: str, group: str, consumer: str):
    while True:
        messages = r.xreadgroup(group, consumer, {stream: '>'}, count=10, block=2000)
        for _, entries in (messages or []):
            for msg_id, data in entries:
                process(data)
                r.xack(stream, group, msg_id)
```

Prefer Streams over Pub/Sub whenever you need delivery guarantees, consumer groups, or
replay for late-joining consumers.

## Key design and TTL

```
resource:id:field        user:123:profile
namespace:resource:id    myapp:ratelimit:user:123
resource:date            stats:pageviews:2024-01-01
```

| Data type | Suggested TTL |
|---|---|
| User session | 24h |
| API response cache | 5–15 min |
| Rate limit window | Match window size |
| Short-lived token | 5–10 min |
| Leaderboard | 1h–24h |
| Static/reference data | 1h–1 week |

Every key gets a TTL. A key without one accumulates forever and becomes memory
pressure nobody notices until eviction starts.

## Connection management

```python
from redis import ConnectionPool, Redis

pool = ConnectionPool(
    host='localhost', port=6379, db=0, max_connections=20,
    decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
)
r = Redis(connection_pool=pool)
```

Cluster mode and Sentinel (HA) use the same client interface with a different entry
point (`RedisCluster`, `Sentinel`) — pick the one that matches your topology, not the
one that's simplest to type.

## Eviction policies

| Policy | Behavior | Best for |
|---|---|---|
| `noeviction` | Errors on write when full | Queues / critical data that must never be silently dropped |
| `allkeys-lru` | Evicts least recently used | General-purpose cache |
| `volatile-lru` | LRU, only among keys with a TTL | Mixed cache + persistent data in one instance |
| `allkeys-lfu` | Evicts least frequently used | Skewed access patterns |
| `volatile-ttl` | Evicts soonest-to-expire first | Prioritize keeping long-lived data |

Set via `redis.conf`: `maxmemory-policy allkeys-lru`.

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| In-process rate limiter (`express-rate-limit` memory store) on a multi-replica API | Redis-backed fixed or sliding window (see Rate Limiting above) |
| Keys with no TTL | Always set a TTL |
| `KEYS *` in production | Use `SCAN` with a cursor |
| Storing large blobs (>100KB) in Redis | Store a reference; fetch the blob from object storage |
| One Redis instance for cache, queue, and locks | Separate DBs or instances so a queue backlog can't evict cache entries |
| Releasing a distributed lock without checking the token | Always verify ownership in the release script before deleting |
| Cold-cache stampede with no lock | Use the lock-around-fetch pattern or probabilistic early expiry |
| `FLUSHALL` run casually | Scope deletes by key pattern; treat `FLUSHALL` as a destructive, deliberate action |

## Pre-flight checklist — run before delivering any Redis-backed pattern

- [ ] Every key that isn't meant to live forever has a TTL
- [ ] Any rate limiter is Redis-backed (or another shared store), never in-process memory
- [ ] Multi-step operations that must be atomic use a pipeline, `MULTI`/`EXEC`, or Lua
- [ ] Distributed locks verify the token on release, not just on acquire
- [ ] Connection access goes through a pool, not a fresh connection per call
- [ ] Cache invalidation path is defined for every cache-aside/write-through key added
- [ ] Streams are used instead of Pub/Sub wherever delivery guarantees or replay matter
- [ ] `maxmemory-policy` is set deliberately, not left at the Redis default
