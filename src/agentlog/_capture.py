"""
Canonical v2 capture primitives plus legacy IO capture utility.
"""

import sys
import io
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterable, Optional, Tuple

from ._core import is_enabled
from ._describe import describe
from ._emit import emit

@contextmanager
def capture_io() -> Generator[Tuple[io.StringIO, io.StringIO], None, None]:
    """
    Capture stdout and stderr.
    
    Yields:
        (stdout_capture, stderr_capture) streams.
    """
    # Create new streams
    new_out = io.StringIO()
    new_err = io.StringIO()
    
    # Save original streams
    old_out = sys.stdout
    old_err = sys.stderr
    
    try:
        # Redirect
        sys.stdout = new_out
        sys.stderr = new_err
        yield new_out, new_err
    finally:
        # Restore
        sys.stdout = old_out
        sys.stderr = old_err


def breadcrumb(event: str, **ctx: Any) -> None:
    """Record a structured breadcrumb for later debug-context assembly."""
    if not is_enabled():
        return
    data: Dict[str, Any] = {"event": event}
    _promote_common_fields(data, ctx)
    if ctx:
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("info", data)


def start_operation(name: str, **ctx: Any) -> str:
    """Start a named operation and return its operation id."""
    operation_id = ctx.pop("operation_id", None) or f"op_{uuid.uuid4().hex[:12]}"
    if not is_enabled():
        return operation_id
    data: Dict[str, Any] = {
        "operation_id": operation_id,
        "name": name,
        "event": "start",
    }
    _promote_common_fields(data, ctx)
    if ctx:
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("operation", data)
    return operation_id


def end_operation(status: str = "success", **ctx: Any) -> None:
    """End a named operation."""
    if not is_enabled():
        return
    data: Dict[str, Any] = {"event": "end", "status": status}
    if ctx:
        operation_id = ctx.pop("operation_id", None)
        name = ctx.pop("name", None)
        _promote_common_fields(data, ctx)
        if operation_id:
            data["operation_id"] = operation_id
        if name:
            data["name"] = name
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("operation", data)


def capture_decision(
    decision_type: str,
    chosen: Any,
    candidates: Optional[Iterable[Any]] = None,
    **ctx: Any,
) -> None:
    """Capture a decision with candidates, scores, thresholds, and rationale."""
    if not is_enabled():
        return
    data: Dict[str, Any] = {
        "decision_type": decision_type,
        "chosen": describe(chosen, field_name="chosen"),
    }
    _promote_common_fields(data, ctx)
    if candidates is not None:
        data["candidates"] = describe(list(candidates), field_name="candidates")
    if ctx:
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("decision", data)


def capture_tool_call(
    name: str,
    input: Optional[Any] = None,
    output: Optional[Any] = None,
    error: Optional[BaseException] = None,
    **ctx: Any,
) -> str:
    """Capture a tool or function-call summary."""
    if not is_enabled():
        return ""
    call_id = str(ctx.pop("call_id", None) or uuid.uuid4().hex[:8])
    data: Dict[str, Any] = {"call_id": call_id, "tool": name, "success": error is None}
    _promote_common_fields(data, ctx)
    if input is not None:
        data["input"] = describe(input, field_name="input")
        if isinstance(input, dict):
            data["args"] = {key: describe(value, field_name=key) for key, value in input.items()}
    if output is not None:
        data["output"] = describe(output, field_name="output")
        data["result"] = data["output"]
    if error is not None:
        data["error"] = {"type": type(error).__name__, "msg": str(error)}
    if ctx:
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("tool", data)
    return call_id


def capture_llm_call(
    model: str,
    input: Optional[Any] = None,
    output: Optional[Any] = None,
    usage: Optional[Dict[str, Any]] = None,
    error: Optional[BaseException] = None,
    **ctx: Any,
) -> str:
    """Capture an LLM interaction summary."""
    if not is_enabled():
        return ""
    call_id = str(ctx.pop("call_id", None) or uuid.uuid4().hex[:8])
    data: Dict[str, Any] = {"call_id": call_id, "model": model}
    _promote_common_fields(data, ctx)
    if input is not None:
        data["input"] = describe(input, field_name="input")
        data["prompt"] = data["input"]
    if output is not None:
        data["output"] = describe(output, field_name="output")
        data["response"] = data["output"]
    if usage:
        if "tokens_in" in usage:
            data["tokens_in"] = usage["tokens_in"]
        if "tokens_out" in usage:
            data["tokens_out"] = usage["tokens_out"]
        if "prompt_tokens" in usage:
            data["tokens_in"] = usage["prompt_tokens"]
        if "completion_tokens" in usage:
            data["tokens_out"] = usage["completion_tokens"]
        data["usage"] = usage
    if error is not None:
        data["error"] = {"type": type(error).__name__, "msg": str(error)}
    if ctx:
        data["ctx"] = {key: describe(value, field_name=key) for key, value in ctx.items()}
    emit("llm", data)
    return call_id


@contextmanager
def operation(name: str, **ctx: Any):
    """Context manager for operation capture."""
    operation_id = start_operation(name, **ctx)
    started = time.time()
    try:
        yield operation_id
    except Exception as error:
        end_operation(
            "error",
            operation_id=operation_id,
            name=name,
            duration_ms=round((time.time() - started) * 1000, 1),
            error=str(error),
        )
        raise
    else:
        end_operation(
            "success",
            operation_id=operation_id,
            name=name,
            duration_ms=round((time.time() - started) * 1000, 1),
        )


def _promote_common_fields(data: Dict[str, Any], ctx: Dict[str, Any]) -> None:
    """Promote common correlation fields out of ctx for fast filtering."""
    for key in ("incident_id", "request_id", "correlation_id"):
        if key in ctx:
            data[key] = ctx.pop(key)
