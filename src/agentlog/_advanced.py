"""
Advanced observability functions.

Provides: log_decision, log_flow, log_diff, log_query, log_perf
"""

import os
import sys
import threading
from typing import Any, Dict, Optional

from ._core import is_enabled
from ._describe import describe
from ._emit import emit


def log_decision(question: str, answer: Any, reason: str = "", **kwargs: Any) -> None:
    """
    Log a branching decision so AI agents understand control flow.

    Example:
        log_decision(
            "Should merge with existing skill?",
            confidence >= 0.9,
            reason=f"confidence {confidence} >= threshold 0.9",
            confidence=confidence, threshold=0.9
        )
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {
        "question": question,
        "answer": describe(answer),
    }
    if reason:
        data["reason"] = reason
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("decision", data)


def log_flow(pipeline: str, step: str, value: Any, **kwargs: Any) -> None:
    """
    Log a data transformation step in a named pipeline.

    Example:
        log_flow("skill_creation", "raw_input", raw_name)
        log_flow("skill_creation", "normalized", normalized, confidence=0.95)
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {
        "pipeline": pipeline,
        "step": step,
        "value": describe(value),
    }
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("flow", data)


def log_diff(label: str, before: Any, after: Any) -> None:
    """
    Log the difference between two states. Works with dicts and objects.

    Example:
        log_diff("user_profile", old_profile.__dict__, new_profile.__dict__)
        log_diff("config", old_config, new_config)
    """
    if not is_enabled():
        return

    def _to_dict(obj: Any) -> dict:
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        return {"value": obj}

    b = _to_dict(before)
    a = _to_dict(after)
    all_keys = set(list(b.keys()) + list(a.keys()))

    added = {k: describe(a[k]) for k in all_keys if k not in b}
    removed = {k: describe(b[k]) for k in all_keys if k not in a}
    changed = {}
    for k in all_keys:
        if k in b and k in a:
            try:
                if b[k] != a[k]:
                    changed[k] = {"from": describe(b[k]), "to": describe(a[k])}
            except Exception:
                changed[k] = {"from": describe(b[k]), "to": describe(a[k])}

    if not added and not removed and not changed:
        return  # no diff, no log

    data: Dict[str, Any] = {"label": label}
    if added:
        data["added"] = added
    if removed:
        data["removed"] = removed
    if changed:
        data["changed"] = changed
    emit("diff", data)


def log_query(
    operation: str,
    target: str,
    duration_ms: Optional[float] = None,
    rows: Optional[int] = None,
    **kwargs: Any,
) -> None:
    """
    Log a database query or external data operation.

    Example:
        log_query("SELECT", "skills", 12.3, rows=42, where="category='ml'")
        log_query("vector_search", "embeddings", 89.5, rows=10, k=10)
        log_query("cache_get", "redis:skills", 0.5, hit=True, key=cache_key)
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {"op": operation, "target": target}
    if duration_ms is not None:
        data["ms"] = round(duration_ms, 1)
    if rows is not None:
        data["rows"] = rows
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("query", data)


def log_perf(label: str = "", **kwargs: Any) -> None:
    """
    Log a performance/memory snapshot of the current process.

    Example:
        log_perf("before_embedding_batch")
        embeddings = compute_embeddings(batch)
        log_perf("after_embedding_batch", batch_size=len(batch))
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {}
    if label:
        data["label"] = label

    # Memory usage (RSS in MB)
    try:
        import resource as _resource_mod
        usage = _resource_mod.getrusage(_resource_mod.RUSAGE_SELF)
        rss_kb = usage.ru_maxrss
        if sys.platform == "darwin":
            rss_kb = rss_kb // 1024
        data["rss_mb"] = round(rss_kb / 1024, 1)
    except Exception:
        pass

    # Thread count
    try:
        data["threads"] = threading.active_count()
    except Exception:
        pass

    # PID
    data["pid"] = os.getpid()

    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("perf", data)
