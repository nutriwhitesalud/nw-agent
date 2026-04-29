import { Type } from "@sinclair/typebox";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

const DEFAULT_RAG_API_URL = "http://127.0.0.1:8081";
const DEFAULT_CRM_ADAPTER_URL = "http://127.0.0.1:8082";
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);

function localHttpBaseUrl(value, fieldName) {
  const url = new URL(value);
  if (url.protocol !== "http:" || !LOOPBACK_HOSTS.has(url.hostname)) {
    throw new Error(`${fieldName} must be a loopback http URL.`);
  }
  return url.origin;
}

function pluginConfig(api) {
  const config = api.pluginConfig ?? {};
  return {
    ragApiUrl: localHttpBaseUrl(config.ragApiUrl ?? DEFAULT_RAG_API_URL, "ragApiUrl"),
    crmAdapterUrl: localHttpBaseUrl(config.crmAdapterUrl ?? DEFAULT_CRM_ADAPTER_URL, "crmAdapterUrl"),
    internalApiKey: config.internalApiKey ?? "",
  };
}

async function postJson(baseUrl, internalApiKey, path, payload) {
  if (!internalApiKey) {
    throw new Error("internalApiKey is not set for the customer-service-tools plugin.");
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

function faqAnswer(topic, answer, sourceUri) {
  return asText({
    topic,
    source_uri: sourceUri,
    answer,
    instruction:
      "Responde en español usando solo este contenido. No digas que vas a buscar. No escales si la pregunta coincide con este tema.",
  });
}

export default definePluginEntry({
  id: "customer-service-tools",
  name: "Customer Service Tools",
  description: "NutriWhite tools for knowledge retrieval and Zoho-backed patient workflows.",
  register(api) {
    const { ragApiUrl, crmAdapterUrl, internalApiKey } = pluginConfig(api);

    // ── Knowledge retrieval ──────────────────────────────────────────────────
    api.registerTool(
      {
        name: "kb_search",
        description:
          "OBLIGATORIA antes de responder preguntas generales de NutriWhite: ubicacion/sede, compras, productos/servicios, planes, precios, metodos de pago, cuotas, examenes, suplementos, Protocolo 3R, seguros o llamada gratis. " +
          "Usa resultados aprobados de la base de conocimiento y cita source_uri. Si no hay resultados relevantes, no improvises; escala con handoff_human.",
        parameters: Type.Object({
          query: Type.String({ minLength: 3 }),
          top_k: Type.Optional(Type.Integer({ minimum: 1, maximum: 10 })),
          corpus: Type.Optional(Type.String()),
          product: Type.Optional(Type.String()),
          language: Type.Optional(Type.String()),
        }),
        async execute(_id, params) {
          const result = await postJson(ragApiUrl, internalApiKey, "/v1/retrieve", {
            query: params.query,
            top_k: params.top_k ?? 5,
            corpus: params.corpus ?? "default",
            product: params.product ?? null,
            language: params.language ?? null,
          });
          return asText(result);
        },
      },
    );

    api.registerTool(
      {
        name: "faq_location",
        description:
          "Usa esta herramienta para responder de forma directa cuando pregunten donde esta NutriWhite, ubicacion, sede o direccion.",
        parameters: Type.Object({}),
        async execute() {
          return faqAnswer(
            "ubicacion",
            "NutriWhite esta en Caracas, Venezuela, en Alta Florida, Avenida Los Mangos, Centro Deportivo Caracas MultiSport, Piso 1. Tambien ofrecemos consultas online para pacientes desde cualquier lugar.",
            "knowledge/raw/01_company_overview.md",
          );
        },
      },
    );

    api.registerTool(
      {
        name: "faq_services",
        description:
          "Usa esta herramienta para responder que ofrece NutriWhite, que productos/servicios tiene, o que puede comprar un paciente.",
        parameters: Type.Object({}),
        async execute() {
          return faqAnswer(
            "servicios",
            "NutriWhite ofrece consultas de Inmunonutricion, consultas de nutricion, examenes especializados, suplementos especificos coordinados segun la ubicacion del paciente, evaluacion gratuita de salud, llamada gratuita de 15 minutos y acompanamiento con el Protocolo 3R. Para suplementos, fuera de Venezuela se trabaja con Fullscript y Wholescripts; en Venezuela coordina el equipo de logistica interna.",
            "knowledge/raw/01_company_overview.md; knowledge/raw/04_supplements.md",
          );
        },
      },
    );

    api.registerTool(
      {
        name: "faq_consultation_plans",
        description:
          "Usa esta herramienta para responder que planes de consulta hay disponibles, precios de planes, costo de planes o informacion comercial general de planes.",
        parameters: Type.Object({}),
        async execute() {
          return faqAnswer(
            "planes_consulta",
            "Planes disponibles: Plan 1 Consulta (Basico): $229 USD, duracion 1 mes, 1 consulta de 90 minutos. Plan 3 Consultas (Mas Recomendado): $559 USD, duracion 3 meses, 3 consultas/seguimientos. Plan 5 Consultas (Premium): $789 USD, duracion 5 meses, 5 consultas/seguimientos. No calcules cuotas ni comisiones; si preguntan por cuotas, indica que son solo con TDC y se agrega 3% de comision bancaria.",
            "knowledge/raw/02_consultation_plans.md",
          );
        },
      },
    );

    api.registerTool(
      {
        name: "faq_payment_methods",
        description:
          "Usa esta herramienta para metodos de pago, cuotas, TDC, comision, seguro o reembolso.",
        parameters: Type.Object({}),
        async execute() {
          return faqAnswer(
            "pagos",
            "Metodos de pago: PayPal, Zelle, Tarjeta de Credito (TDC), Efectivo y Pago movil en Venezuela. Las cuotas estan disponibles unicamente con TDC y se agrega 3% de comision bancaria. NutriWhite no trabaja directamente con seguros, pero puede emitir factura para que el paciente gestione reembolso con su corredor si su seguro cubre nutricion.",
            "knowledge/raw/02_consultation_plans.md; knowledge/raw/06_faq.md",
          );
        },
      },
    );

    // ── Patient lookup ───────────────────────────────────────────────────────
    api.registerTool(
      {
        name: "customer_lookup",
        description:
          "Buscar paciente por número de WhatsApp (preferido), email, o ID de Zoho. " +
          "El número debe coincidir con el remitente del mensaje.",
        parameters: Type.Object({
          phone: Type.Optional(Type.String({ description: "Formato E.164: +584145610594" })),
          email: Type.Optional(Type.String()),
          customer_id: Type.Optional(Type.String({ description: "Zoho Contact id" })),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/customer/profile", {
            phone: params.phone ?? null,
            email: params.email ?? null,
            customer_id: params.customer_id ?? null,
          });
          return asText(result);
        },
      },
    );

    // ── Deals / Plans (Tratos) ────────────────────────────────────────────────
    api.registerTool(
      {
        name: "customer_orders",
        description: "Listar planes activos del paciente (Tratos en Zoho).",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/customer/orders", params);
          return asText(result);
        },
      },
    );

    // ── Consultas ─────────────────────────────────────────────────────────────
    api.registerTool(
      {
        name: "customer_tickets",
        description: "Listar consultas programadas y vistas del paciente.",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/customer/tickets", params);
          return asText(result);
        },
      },
    );

    api.registerTool(
      {
        name: "customer_consultas",
        description: "Alias claro de customer_tickets — consultas del paciente.",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/customer/consultas", params);
          return asText(result);
        },
      },
    );

    // ── Exámenes ──────────────────────────────────────────────────────────────
    api.registerTool(
      {
        name: "customer_examenes",
        description: "Listar exámenes del paciente con su estatus de proceso.",
        parameters: Type.Object({
          customer_id: Type.String(),
        }),
        async execute(_id, params) {
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/customer/examenes", params);
          return asText(result);
        },
      },
    );

    // ── Note draft for human review ──────────────────────────────────────────
    api.registerTool(
      {
        name: "ticket_create_draft",
        description:
          "Crear una nota en el contacto de Zoho para revisión humana. Útil para resumir el caso antes de un handoff.",
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
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/tickets/draft", {
            ...params,
            priority: params.priority ?? "normal",
          });
          return asText(result);
        },
      },
    );

    // ── Handoff ───────────────────────────────────────────────────────────────
    api.registerTool(
      {
        name: "handoff_human",
        description:
          "Escalar la conversación a una asesora humana. Crea una nota en el contacto de Zoho con el motivo y prioridad.",
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
          const result = await postJson(crmAdapterUrl, internalApiKey, "/v1/handoff", {
            ...params,
            priority: params.priority ?? "high",
          });
          return asText(result);
        },
      },
    );
  },
});
