import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

const ragApiUrl = process.env.RAG_API_URL || "http://127.0.0.1:8081";
const crmAdapterUrl = process.env.CRM_ADAPTER_URL || "http://127.0.0.1:8082";
const internalApiKey = process.env.INTERNAL_API_KEY || "";

async function postJson(baseUrl, path, payload) {
  if (!internalApiKey) {
    throw new Error("INTERNAL_API_KEY is not set for the customer-service-tools plugin.");
  }

  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-internal-api-key": internalApiKey,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (${response.status}): ${body}`);
  }

  return response.json();
}

function asText(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2),
      },
    ],
  };
}

export default definePluginEntry({
  id: "customer-service-tools",
  name: "Customer Service Tools",
  description: "Typed tools for knowledge retrieval and CRM-backed support workflows.",
  register(api) {
    api.registerTool(
      {
        name: "kb_search",
        description: "Retrieve approved company knowledge with citations.",
        parameters: Type.Object({
          query: Type.String({ minLength: 3 }),
          top_k: Type.Optional(Type.Integer({ minimum: 1, maximum: 10 })),
          corpus: Type.Optional(Type.String()),
          product: Type.Optional(Type.String()),
          language: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const result = await postJson(ragApiUrl, "/v1/retrieve", {
            query: params.query,
            top_k: params.top_k ?? 5,
            corpus: params.corpus ?? "default",
            product: params.product ?? null,
            language: params.language ?? null,
          });
          return asText(result);
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "customer_lookup",
        description: "Look up a customer profile by id or email.",
        parameters: Type.Object({
          customer_id: Type.Optional(Type.String()),
          email: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, "/v1/customer/profile", {
            customer_id: params.customer_id ?? null,
            email: params.email ?? null,
          });
          return asText(result);
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "customer_orders",
        description: "Retrieve recent orders for a known customer.",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, "/v1/customer/orders", params);
          return asText(result);
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "customer_tickets",
        description: "Retrieve recent support tickets for a known customer.",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, "/v1/customer/tickets", params);
          return asText(result);
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "ticket_create_draft",
        description: "Create a support ticket draft for later human review or submission.",
        parameters: Type.Object({
          customer_id: Type.String(),
          summary: Type.String({ minLength: 5 }),
          details: Type.String({ minLength: 10 }),
          priority: Type.Optional(
            Type.Union([
              Type.Literal("low"),
              Type.Literal("normal"),
              Type.Literal("high"),
              Type.Literal("urgent"),
            ]),
          ),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, "/v1/tickets/draft", {
            ...params,
            priority: params.priority ?? "normal",
          });
          return asText(result);
        },
      },
      { optional: true },
    );

    api.registerTool(
      {
        name: "handoff_human",
        description: "Queue a conversation for human support handoff.",
        parameters: Type.Object({
          conversation_id: Type.String(),
          reason: Type.String({ minLength: 10 }),
          customer_id: Type.Optional(Type.String()),
          priority: Type.Optional(
            Type.Union([
              Type.Literal("low"),
              Type.Literal("normal"),
              Type.Literal("high"),
              Type.Literal("urgent"),
            ]),
          ),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, "/v1/handoff", {
            ...params,
            priority: params.priority ?? "high",
          });
          return asText(result);
        },
      },
      { optional: true },
    );
  },
});
