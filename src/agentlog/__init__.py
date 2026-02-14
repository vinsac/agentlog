"""
agentlog — Runtime observability for AI coding agents.

Structured, token-efficient logging that works in both development
and production, designed specifically for AI agents to consume.

    pip install agentlog

Toggle:
    AGENTLOG=true                # enable (recommended)
    AGENTLOG_LEVEL=info          # filter by level (debug/info/warn/error)
    DEVLOG=true                  # legacy toggle (also works)

Usage:
    from agentlog import log, log_vars, log_error, log_func, span

    log("Processing request", user_id=uid, skill_name=name)
    log_vars(confidence, embedding_vector, result_dict)

    @log_func
    async def create_skill(name: str) -> dict: ...

    with span("normalize"):
        result = normalize(raw_name)

Output:
    [AGENTLOG:info] {"seq":1,"ts":1739512200,"at":"main.py:42 create_skill","msg":"Processing","ctx":{...}}

Reference: https://github.com/vinsac/agentlog
License: MIT
"""

__version__ = "1.0.0"

# Core configuration
from ._core import (
    enable,
    disable,
    configure,
    is_enabled,
    enable_dev_logging,
    disable_dev_logging,
)

# Core logging API
from ._api import (
    log,
    log_vars,
    log_state,
    log_error,
    log_check,
    log_http,
)

# Function decorator
from ._decorator import log_func

# Distributed tracing
from ._trace import (
    trace,
    trace_end,
    get_trace_id,
    span,
)

# Advanced observability
from ._advanced import (
    log_decision,
    log_flow,
    log_diff,
    log_query,
    log_perf,
)

# Context budget
from ._buffer import (
    get_context,
    summary,
    set_buffer_size,
)

# File sink
from ._sink import (
    to_file,
    close_file,
)

__all__ = [
    # Version
    "__version__",
    # Configuration
    "enable",
    "disable",
    "configure",
    "is_enabled",
    "enable_dev_logging",
    "disable_dev_logging",
    # Core API
    "log",
    "log_vars",
    "log_state",
    "log_error",
    "log_check",
    "log_http",
    # Decorator
    "log_func",
    # Tracing
    "trace",
    "trace_end",
    "get_trace_id",
    "span",
    # Advanced
    "log_decision",
    "log_flow",
    "log_diff",
    "log_query",
    "log_perf",
    # Context budget
    "get_context",
    "summary",
    "set_buffer_size",
    # File sink
    "to_file",
    "close_file",
]
