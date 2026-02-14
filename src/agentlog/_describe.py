"""
Value descriptor engine — the core of AI-first logging.

AI agents need to understand WHAT a variable is, not just its repr.
For each value we emit a compact descriptor with short keys to
minimize token usage in LLM context windows:

    t  = type name
    v  = value (for scalars) or preview
    n  = length/count (for collections)
    k  = keys (for dicts)
    sh = shape (for numpy/torch/pandas)
    dt = dtype (for numpy/torch)
    it = item type (for homogeneous collections)
    range = min/max (for numeric arrays)
    preview = first items of large collections
    truncated = original length if string was cut
"""

import json
from typing import Any, Dict


_MAX_SCALAR_LEN = 200
_MAX_COLLECTION_PREVIEW = 5
_MAX_DICT_KEYS = 20
_MAX_REPR_LEN = 300


def describe(value: Any) -> Dict[str, Any]:
    """Describe a value for AI agent consumption. Compact keys, rich metadata."""
    t = type(value).__name__
    d: Dict[str, Any] = {"t": t}

    if value is None:
        d["v"] = None
        return d

    if isinstance(value, bool):
        d["v"] = value
        return d

    if isinstance(value, (int, float)):
        d["v"] = value
        return d

    if isinstance(value, str):
        if len(value) <= _MAX_SCALAR_LEN:
            d["v"] = value
        else:
            d["v"] = value[:_MAX_SCALAR_LEN]
            d["truncated"] = len(value)
        return d

    if isinstance(value, bytes):
        d["n"] = len(value)
        d["v"] = repr(value[:50])
        return d

    if isinstance(value, (list, tuple)):
        d["n"] = len(value)
        if len(value) > 0:
            d["it"] = type(value[0]).__name__
        if len(value) <= _MAX_COLLECTION_PREVIEW:
            try:
                d["v"] = json.loads(json.dumps(value, default=str))
            except (TypeError, ValueError):
                d["v"] = _safe_repr(value)
        elif len(value) > 0:
            try:
                d["preview"] = json.loads(json.dumps(value[:3], default=str))
            except (TypeError, ValueError):
                d["preview"] = _safe_repr(value[:3])
        return d

    if isinstance(value, dict):
        d["n"] = len(value)
        d["k"] = list(value.keys())[:_MAX_DICT_KEYS]
        if len(value) <= _MAX_COLLECTION_PREVIEW:
            try:
                d["v"] = json.loads(json.dumps(value, default=str))
            except (TypeError, ValueError):
                d["v"] = _safe_repr(value)
        return d

    if isinstance(value, set):
        d["n"] = len(value)
        if len(value) <= 10:
            d["v"] = _safe_repr(value)
        return d

    # numpy / torch / pandas — shape-aware
    if hasattr(value, "shape"):
        d["sh"] = str(value.shape)
        if hasattr(value, "dtype"):
            d["dt"] = str(value.dtype)
        if hasattr(value, "min") and hasattr(value, "max"):
            try:
                d["range"] = [float(value.min()), float(value.max())]
            except Exception:
                pass
        return d

    # pandas DataFrame
    if hasattr(value, "columns") and hasattr(value, "shape"):
        d["sh"] = str(value.shape)
        d["cols"] = list(value.columns)[:20]
        return d

    # Generic objects with __dict__
    if hasattr(value, "__dict__"):
        attrs = {k: v for k, v in value.__dict__.items() if not k.startswith("_")}
        d["k"] = list(attrs.keys())[:_MAX_DICT_KEYS]
        d["n"] = len(attrs)
        return d

    # Fallback
    if hasattr(value, "__len__"):
        try:
            d["n"] = len(value)
        except Exception:
            pass

    d["v"] = _safe_repr(value)
    return d


def _safe_repr(value: Any) -> str:
    """Safe repr with truncation."""
    try:
        r = repr(value)
        if len(r) > _MAX_REPR_LEN:
            return r[:_MAX_REPR_LEN] + f"...[{len(r)} chars]"
        return r
    except Exception:
        return f"<{type(value).__name__}>"
