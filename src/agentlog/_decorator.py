"""
Function decorator for automatic entry/exit/args/return/duration logging.
"""

import os
import json
import time
import inspect
import functools
import logging
from typing import Any, Dict

from ._core import is_enabled
from ._describe import describe
from ._emit import _ensure_handler, _next_seq, _logger


def log_func(func=None, *, log_args=True, log_return=True, log_time=True):
    """
    Decorator to log function entry, exit, args, return value, and duration.

    Works with both sync and async functions.

    Example:
        @log_func
        def create_skill(name: str, source: str) -> dict: ...

        @log_func(log_return=False)
        async def fetch_all_embeddings() -> list: ...
    """
    def decorator(fn):
        fn_name = f"{fn.__module__}.{fn.__qualname__}"

        def _get_caller():
            try:
                return {
                    "file": os.path.basename(inspect.getfile(fn)),
                    "line": inspect.getsourcelines(fn)[1],
                    "function": fn.__qualname__,
                }
            except (OSError, TypeError):
                return {"file": "?", "line": 0, "function": fn.__qualname__}

        def _build_args_desc(args, kwargs):
            if not log_args:
                return None
            try:
                sig = inspect.signature(fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                return {
                    k: describe(v) for k, v in bound.arguments.items()
                    if k != "self"
                }
            except Exception:
                return None

        def _emit_func(tag_data, caller_info):
            from ._core import get_tag_prefix
            _ensure_handler()
            entry = {
                "seq": _next_seq(),
                "ts": time.time(),
                "at": f"{caller_info['file']}:{caller_info['line']} {caller_info['function']}",
                **tag_data,
            }
            prefix = get_tag_prefix()
            _logger.debug(
                f"[{prefix}:func] {json.dumps(entry, default=str, separators=(',', ':'))}"
            )

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                if not is_enabled():
                    return await fn(*args, **kwargs)
                caller = _get_caller()
                entry_data: Dict[str, Any] = {"fn": fn_name, "ev": "entry"}
                args_desc = _build_args_desc(args, kwargs)
                if args_desc:
                    entry_data["args"] = args_desc
                _emit_func(entry_data, caller)

                t0 = time.monotonic()
                try:
                    result = await fn(*args, **kwargs)
                except Exception as e:
                    elapsed = round((time.monotonic() - t0) * 1000, 1)
                    _emit_func({
                        "fn": fn_name, "ev": "exception",
                        "err": type(e).__name__, "err_msg": str(e),
                        "ms": elapsed,
                    }, caller)
                    raise

                elapsed = round((time.monotonic() - t0) * 1000, 1)
                exit_data: Dict[str, Any] = {"fn": fn_name, "ev": "exit"}
                if log_return:
                    exit_data["ret"] = describe(result)
                if log_time:
                    exit_data["ms"] = elapsed
                _emit_func(exit_data, caller)
                return result
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                if not is_enabled():
                    return fn(*args, **kwargs)
                caller = _get_caller()
                entry_data: Dict[str, Any] = {"fn": fn_name, "ev": "entry"}
                args_desc = _build_args_desc(args, kwargs)
                if args_desc:
                    entry_data["args"] = args_desc
                _emit_func(entry_data, caller)

                t0 = time.monotonic()
                try:
                    result = fn(*args, **kwargs)
                except Exception as e:
                    elapsed = round((time.monotonic() - t0) * 1000, 1)
                    _emit_func({
                        "fn": fn_name, "ev": "exception",
                        "err": type(e).__name__, "err_msg": str(e),
                        "ms": elapsed,
                    }, caller)
                    raise

                elapsed = round((time.monotonic() - t0) * 1000, 1)
                exit_data: Dict[str, Any] = {"fn": fn_name, "ev": "exit"}
                if log_return:
                    exit_data["ret"] = describe(result)
                if log_time:
                    exit_data["ms"] = elapsed
                _emit_func(exit_data, caller)
                return result
            return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator
