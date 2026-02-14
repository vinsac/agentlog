"""
Backward compatibility shim for devlog API names.

Allows existing code using devlog to migrate to agentlog with minimal changes:

    # Old (devlog)
    from devlog import devlog, devlog_vars, devlog_func

    # Migration step 1: change import source
    from agentlog.compat import devlog, devlog_vars, devlog_func

    # Migration step 2 (optional): rename to new API
    from agentlog import log, log_vars, log_func
"""

from . import (
    log as devlog,
    log_vars as devlog_vars,
    log_state as devlog_state,
    log_error as devlog_error,
    log_check as devlog_check,
    log_http as devlog_http,
    log_func as devlog_func,
    trace as devlog_trace,
    trace_end as devlog_trace_end,
    get_trace_id,
    span as devlog_span,
    log_decision as devlog_decision,
    log_flow as devlog_flow,
    log_diff as devlog_diff,
    log_query as devlog_query,
    log_perf as devlog_perf,
    to_file as devlog_to_file,
    close_file as devlog_close_file,
    get_context as devlog_get_context,
    set_buffer_size as devlog_set_buffer_size,
    summary as devlog_summary,
    enable,
    disable,
    enable_dev_logging,
    disable_dev_logging,
)

__all__ = [
    "devlog",
    "devlog_vars",
    "devlog_state",
    "devlog_error",
    "devlog_check",
    "devlog_http",
    "devlog_func",
    "devlog_trace",
    "devlog_trace_end",
    "get_trace_id",
    "devlog_span",
    "devlog_decision",
    "devlog_flow",
    "devlog_diff",
    "devlog_query",
    "devlog_perf",
    "devlog_to_file",
    "devlog_close_file",
    "devlog_get_context",
    "devlog_set_buffer_size",
    "devlog_summary",
    "enable",
    "disable",
    "enable_dev_logging",
    "disable_dev_logging",
]
