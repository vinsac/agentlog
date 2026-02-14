"""
OpenTelemetry bridge for agentlog.

Export logs to OpenTelemetry format for integration with existing observability stacks.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# OTEL Attribute Mapping
# ---------------------------------------------------------------------------

def _convert_to_otel_attributes(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Convert agentlog entry to OTEL attribute format."""
    attrs = {}
    
    tag = entry.get("tag", "unknown")
    attrs["agentlog.tag"] = tag
    
    # Map common fields
    if "seq" in entry:
        attrs["agentlog.seq"] = entry["seq"]
    if "ts" in entry:
        attrs["agentlog.timestamp"] = entry["ts"]
    if "at" in entry:
        attrs["code.function"] = entry["at"]
    
    # Map tag-specific fields
    if tag == "error":
        if "error" in entry:
            err = entry["error"]
            attrs["error.type"] = err.get("type", "unknown")
            attrs["error.message"] = err.get("msg", "")
        if "fn" in entry:
            attrs["code.function"] = entry["fn"]
    
    elif tag == "llm":
        if "model" in entry:
            attrs["llm.model"] = entry["model"]
        if "tokens_in" in entry:
            attrs["llm.tokens.input"] = entry["tokens_in"]
        if "tokens_out" in entry:
            attrs["llm.tokens.output"] = entry["tokens_out"]
        if "ms" in entry:
            attrs["llm.duration_ms"] = entry["ms"]
    
    elif tag == "tool":
        if "tool" in entry:
            attrs["tool.name"] = entry["tool"]
        if "success" in entry:
            attrs["tool.success"] = entry["success"]
        if "ms" in entry:
            attrs["tool.duration_ms"] = entry["ms"]
    
    elif tag == "session":
        if "session_id" in entry:
            attrs["session.id"] = entry["session_id"]
        if "agent" in entry:
            attrs["agent.name"] = entry["agent"]
        if "task" in entry:
            attrs["agent.task"] = entry["task"]
    
    # Add remaining context as flat attributes
    if "ctx" in entry and isinstance(entry["ctx"], dict):
        for key, value in entry["ctx"].items():
            attr_key = f"agentlog.ctx.{key}"
            attrs[attr_key] = _serialize_value(value)
    
    return attrs


def _serialize_value(value: Any) -> Any:
    """Serialize value to OTEL-compatible format."""
    if isinstance(value, (str, int, float, bool)):
        return value
    elif value is None:
        return "null"
    else:
        return str(value)[:200]  # Truncate complex values


# ---------------------------------------------------------------------------
# OTEL Export
# ---------------------------------------------------------------------------

def to_otlp_logs(
    entries: Optional[List[Dict[str, Any]]] = None,
    resource_attributes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert agentlog entries to OTEL LogRecord format.
    
    Args:
        entries: Log entries to convert (default: all from buffer)
        resource_attributes: Resource-level attributes
        
    Returns:
        OTEL ResourceLogs structure
        
    Example:
        >>> otlp = to_otlp_logs()
        >>> print(json.dumps(otlp, indent=2))
    """
    from ._buffer import get_context
    
    if entries is None:
        # Get all entries from buffer
        raw = get_context(max_tokens=10000)
        entries = []
        for line in raw.strip().split('\n'):
            if line and not line.startswith('#'):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    # Build ResourceLogs
    resource_attrs = resource_attributes or {}
    resource_attrs["service.name"] = resource_attrs.get("service.name", "agentlog")
    resource_attrs["service.version"] = resource_attrs.get("service.version", "1.0.0")
    
    log_records = []
    for entry in entries:
        ts = entry.get("ts", datetime.now().timestamp())
        
        # Convert to nanoseconds since epoch
        time_unix_nano = int(ts * 1_000_000_000)
        
        log_record = {
            "timeUnixNano": str(time_unix_nano),
            "severityNumber": _map_severity(entry.get("tag", "info")),
            "severityText": entry.get("tag", "info").upper(),
            "body": {
                "stringValue": json.dumps(entry, default=str, separators=(',', ':'))[:1000]
            },
            "attributes": [
                {"key": k, "value": _to_otel_value(v)}
                for k, v in _convert_to_otel_attributes(entry).items()
            ]
        }
        log_records.append(log_record)
    
    return {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": k, "value": _to_otel_value(v)}
                    for k, v in resource_attrs.items()
                ]
            },
            "scopeLogs": [{
                "scope": {
                    "name": "agentlog",
                    "version": "1.0.0"
                },
                "logRecords": log_records
            }]
        }]
    }


def _map_severity(tag: str) -> int:
    """Map agentlog tag to OTEL severity number."""
    severity_map = {
        "debug": 5,
        "info": 9,
        "warn": 13,
        "error": 17,
        "fatal": 21,
    }
    return severity_map.get(tag, 9)


def _to_otel_value(value: Any) -> Dict[str, Any]:
    """Convert Python value to OTEL AnyValue."""
    if isinstance(value, str):
        return {"stringValue": value}
    elif isinstance(value, bool):
        return {"boolValue": value}
    elif isinstance(value, int):
        return {"intValue": str(value)}
    elif isinstance(value, float):
        return {"doubleValue": value}
    else:
        return {"stringValue": str(value)[:200]}


# ---------------------------------------------------------------------------
# Export to String
# ---------------------------------------------------------------------------

def export_otlp_json(
    entries: Optional[List[Dict[str, Any]]] = None,
    resource_attributes: Optional[Dict[str, Any]] = None
) -> str:
    """
    Export as OTEL JSON string.
    
    Args:
        entries: Log entries to export
        resource_attributes: Resource-level attributes
        
    Returns:
        OTEL-formatted JSON string
    """
    otlp = to_otlp_logs(entries, resource_attributes)
    return json.dumps(otlp, indent=2, default=str)


def export_otlp_proto(
    entries: Optional[List[Dict[str, Any]]] = None
) -> bytes:
    """
    Export as OTEL protobuf bytes (placeholder).
    
    Note: Full protobuf support would require protobuf library.
    This returns JSON bytes as a fallback.
    """
    json_str = export_otlp_json(entries)
    return json_str.encode('utf-8')


# ---------------------------------------------------------------------------
# Span Export (for tracing integration)
# ---------------------------------------------------------------------------

def to_otlp_spans(
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert session/trace to OTEL Span format.
    
    Args:
        trace_id: Optional trace ID to filter
        
    Returns:
        OTEL ResourceSpans structure
    """
    from ._trace import get_trace_id
    from ._buffer import get_context
    
    if trace_id is None:
        trace_id = get_trace_id()
    
    # Get trace-related entries
    entries = []
    raw = get_context(tags=["trace", "span", "llm", "tool"])
    for line in raw.strip().split('\n'):
        if line and not line.startswith('#'):
            try:
                entry = json.loads(line)
                if entry.get("trace") == trace_id or entry.get("trace_id") == trace_id:
                    entries.append(entry)
            except json.JSONDecodeError:
                pass
    
    spans = []
    for entry in entries:
        ts = entry.get("ts", datetime.now().timestamp())
        span = {
            "traceId": trace_id or "unknown",
            "spanId": entry.get("span_id", "unknown"),
            "name": entry.get("fn", entry.get("tag", "unknown")),
            "kind": 1,  # INTERNAL
            "startTimeUnixNano": str(int(ts * 1_000_000_000)),
            "endTimeUnixNano": str(int((ts + entry.get("ms", 0) / 1000) * 1_000_000_000)),
            "attributes": [
                {"key": k, "value": _to_otel_value(v)}
                for k, v in _convert_to_otel_attributes(entry).items()
            ]
        }
        spans.append(span)
    
    return {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "agentlog"}}
                ]
            },
            "scopeSpans": [{
                "scope": {
                    "name": "agentlog",
                    "version": "1.0.0"
                },
                "spans": spans
            }]
        }]
    }


def export_spans_json(trace_id: Optional[str] = None) -> str:
    """Export spans as OTEL JSON string."""
    otlp = to_otlp_spans(trace_id)
    return json.dumps(otlp, indent=2, default=str)
