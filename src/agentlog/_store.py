"""
Durable incident storage for agent handoff.

The ring buffer is ideal for in-process context assembly. This module provides
a small JSONL-backed store for incidents that need to survive process exit.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ._context import assemble_debug_context_with_metadata
from ._redaction import sanitize_event


DEFAULT_STORE_PATH = ".agentlog/incidents.jsonl"
BUNDLE_SCHEMA_VERSION = "agentlog.debug_bundle.v1"

_store_path: Optional[str] = None
_store_max_bytes: Optional[int] = None
_store_lock = threading.Lock()


class JsonlIncidentStore:
    """Append-only JSONL incident store."""

    def __init__(self, path: str = DEFAULT_STORE_PATH, *, max_bytes: Optional[int] = None):
        self.path = path
        self.max_bytes = max_bytes

    def append(self, entry: Dict[str, Any]) -> None:
        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(sanitize_event(entry), default=str, separators=(",", ":")) + "\n"
        self._rotate_if_needed(len(line.encode("utf-8")))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line)

    def _rotate_if_needed(self, next_bytes: int) -> None:
        if not self.max_bytes or self.max_bytes <= 0:
            return
        path = Path(self.path)
        if not path.exists():
            return
        if path.stat().st_size + next_bytes <= self.max_bytes:
            return
        rotated = path.with_name(path.name + ".1")
        try:
            if rotated.exists():
                rotated.unlink()
            path.replace(rotated)
        except OSError:
            pass

    def read_entries(
        self,
        *,
        incident_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not os.path.exists(self.path):
            return entries

        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if incident_id and not _entry_has_value(entry, "incident_id", incident_id):
                    continue
                if session_id and entry.get("session_id") != session_id:
                    continue
                entries.append(entry)

        if limit is not None:
            entries = entries[-limit:]
        return entries

    def list_incidents(self, *, limit: int = 50) -> List[Dict[str, Any]]:
        incidents: Dict[str, Dict[str, Any]] = {}
        for entry in self.read_entries():
            incident_id = _extract_value(entry, "incident_id")
            if not incident_id:
                continue
            record = incidents.setdefault(
                str(incident_id),
                {
                    "incident_id": str(incident_id),
                    "events": 0,
                    "first_ts": entry.get("ts"),
                    "last_ts": entry.get("ts"),
                    "session_id": entry.get("session_id"),
                    "tags": {},
                    "last_error": None,
                },
            )
            record["events"] += 1
            record["last_ts"] = entry.get("ts", record["last_ts"])
            record["session_id"] = entry.get("session_id") or record["session_id"]
            tag = str(entry.get("tag", "info"))
            record["tags"][tag] = record["tags"].get(tag, 0) + 1
            if tag == "error":
                record["last_error"] = entry.get("err_msg") or entry.get("msg")

        return sorted(
            incidents.values(),
            key=lambda item: (item.get("last_ts") is not None, item.get("last_ts") or 0),
            reverse=True,
        )[:limit]


def configure_incident_store(path: str = DEFAULT_STORE_PATH, *, max_bytes: Optional[int] = None) -> str:
    """Enable durable incident storage and return the active path."""
    global _store_path, _store_max_bytes
    _store_path = path
    _store_max_bytes = max_bytes
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def disable_incident_store() -> None:
    """Disable automatic durable incident storage."""
    global _store_path, _store_max_bytes
    _store_path = None
    _store_max_bytes = None


def get_incident_store_path() -> Optional[str]:
    """Return the active durable incident-store path, if configured."""
    return _store_path


def get_incident_store_max_bytes() -> Optional[int]:
    """Return the active incident-store rotation size, if configured."""
    return _store_max_bytes


def persist_entry(entry: Dict[str, Any]) -> None:
    """Persist an emitted entry when durable storage is enabled."""
    if not _store_path:
        return
    with _store_lock:
        try:
            JsonlIncidentStore(_store_path, max_bytes=_store_max_bytes).append(entry)
        except Exception:
            pass


def list_incidents(path: Optional[str] = None, *, limit: int = 50) -> List[Dict[str, Any]]:
    """List incident summaries from a JSONL incident store."""
    return JsonlIncidentStore(path or _store_path or DEFAULT_STORE_PATH).list_incidents(limit=limit)


def load_incident_entries(
    incident_id: Optional[str] = None,
    *,
    session_id: Optional[str] = None,
    path: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load stored entries for an incident or session."""
    return JsonlIncidentStore(path or _store_path or DEFAULT_STORE_PATH).read_entries(
        incident_id=incident_id,
        session_id=session_id,
        limit=limit,
    )


def export_debug_bundle(
    *,
    incident_id: Optional[str] = None,
    session_id: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None,
    token_budget: int = 4000,
    path: Optional[str] = None,
    format: str = "text",
    include_metadata: bool = True,
    explain: bool = True,
) -> str:
    """Export a versioned debug bundle from stored incident entries."""
    entries = load_incident_entries(incident_id, session_id=session_id, path=path)
    assembled = assemble_debug_context_with_metadata(
        entries,
        max_tokens=token_budget,
        session_id=session_id,
        incident_id=incident_id,
        scope=scope,
        include_metadata=include_metadata,
        explain=explain,
    )
    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "incident_id": incident_id,
        "session_id": session_id,
        "token_budget": token_budget,
        "event_count": len(entries),
        "filtered_count": assembled["filtered_count"],
        "selected_count": assembled["selected_count"],
        "dropped_count": assembled["dropped_count"],
        "filters": assembled["filters"],
        "selection": assembled["selection"],
        "context": assembled["context"],
    }

    if format == "json":
        return json.dumps(bundle, indent=2, default=str)
    if format == "markdown":
        title = incident_id or session_id or "debug context"
        return (
            f"# agentlog Debug Bundle\n\n"
            f"- schema: `{BUNDLE_SCHEMA_VERSION}`\n"
            f"- scope: `{title}`\n"
            f"- events: `{len(entries)}`\n"
            f"- selected: `{assembled['selected_count']}`\n"
            f"- dropped: `{assembled['dropped_count']}`\n"
            f"- token budget: `{token_budget}`\n\n"
            "```jsonl\n"
            f"{assembled['context']}\n"
            "```\n"
        )
    return assembled["context"]


def _entry_has_value(entry: Dict[str, Any], key: str, value: Any) -> bool:
    extracted = _extract_value(entry, key)
    return extracted == value


def _extract_value(entry: Dict[str, Any], key: str) -> Any:
    if key in entry:
        return entry[key]
    ctx = entry.get("ctx")
    if isinstance(ctx, dict):
        descriptor = ctx.get(key)
        if isinstance(descriptor, dict):
            return descriptor.get("v")
        return descriptor
    return None
