# Oracle AI Database 26ai — Vectors, RAG, OCI GenAI & Operations

## Architecture Patterns

### Integration pattern selection guide

| Pattern | Use when | Core mechanism |
|---|---|---|
| **In-database RAG** | Data sovereignty, auditing, permission alignment matter; avoid "shadow data" in a separate vector DB | VECTOR columns + HNSW/IVF indexes + `VECTOR_DISTANCE` |
| **Hybrid keyword + semantic** | Users need keyword precision AND semantic recall together | `DBMS_HYBRID_VECTOR.SEARCH` — Oracle Text + vector index unified |
| **JSON-Relational Duality** | AI-generated content must persist as JSON but link to normalized entities | `CREATE JSON RELATIONAL DUALITY VIEW` — updatable, materialized on demand |
| **ORDS as DB-as-API** | Stable, well-governed data-centric REST endpoints (reporting, CRUD) | ORDS REST + OAuth clients — NOT an unbounded "SQL over HTTP" surface |
| **OCI GenAI Agents** | Managed conversational/agent runtime is the product; compliance requires guardrails and auditability | OCI Generative AI Agents with 26ai as retrieval backend |

### Reference architecture (two coupled control planes)

```
Clients → WAF + Rate Limits → API Gateway → App Service
                                                ↓
                             Oracle AI Database 26ai (Relational + VECTOR)
                                    ↓ Vector Indexes (HNSW/IVF)
                             App Service → OCI Generative AI
                                              ↓ Guardrails (PII/Injection/Content)
                                         ← Response

Security plane: IAM Policies / Dynamic Groups, Vault/KMS, Logging + APM, Audit Logs
```

**Data/retrieval plane** (26ai) governed by: TDE, SQL Firewall, roles, DBMS_RLS.
**AI plane** governed by: OCI IAM, service limits, guardrails, logging/auditing.
The seams — embedding generation, prompt construction, output handling — are where most production failures and security issues occur.

---

## Vector Search — DBMS_VECTOR

### Index types

| Index | Characteristics | Choose when |
|---|---|---|
| **HNSW** (Hierarchical Navigable Small World) | Fastest retrieval; lives in Vector Pool (SGA); in-memory graph | Low-latency production retrieval; static or slow-changing corpus |
| **IVF** (Inverted File) | Lower memory footprint; disk-based; faster build time | Large corpus; memory-constrained; IVF DML benefits from Vector Pool too |

### Distance metrics — must match embedding model

```sql
-- cosine (default for most transformer models)
VECTOR_DISTANCE(embedding_vec, :query_vec, COSINE)

-- dot product / inner product (for models trained with dot product)
VECTOR_DISTANCE(embedding_vec, :query_vec, DOT)

-- euclidean / L2
VECTOR_DISTANCE(embedding_vec, :query_vec, EUCLIDEAN)
```

Always set the metric at **index creation time** and use the same metric in queries. Mismatch produces subtly wrong recall.

### Vector Pool sizing (SGA)

```sql
-- Check current vector pool size
SHOW PARAMETER vector_memory_size;

-- Set at startup (or in spfile) -- example: 2GB
ALTER SYSTEM SET vector_memory_size = 2G SCOPE = SPFILE;
```

Size the pool before creating HNSW indexes in production — unexpected pool exhaustion causes index creation to fail or fall back to slower modes.

### Scalar quantization for HNSW

Compress HNSW indexes (reduced storage + improved efficiency, minimal accuracy loss):

```sql
CREATE VECTOR INDEX docs_vidx ON documents(embedding_vec)
  ORGANIZATION INMEMORY NEIGHBOR GRAPH
  DISTANCE COSINE
  WITH TARGET ACCURACY 95
  PARAMETERS (type HNSW, neighbors 32, efConstruction 200, compress SCALAR);
```

### Hybrid vector index

```sql
-- Hybrid index combining Oracle Text + vector structure
CREATE VECTOR INDEX docs_hybrid_vidx ON documents(content, embedding_vec)
  ORGANIZATION NEIGHBOR PARTITIONS
  DISTANCE COSINE
  PARAMETERS (type IVF, neighbor partitions 64);

-- Query using DBMS_HYBRID_VECTOR.SEARCH for unified keyword + semantic results
SELECT *
FROM   TABLE(
         DBMS_HYBRID_VECTOR.SEARCH(
           json_object(
             'index_name'  VALUE 'DOCS_HYBRID_VIDX',
             'query'       VALUE :user_query,
             'vector'      VALUE :query_vec,
             'topN'        VALUE 10
           )
         )
       );
```

### Work-queue dequeue with SKIP LOCKED

```sql
SELECT *
FROM  (
  SELECT task_id, payload, created_at
  FROM   task_queue
  WHERE  status = 'READY'
  ORDER  BY created_at
)
WHERE  ROWNUM <= 1
FOR UPDATE SKIP LOCKED;
```

---

## Embedding Lifecycle

### Schema pattern — version embeddings

```sql
ALTER TABLE documents ADD (
  embedding_vec          VECTOR(1536, FLOAT32),
  embedding_model_version VARCHAR2(100),     -- e.g., 'cohere-embed-v3'
  embedded_at            TIMESTAMP DEFAULT SYSTIMESTAMP
);
```

When changing embedding models or chunking strategy:
1. Re-generate all vectors with the new model
2. Rebuild vector indexes
3. Do NOT assume cross-version similarity is stable — dot-product scores from model A are not comparable to model B

### Python pipeline skeleton (python-oracledb)

```python
import oracledb
import oci

def get_embedding(oci_client, text: str, model: str = "cohere.embed-english-v3.0") -> list[float]:
    # OCI Generative AI embedding — handle retries/backoff for throttling
    resp = oci_client.embed_text(
        embed_text_details=oci.generative_ai_inference.models.EmbedTextDetails(
            inputs=[text],
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(model_id=model),
            compartment_id=COMPARTMENT_ID,
        )
    )
    return resp.data.embeddings[0]

def store_doc(conn, doc_id: str, content: str, embedding: list[float], model_version: str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO documents(doc_id, content, embedding_vec, embedding_model_version, embedded_at)
            VALUES (:1, :2, :3, :4, SYSTIMESTAMP)
        """, [doc_id, content, embedding, model_version])
    conn.commit()

def retrieve(conn, query_vec: list[float], tenant_id: str, k: int = 10):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT doc_id, content,
                   VECTOR_DISTANCE(embedding_vec, :qv, COSINE) AS score
            FROM   documents
            WHERE  tenant_id = :tid
            AND    is_active = 1
            ORDER  BY score
            FETCH  FIRST :k ROWS ONLY
        """, qv=query_vec, tid=tenant_id, k=k)
        return cur.fetchall()
```

Key conventions: use `python-oracledb` (Oracle-maintained); pool connections at startup; never embed secrets in notebooks; treat OCI Generative AI limits as a design constraint (backoff + queuing).

### Node.js pooled vector retrieval

```javascript
const oracledb = require("oracledb");

async function vectorSearch(queryVector, tenantId) {
  const pool = oracledb.getPool();  // pool created at app startup
  let conn;
  try {
    conn = await pool.getConnection();
    const result = await conn.execute(
      `SELECT doc_id, title,
              VECTOR_DISTANCE(embedding_vec, :qv, COSINE) AS score
       FROM   documents
       WHERE  tenant_id = :tid
       AND    is_active = 1
       ORDER  BY score
       FETCH  FIRST 10 ROWS ONLY`,
      { qv: queryVector, tid: tenantId }
    );
    return result.rows;
  } finally {
    if (conn) await conn.close();  // return to pool
  }
}
```

---

## JSON-Relational Duality Views

Expose aggregate as a JSON document while physically storing data normalized:

```sql
CREATE JSON RELATIONAL DUALITY VIEW order_dv AS
  SELECT JSON {
    'orderId'    : o.order_id,
    'orderDate'  : o.order_date,
    'customerId' : o.customer_id,
    'status'     : o.status,
    'lines'      : [
      SELECT JSON {
        'lineNo'    : l.line_no,
        'sku'       : l.sku,
        'qty'       : l.qty,
        'unitPrice' : l.unit_price
      }
      FROM order_lines l
      WHERE l.order_id = o.order_id
    ]
  }
  FROM orders o;
```

Documents are materialized on demand (not stored as copies). Useful when AI-generated content must be returned as a document but stored relationally.

---

## OCI GenAI Integration

### Auth — prefer resource principals

```python
# Resource principal (for Compute/OKE/Functions — no embedded credentials)
signer = oci.auth.signers.get_resource_principals_signer()
genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config={}, signer=signer)

# API key config only for constrained automation/local dev
config = oci.config.from_file("~/.oci/config", "DEFAULT")
```

### Guardrails — apply at service boundary

OCI Generative AI guardrails provide three categories:
1. **Content moderation** — block harmful/offensive outputs
2. **Prompt injection defense** — detect and block instruction injection attempts
3. **PII handling** — detect/redact PII in prompts and responses

Apply guardrails before any user input reaches the model. Test guardrail effectiveness in CI (inject test prompts, assert blocks).

### Service limits and backpressure

OCI Generative AI imposes request-per-minute and token-per-minute limits (some dynamic/undocumented). Design for backpressure:

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
def call_genai_with_backoff(client, request):
    return client.chat(request)
```

---

## Security Controls

### TDE — encrypt at rest (including VECTOR columns)

```sql
-- Enable tablespace encryption (AES256 default in 26ai, AES-XTS also available)
ALTER TABLESPACE data_ts ENCRYPTION ENCRYPT USING AES256;

-- Or encrypt specific sensitive columns
ALTER TABLE documents MODIFY (embedding_vec ENCRYPT USING 'AES256');
```

### SQL Firewall — allowlisting for agent SQL paths

Especially critical when NL-to-SQL or agent tools generate queries:

```sql
-- Enable SQL Firewall capture for a schema
BEGIN
  DBMS_SQL_FIREWALL.ENABLE_CAPTURE(username => 'APP_SCHEMA');
END;
/
-- After capture period, publish allowlist
BEGIN
  DBMS_SQL_FIREWALL.PUBLISH_FIREWALL_POLICY(username => 'APP_SCHEMA');
END;
/
-- Enable enforcement (log or block unauthorized SQL)
BEGIN
  DBMS_SQL_FIREWALL.ENABLE(username => 'APP_SCHEMA');
END;
/
```

### VPD — row-level security for multi-tenant

```sql
CREATE OR REPLACE FUNCTION tenant_policy(schema_name IN VARCHAR2, table_name IN VARCHAR2)
  RETURN VARCHAR2 AS
BEGIN
  RETURN 'tenant_id = SYS_CONTEXT(''APP_CTX'', ''TENANT_ID'')';
END;
/

BEGIN
  DBMS_RLS.ADD_POLICY(
    object_schema   => 'APP_SCHEMA',
    object_name     => 'DOCUMENTS',
    policy_name     => 'TENANT_ISOLATION',
    function_schema => 'APP_SCHEMA',
    policy_function => 'TENANT_POLICY'
  );
END;
/
```

---

## Deployment & Operations

### Observability signals for LLM/RAG apps

Beyond standard microservice metrics, instrument:
- **Retrieval**: embedding latency, DB query latency, top-k similarity score distribution, "no result" events
- **Prompt**: tokens in/out, guardrail trigger rate, refusal rate
- **Cost**: inference cost per request, per tenant
- **Drift**: top-k overlap over time, similarity score distribution shifts, prompt template version deployed

Export via OpenTelemetry → OCI APM + Logging Analytics.

### CI/CD with AI gates

```
Commit → Build + Unit Tests
       → Security Scans (SAST/secrets)
       → Deploy to Staging
       → Integration Tests (DB + IAM + ORDS)
       → AI Test Suite (prompt injection, PII leakage, embedding regression)
       → Load/Perf Tests (vector index latency, inference throughput)
       → Canary/Blue-Green gate (error rate, cost/request, hallucination proxy)
       → Production
       → Continuous Monitoring (logs/traces/drift alerts)
```

### Cost controls

- Compress HNSW indexes with scalar quantization (reduced storage, minimal accuracy loss)
- Keep top-k retrieval small; use hybrid search when keyword constraints reduce candidate sets
- Cache frequent embeddings/query results
- Apply WAF rate limiting + per-tenant request quotas — "unbounded consumption" is both a security and cost risk (OWASP LLM Top 10)
- Tag resources for cost attribution: OCI Cost Analysis + cost-tracking tags per project/feature

---

## Compliance Anchors

| Framework | Relevance |
|---|---|
| **NIST AI RMF 1.0** | GOVERN / MAP / MEASURE / MANAGE functions for AI risk; GenAI profile (AI 600-1) covers GenAI-specific risks |
| **OWASP LLM Top 10 (2025)** | Prompt injection, sensitive info disclosure, unbounded consumption — directly applicable to RAG/agent apps |
| **CIS OCI Foundations Benchmark** | Prescriptive OCI secure configuration; align landing zone to CIS controls |
