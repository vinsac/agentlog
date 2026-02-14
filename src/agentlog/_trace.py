"""
Distributed trace context propagation.

Correlation IDs for tracing requests across microservices.
AI agents debugging distributed systems need to correlate logs
from different services that handled the same request.
"""

import uuid
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from ._core import is_enabled
from ._describe import describe
from ._emit import emit, set_trace_id, get_current_trace_id, push_span, pop_span


def trace(trace_id: Optional[str] = None) -> str:
    """
    Set or generate a trace ID for correlating logs across services.
    Returns the active trace ID.

    Example:
        tid = trace()  # generates a new trace ID
        resp = httpx.post(url, headers={"X-Trace-Id": tid})

        # In downstream service
        trace(request.headers.get("X-Trace-Id"))
    """
    tid = trace_id or uuid.uuid4().hex[:16]
    set_trace_id(tid)
    if is_enabled():
        emit("trace", {"msg": "trace_start", "trace": tid}, depth=3)
    return tid


def trace_end() -> None:
    """End the current trace."""
    tid = get_current_trace_id()
    if is_enabled() and tid:
        emit("trace", {"msg": "trace_end", "trace": tid}, depth=3)
    set_trace_id(None)


def get_trace_id() -> Optional[str]:
    """Get the current trace ID for propagation to downstream services."""
    return get_current_trace_id()


@contextmanager
def span(name: str, **kwargs: Any):
    """
    Context manager for creating a named span within a trace.
    Spans nest automatically and log entry/exit with duration.

    Example:
        with span("normalize_skill", input=raw_name):
            normalized = await normalize(raw_name)
            with span("fetch_embeddings"):
                embeddings = await get_embeddings(normalized)
    """
    span_id = uuid.uuid4().hex[:12]
    push_span(span_id)
    t0 = time.monotonic()
    if is_enabled():
        data: Dict[str, Any] = {"span_name": name, "ev": "start"}
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        emit("span", data, depth=4)
    try:
        yield span_id
    except Exception as e:
        if is_enabled():
            elapsed = round((time.monotonic() - t0) * 1000, 1)
            emit("span", {
                "span_name": name, "ev": "error",
                "err": type(e).__name__, "err_msg": str(e), "ms": elapsed,
            }, depth=4)
        pop_span()
        raise
    elapsed = round((time.monotonic() - t0) * 1000, 1)
    if is_enabled():
        emit("span", {"span_name": name, "ev": "end", "ms": elapsed}, depth=4)
    pop_span()
