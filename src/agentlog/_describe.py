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

from ._redaction import redact_string, sanitize


_MAX_SCALAR_LEN = 200
_MAX_COLLECTION_PREVIEW = 5
_MAX_DICT_KEYS = 20
_MAX_REPR_LEN = 300


def redact(value: str) -> str:
    """Backward-compatible string redaction helper."""
    return redact_string(value)


def describe(value: Any, field_name: str = None) -> Dict[str, Any]:
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
        # Redact secrets before truncation
        safe_value = redact_string(value, field_name)
        
        if len(safe_value) <= _MAX_SCALAR_LEN:
            d["v"] = safe_value
        else:
            d["v"] = safe_value[:_MAX_SCALAR_LEN]
            d["truncated"] = len(safe_value)
        return d

    if isinstance(value, bytes):
        d["n"] = len(value)
        d["v"] = redact_string(repr(value[:50]), field_name)
        return d

    if isinstance(value, (list, tuple)):
        d["n"] = len(value)
        if len(value) > 0:
            d["it"] = type(value[0]).__name__
        if len(value) <= _MAX_COLLECTION_PREVIEW:
            try:
                d["v"] = sanitize(json.loads(json.dumps(value, default=str)), field_name)
            except (TypeError, ValueError):
                d["v"] = redact_string(_safe_repr(value), field_name)
        elif len(value) > 0:
            try:
                d["preview"] = sanitize(
                    json.loads(json.dumps(value[:3], default=str)),
                    field_name,
                )
            except (TypeError, ValueError):
                d["preview"] = redact_string(_safe_repr(value[:3]), field_name)
        return d

    if isinstance(value, dict):
        d["n"] = len(value)
        d["k"] = list(value.keys())[:_MAX_DICT_KEYS]
        if len(value) <= _MAX_COLLECTION_PREVIEW:
            try:
                d["v"] = sanitize(json.loads(json.dumps(value, default=str)))
            except (TypeError, ValueError):
                d["v"] = redact_string(_safe_repr(value), field_name)
        return d

    if isinstance(value, set):
        d["n"] = len(value)
        if len(value) <= 10:
            d["v"] = redact_string(_safe_repr(value), field_name)
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

    d["v"] = redact_string(_safe_repr(value), field_name)
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
