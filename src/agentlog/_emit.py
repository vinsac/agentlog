"""
Output engine for agentlog.

Handles formatting log entries and routing them to sinks
(stdout via logging, JSONL file, ringbuffer).
"""

import os
import sys
import json
import time
import inspect
import logging
import threading
from typing import Any, Dict, Optional

from ._core import should_emit, get_tag_prefix


# ---------------------------------------------------------------------------
# Sequence counter
# ---------------------------------------------------------------------------

_sequence: int = 0
_seq_lock = threading.Lock()


def _next_seq() -> int:
    """Monotonically increasing sequence number for ordering."""
    global _sequence
    with _seq_lock:
        _sequence += 1
        return _sequence


# ---------------------------------------------------------------------------
# Caller location
# ---------------------------------------------------------------------------

def _caller(depth: int = 2) -> str:
    """Compact caller location: 'file.py:42 func_name'."""
    try:
        frame = inspect.stack()[depth]
        filename = os.path.basename(frame.filename)
        return f"{filename}:{frame.lineno} {frame.function}"
    except (IndexError, AttributeError):
        return "?"


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

_logger = logging.getLogger("agentlog")
_handler_installed = False


def _ensure_handler() -> None:
    """Ensure the agentlog logger has a stdout handler."""
    global _handler_installed
    if not _handler_installed:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        _logger.addHandler(handler)
        _logger.setLevel(logging.DEBUG)
        _logger.propagate = False
        _handler_installed = True


# ---------------------------------------------------------------------------
# Trace context (injected by _trace module)
# ---------------------------------------------------------------------------

_trace_id: Optional[str] = None
_span_stack: list = []


def set_trace_id(tid: Optional[str]) -> None:
    """Set the current trace ID (called by _trace module)."""
    global _trace_id
    _trace_id = tid


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    return _trace_id


def push_span(span_id: str) -> None:
    """Push a span ID onto the stack."""
    _span_stack.append(span_id)


def pop_span() -> None:
    """Pop the top span ID from the stack."""
    if _span_stack:
        _span_stack.pop()


# ---------------------------------------------------------------------------
# JSONL file sink (managed by _sink module)
# ---------------------------------------------------------------------------

_jsonl_file = None
_jsonl_lock = threading.Lock()


def set_jsonl_file(f: Any) -> None:
    """Set the JSONL file handle (called by _sink module)."""
    global _jsonl_file
    _jsonl_file = f


def get_jsonl_file() -> Any:
    """Get the current JSONL file handle."""
    return _jsonl_file


def get_jsonl_lock() -> threading.Lock:
    """Get the JSONL file lock."""
    return _jsonl_lock


# ---------------------------------------------------------------------------
# Ringbuffer callback (set by _buffer module)
# ---------------------------------------------------------------------------

_ringbuffer_add_fn = None


def set_ringbuffer_add(fn: Any) -> None:
    """Register the ringbuffer add function (called by _buffer module)."""
    global _ringbuffer_add_fn
    _ringbuffer_add_fn = fn


# ---------------------------------------------------------------------------
# Core emit function
# ---------------------------------------------------------------------------

def emit(tag: str, data: Dict[str, Any], depth: int = 3) -> None:
    """
    Write a single agentlog line to stdout and optional sinks.

    This is the central output function. All public API functions
    call this after checking should_emit().
    """
    if not should_emit(tag):
        return

    _ensure_handler()

    entry: Dict[str, Any] = {
        "seq": _next_seq(),
        "ts": time.time(),
        "at": _caller(depth),
    }

    # Inject session ID if active
    from . import _core
    if _core._session_id:
        entry["session_id"] = _core._session_id

    # Inject trace context if active
    if _trace_id:
        entry["trace"] = _trace_id
    if _span_stack:
        entry["span"] = _span_stack[-1]

    entry.update(data)

    prefix = get_tag_prefix()
    line = f"[{prefix}:{tag}] {json.dumps(entry, default=str, separators=(',', ':'))}"
    _logger.debug(line)

    # Write to JSONL file sink if configured
    if _jsonl_file is not None:
        with _jsonl_lock:
            try:
                _jsonl_file.write(json.dumps(entry, default=str, separators=(',', ':')) + '\n')
                _jsonl_file.flush()
            except Exception:
                pass

    # Add to ringbuffer for context budget export
    if _ringbuffer_add_fn is not None:
        _ringbuffer_add_fn(entry, tag)
