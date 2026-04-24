# Architecture

## Production model

The customer service agent should run as a narrow orchestration layer over two internal systems:

- `rag-api` for company knowledge retrieval
- `crm-adapter` for customer-specific state and support workflow actions

OpenClaw should never be the direct owner of:

- raw company documents
- direct database access
- unrestricted CRM credentials
- broad shell or browser authority in customer-facing flows

## System boundaries

### 1. OpenClaw on the Ubuntu host

Responsibilities:

- receive customer messages
- choose when to use tools
- compose the final answer
- enforce policy through tools + skills

Do not expose general runtime or filesystem tools to the customer-facing agent.

### 2. `rag-api`

Responsibilities:

- retrieve approved chunks from curated company content
- return citations and metadata
- apply query filters like product, language, or corpus

This service should not generate the final answer. Retrieval stays deterministic and auditable.

### 3. `crm-adapter`

Responsibilities:

- look up customer profile
- read recent orders and open tickets
- create support case drafts
- request human handoff

This should be your only CRM integration surface. Start read-only in production if needed.

### 4. `ingest-worker`

Responsibilities:

- load approved source documents
- chunk them consistently
- generate embeddings
- upsert documents and chunks into Postgres

## Data model

### `knowledge_documents`

One row per approved source document.

### `knowledge_chunks`

One row per searchable chunk with:

- chunk text
- metadata
- full-text index
- vector embedding

## Retrieval strategy

The default strategy in this scaffold is reciprocal-rank fusion over:

- lexical retrieval via Postgres full-text search
- semantic retrieval via `pgvector`

That gives you a strong baseline without introducing a separate vector database on day one.

## Production hardening targets

1. Keep all services inside a private VPC.
2. Only expose `80/443` publicly through a reverse proxy.
3. Require service-to-service authentication before production traffic.
4. Trace every request, retrieval, and tool call.
5. Add evaluation gates before autonomous customer replies.

