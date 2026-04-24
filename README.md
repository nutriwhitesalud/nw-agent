# Customer Service Agent Foundation

This repository scaffolds the first production-safe version of your company customer service agent stack around OpenClaw.

It deliberately separates responsibilities:

- `OpenClaw` handles conversations and agent orchestration on the host.
- `rag-api` handles controlled retrieval over approved company knowledge.
- `crm-adapter` handles narrow, auditable CRM access.
- `ingest-worker` turns company files into searchable chunks.
- `openclaw/plugins/customer-service-tools` exposes typed tools instead of broad shell or browser access.

## Why this layout

OpenClaw is strongest as the agent runtime, not as your entire business backend. This repo keeps company knowledge, customer state, and tool policy in separate services so you can harden, test, and audit each one independently.

## Repo layout

```text
docs/                     Architecture and setup guides
knowledge/raw/            Approved source documents for ingestion
openclaw/                 Plugin and skill scaffold for the agent
sql/                      Database bootstrap schema
src/company_agent/        Python services
tests/                    Small unit tests for core utility logic
```

## Quick start

1. Copy `.env.example` to `.env`.
2. Set a non-default `INTERNAL_API_KEY` value. This key is required by both internal APIs and the OpenClaw plugin.
3. Put approved Markdown, text, or JSON knowledge files into `knowledge/raw/`.
4. Start the local backing services:

   ```bash
   docker compose up --build postgres rag-api crm-adapter
   ```

5. Ingest knowledge:

   ```bash
   docker compose run --rm ingest-worker python -m company_agent.ingest_worker.main sync
   ```

6. Install the OpenClaw plugin from `openclaw/plugins/customer-service-tools` on the Ubuntu host where OpenClaw runs.
7. Export the same `INTERNAL_API_KEY` into the OpenClaw host environment before starting the Gateway.

## Current scope

This scaffold is intentionally conservative:

- Retrieval is hybrid-ready and uses Postgres full-text + `pgvector`.
- CRM access starts in `mock` mode for development.
- OpenClaw tools are narrow and business-specific.
- No generic shell, filesystem, browser, or web tools are assumed for customer-facing use.

## Recommended next build steps

1. Replace the mock CRM adapter with your real CRM integration.
2. Replace the shared API key with a stronger service-to-service auth model if needed.
3. Add observability with Phoenix or Langfuse.
4. Build a gold evaluation set and run Ragas before production rollout.

See [docs/architecture.md](/C:/Users/LANZ/nw-agent/docs/architecture.md) and [docs/openclaw-setup.md](/C:/Users/LANZ/nw-agent/docs/openclaw-setup.md) for the operational plan.
