"""
Core public API for agentlog.

Provides: log, log_vars, log_state, log_error, log_check, log_http
"""

import inspect
import traceback
from typing import Any, Dict, Optional

from ._core import is_enabled
from ._describe import describe
from ._emit import emit


def log(message: str, **kwargs: Any) -> None:
    """
    Log a message with optional key-value context.

    Example:
        log("Processing request", user_id=uid, skill_name=name)
        log("Cache miss", key=cache_key, ttl=ttl_seconds)
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {"msg": message}
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("info", data)


def log_vars(*args: Any, **kwargs: Any) -> None:
    """
    Log variable names, types, and values.

    Positional args: variable names extracted from source code.
    Keyword args: key is used as the variable name.

    Example:
        log_vars(skill_name, confidence, embeddings)
        log_vars(result=api_response, count=len(items))
    """
    if not is_enabled():
        return

    variables: Dict[str, Any] = {}

    if args:
        try:
            frame = inspect.stack()[1]
            src = frame.code_context[0].strip() if frame.code_context else ""
            # Try to extract variable names from source
            for fn_name in ("log_vars(", "devlog_vars("):
                if fn_name in src:
                    inner = src.split(fn_name, 1)[1].rsplit(")", 1)[0]
                    names = [a.strip() for a in inner.split(",")]
                    for i, val in enumerate(args):
                        name = names[i] if i < len(names) and "=" not in names[i] else f"arg{i}"
                        variables[name] = describe(val)
                    break
            else:
                for i, val in enumerate(args):
                    variables[f"arg{i}"] = describe(val)
        except Exception:
            for i, val in enumerate(args):
                variables[f"arg{i}"] = describe(val)

    for name, val in kwargs.items():
        variables[name] = describe(val)

    emit("vars", {"vars": variables})


def log_state(label: str, state: Any) -> None:
    """
    Log a state snapshot. Use before/after pairs to track mutations.

    Example:
        log_state("profile_before", profile.__dict__)
        profile.skills = new_skills
        log_state("profile_after", profile.__dict__)
    """
    if not is_enabled():
        return
    emit("state", {"label": label, "state": describe(state)})


def log_error(message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
    """
    Log an error with traceback and context.

    Example:
        try:
            result = await normalize(name)
        except Exception as e:
            log_error("Normalization failed", error=e, input_name=name)
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {"msg": message}
    if error:
        data["err"] = type(error).__name__
        data["err_msg"] = str(error)
        data["tb"] = traceback.format_exc()
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("error", data)


def log_check(condition: bool, message: str, **kwargs: Any) -> bool:
    """
    Runtime assertion that logs instead of crashing. Returns the condition.

    AI agents can scan for failed checks to understand unexpected state.

    Example:
        log_check(len(results) > 0, "Expected non-empty results", query=q)
        log_check(score >= 0.0, "Score should be non-negative", score=score)
    """
    if not is_enabled():
        return condition
    if not condition:
        data: Dict[str, Any] = {"msg": message, "passed": False}
        if kwargs:
            data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
        emit("check", data)
    return condition


def log_http(
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    **kwargs: Any,
) -> None:
    """
    Log an HTTP request/response.

    Example:
        log_http("POST", "/api/skills", 201, 45.2, body=payload)
        log_http("GET", url, resp.status_code, elapsed, error=resp.text)
    """
    if not is_enabled():
        return
    data: Dict[str, Any] = {"method": method, "url": url}
    if status_code is not None:
        data["status"] = status_code
    if duration_ms is not None:
        data["ms"] = round(duration_ms, 1)
    if kwargs:
        data["ctx"] = {k: describe(v) for k, v in kwargs.items()}
    emit("http", data)
