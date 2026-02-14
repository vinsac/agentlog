"""
Token-aware ringbuffer for context budget management.

AI agents have limited context windows. When debugging, they need the
MOST RELEVANT recent logs, not all logs. The ringbuffer keeps the last N
entries and can export a token-budgeted summary.
"""

import json
import threading
from collections import deque
from typing import Any, Dict, List, Optional

from . import _emit


# ---------------------------------------------------------------------------
# Ringbuffer
# ---------------------------------------------------------------------------

_ringbuffer: deque = deque(maxlen=500)
_ringbuffer_lock = threading.Lock()


def _ringbuffer_add(entry: Dict[str, Any], tag: str) -> None:
    """Add an entry to the ringbuffer."""
    with _ringbuffer_lock:
        _ringbuffer.append({"tag": tag, **entry})


# Register with the emit module
_emit.set_ringbuffer_add(_ringbuffer_add)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def set_buffer_size(max_entries: int) -> None:
    """Set the ringbuffer size (default 500)."""
    global _ringbuffer
    with _ringbuffer_lock:
        old = list(_ringbuffer)
        _ringbuffer = deque(old[-max_entries:], maxlen=max_entries)


def get_context(
    max_tokens: int = 4000,
    tags: Optional[List[str]] = None,
    last_n: Optional[int] = None,
) -> str:
    """
    Export recent log entries as a string sized for an AI agent's context.

    Args:
        max_tokens: Approximate token budget (1 token ~ 4 chars).
        tags: Filter to specific tags (e.g., ["error", "check", "decision"]).
        last_n: Only return the last N entries.

    Returns:
        A string of JSONL lines that fits within the token budget.

    Example:
        context = get_context(max_tokens=4000, tags=["error", "check", "decision"])
        context = get_context(last_n=20)
    """
    with _ringbuffer_lock:
        entries = list(_ringbuffer)

    if tags:
        entries = [e for e in entries if e.get("tag") in tags]
    if last_n:
        entries = entries[-last_n:]

    # Build output within token budget (1 token ~ 4 chars)
    max_chars = max_tokens * 4
    lines: List[str] = []
    total_chars = 0

    # Work backwards from most recent (most relevant)
    for entry in reversed(entries):
        line = json.dumps(entry, default=str, separators=(',', ':'))
        if total_chars + len(line) + 1 > max_chars:
            break
        lines.append(line)
        total_chars += len(line) + 1

    lines.reverse()  # restore chronological order
    return '\n'.join(lines)


def summary() -> Dict[str, Any]:
    """
    Generate a compact summary of the current session.
    Useful for AI agents to get a quick overview without reading all logs.

    Returns:
        Dict with counts by tag, error messages, failed checks, and timing.

    Example:
        s = summary()
        # {"total": 142, "by_tag": {"info": 80, "func": 40, "error": 2},
        #  "errors": ["Failed: ValueError(...)"],
        #  "failed_checks": ["Expected non-empty results"],
        #  "slowest_funcs": [{"fn": "create_skill", "ms": 245.3}],
        #  "traces": ["a1b2c3d4e5f6"]}
    """
    with _ringbuffer_lock:
        entries = list(_ringbuffer)

    by_tag: Dict[str, int] = {}
    errors: List[str] = []
    failed_checks: List[str] = []
    slow_funcs: List[Dict[str, Any]] = []
    traces: set = set()

    for e in entries:
        tag = e.get("tag", "?")
        by_tag[tag] = by_tag.get(tag, 0) + 1

        if tag == "error":
            msg = e.get("msg", "")
            err = e.get("err", "")
            err_msg = e.get("err_msg", "")
            errors.append(f"{msg}: {err}({err_msg})" if err else msg)

        if tag == "check" and not e.get("passed", True):
            failed_checks.append(e.get("msg", ""))

        if tag == "func" and e.get("ev") == "exit" and "ms" in e:
            slow_funcs.append({"fn": e.get("fn", "?"), "ms": e["ms"]})

        if "trace" in e:
            traces.add(e["trace"])

    slow_funcs.sort(key=lambda x: x["ms"], reverse=True)

    return {
        "total": len(entries),
        "by_tag": by_tag,
        "errors": errors[-10:],
        "failed_checks": failed_checks[-10:],
        "slowest_funcs": slow_funcs[:5],
        "traces": list(traces),
    }
