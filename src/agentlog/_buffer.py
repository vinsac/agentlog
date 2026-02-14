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
from ._tokens import fit_entries_to_budget
from ._priority import smart_filter as _smart_filter


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

    # Use improved token estimation to fit within budget
    selected_entries = fit_entries_to_budget(entries, max_tokens)
    
    # Convert to JSONL format
    lines = [json.dumps(e, default=str, separators=(',', ':')) for e in selected_entries]
    return '\n'.join(lines)


def get_context_smart(
    max_tokens: int = 4000,
    importance: str = "medium",
    tags: Optional[List[str]] = None,
) -> str:
    """
    Smart context export with importance filtering and compression.
    
    Phase 2 enhancement: Filters by importance before fitting to token budget.
    
    Args:
        max_tokens: Token budget
        importance: "low", "medium", "high", or "critical"
        tags: Optional tag filter (applied after importance filter)
    
    Returns:
        JSONL string of filtered entries
        
    Example:
        # Get only high-priority entries within budget
        context = get_context_smart(max_tokens=2000, importance="high")
        
        # Get critical errors and decisions
        context = get_context_smart(
            max_tokens=1000, 
            importance="critical",
            tags=["error", "decision"]
        )
    """
    with _ringbuffer_lock:
        entries = list(_ringbuffer)
    
    # Apply tag filter first if specified
    if tags:
        entries = [e for e in entries if e.get("tag") in tags]
    
    # Use smart filtering (importance + compression + token budget)
    filtered = _smart_filter(entries, max_tokens, importance)
    
    # Convert to JSONL
    lines = [json.dumps(e, default=str, separators=(',', ':')) for e in filtered]
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


def token_summary() -> Dict[str, Any]:
    """
    Aggregate token usage from LLM calls in the current buffer.
    
    Returns:
        Dict with total tokens and breakdown by model.
    """
    with _ringbuffer_lock:
        entries = list(_ringbuffer)
    
    total_in = 0
    total_out = 0
    by_model: Dict[str, Dict[str, int]] = {}
    
    for e in entries:
        if e.get("tag") == "llm":
            t_in = e.get("tokens_in", 0)
            t_out = e.get("tokens_out", 0)
            model = e.get("model", "unknown")
            
            total_in += t_in
            total_out += t_out
            
            if model not in by_model:
                by_model[model] = {"in": 0, "out": 0}
            
            by_model[model]["in"] += t_in
            by_model[model]["out"] += t_out
            
    return {
        "total_in": total_in,
        "total_out": total_out,
        "total": total_in + total_out,
        "by_model": by_model,
    }
