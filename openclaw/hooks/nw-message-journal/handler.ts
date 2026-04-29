import { appendFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const DEFAULT_JOURNAL_PATH = "/root/nw-agent/runtime/openclaw-message-journal.jsonl";

function normalizePhone(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const digits = value.replace(/[^\d]/g, "");
  return digits ? `+${digits}` : null;
}

function compactMetadata(metadata: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!metadata || typeof metadata !== "object") {
    return {};
  }

  const keys = [
    "id",
    "messageId",
    "senderId",
    "senderName",
    "participant",
    "chatId",
    "jid",
    "remoteJid",
    "messageTimestamp",
    "timestamp",
    "pushName",
  ];
  const result: Record<string, unknown> = {};
  for (const key of keys) {
    if (metadata[key] !== undefined) {
      result[key] = metadata[key];
    }
  }
  return result;
}

function appendJournal(record: Record<string, unknown>) {
  const journalPath = process.env.NW_MESSAGE_JOURNAL_PATH || DEFAULT_JOURNAL_PATH;
  mkdirSync(dirname(journalPath), { recursive: true });
  appendFileSync(journalPath, `${JSON.stringify(record)}\n`, { encoding: "utf8" });
}

export default async function handler(event: any) {
  try {
    if (event?.type !== "message") {
      return;
    }

    const action = event.action;
    if (action !== "received" && action !== "sent") {
      return;
    }

    const context = event.context || {};
    const channelId = context.channelId || context.channel || null;
    if (channelId && String(channelId).toLowerCase() !== "whatsapp") {
      return;
    }

    const metadata = compactMetadata(context.metadata);
    const from = normalizePhone(context.from ?? metadata.senderId ?? metadata.participant);
    const to = normalizePhone(context.to ?? context.target);
    const peer = action === "received" ? from : to;

    appendJournal({
      type: action,
      received_at: new Date().toISOString(),
      event_timestamp: event.timestamp || null,
      session_key: event.sessionKey || null,
      channel_id: channelId || "whatsapp",
      peer,
      from,
      to,
      success: context.success ?? null,
      content: typeof context.content === "string" ? context.content : "",
      metadata,
    });
  } catch (error) {
    console.error("[nw-message-journal] failed", error);
  }
}
