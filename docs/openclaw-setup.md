# OpenClaw Setup Notes

## Deployment stance

Run OpenClaw on the Ubuntu host as the always-on gateway, but keep the business services in containers.

- OpenClaw: host install with Node 24 and `systemd`
- `rag-api`, `crm-adapter`, `ingest-worker`: Docker Compose
- PostgreSQL: local container for development, managed database on DigitalOcean for production

## OpenClaw plugin install

This repo includes a local plugin scaffold:

- [openclaw/plugins/customer-service-tools/index.js](/C:/Users/LANZ/nw-agent/openclaw/plugins/customer-service-tools/index.js)

Install it on the host where OpenClaw runs:

```bash
openclaw plugins install ./openclaw/plugins/customer-service-tools
openclaw gateway restart
```

The plugin expects these environment variables on the OpenClaw host:

```bash
export RAG_API_URL=http://<private-rag-api-host>:8081
export CRM_ADAPTER_URL=http://<private-crm-adapter-host>:8082
export INTERNAL_API_KEY=<same-value-as-backend-services>
```

## Workspace skill

This repo also includes a skill policy scaffold:

- [openclaw/skills/customer-service-policy/SKILL.md](/C:/Users/LANZ/nw-agent/openclaw/skills/customer-service-policy/SKILL.md)

Install it into the OpenClaw workspace `skills/` directory for the target agent.

## Initial OpenClaw policy

Use the smallest tool surface that still works. Start with only the custom business tools:

```json
{
  "tools": {
    "profile": "minimal",
    "allow": [
      "kb_search",
      "customer_lookup",
      "customer_orders",
      "customer_tickets",
      "ticket_create_draft",
      "handoff_human"
    ],
    "deny": [
      "group:automation",
      "group:runtime",
      "group:fs",
      "browser",
      "web_search",
      "web_fetch"
    ]
  }
}
```

## Required next hardening work

Before production traffic:

1. Restrict the APIs to private network access only.
2. Add request logging and trace ids.
3. Add business-level redaction for PII.
4. Replace the shared API key with a stronger service auth model if your threat model requires it.
5. Add human handoff routing to your real ticketing workflow.

