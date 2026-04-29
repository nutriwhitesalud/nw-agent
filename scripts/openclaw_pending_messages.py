from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_JOURNAL = Path("/root/nw-agent/runtime/openclaw-message-journal.jsonl")


@dataclass(slots=True)
class JournalRecord:
    type: str
    received_at: datetime
    peer: str
    content: str
    raw: dict[str, Any]


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def load_records(path: Path, since: datetime) -> list[JournalRecord]:
    if not path.exists():
        return []

    records: list[JournalRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip().lstrip("\ufeff")
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue

            received_at = parse_timestamp(payload.get("received_at"))
            if received_at is None or received_at < since:
                continue

            peer = payload.get("peer")
            if not isinstance(peer, str) or not peer:
                continue

            records.append(
                JournalRecord(
                    type=str(payload.get("type") or ""),
                    received_at=received_at,
                    peer=peer,
                    content=str(payload.get("content") or ""),
                    raw=payload,
                )
            )
    return records


def pending_by_peer(records: list[JournalRecord]) -> list[JournalRecord]:
    last_sent: dict[str, datetime] = {}
    inbound: list[JournalRecord] = []

    for record in sorted(records, key=lambda item: item.received_at):
        if record.type == "sent":
            last_sent[record.peer] = record.received_at
        elif record.type == "received":
            inbound.append(record)

    pending: list[JournalRecord] = []
    for record in inbound:
        if last_sent.get(record.peer, datetime.min.replace(tzinfo=UTC)) < record.received_at:
            pending.append(record)
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report WhatsApp inbound messages captured by OpenClaw with no later outbound reply."
    )
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument("--minutes", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-pending", action="store_true")
    args = parser.parse_args()

    now = datetime.now(UTC)
    since = now - timedelta(minutes=args.minutes)
    records = load_records(args.journal, since)
    pending = pending_by_peer(records)

    if args.json:
        print(
            json.dumps(
                {
                    "journal": str(args.journal),
                    "window_minutes": args.minutes,
                    "pending_count": len(pending),
                    "pending": [
                        {
                            "received_at": item.received_at.isoformat(),
                            "peer": item.peer,
                            "content": item.content,
                            "session_key": item.raw.get("session_key"),
                            "metadata": item.raw.get("metadata"),
                        }
                        for item in pending
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif pending:
        print(f"Pending WhatsApp messages in last {args.minutes} minutes:")
        for item in pending:
            print(f"- {item.received_at.isoformat()} {item.peer}: {item.content}")
    else:
        print(f"No pending WhatsApp messages in last {args.minutes} minutes.")

    return 2 if pending and args.fail_on_pending else 0


if __name__ == "__main__":
    sys.exit(main())
