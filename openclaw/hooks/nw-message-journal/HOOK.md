---
name: nw-message-journal
description: "Journal NutriWhite WhatsApp inbound/outbound events for missed-reply monitoring."
metadata:
  {
    "openclaw": {
      "emoji": "🧾",
      "events": ["message:received", "message:sent"],
      "requires": { "bins": ["node"] },
      "always": true
    }
  }
---

# NutriWhite Message Journal

Records OpenClaw message receive/send events to a JSONL file so an external
watchdog can detect WhatsApp messages that were captured by the gateway but did
not receive a later outbound reply.

Default journal path:

`/root/nw-agent/runtime/openclaw-message-journal.jsonl`

Override with:

`NW_MESSAGE_JOURNAL_PATH=/path/to/journal.jsonl`

This hook does not send customer-facing fallback messages.
