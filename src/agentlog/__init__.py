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
)

# Session management (Phase 1)
from ._session import (
    start_session,
    end_session,
    get_session_id,
    get_parent_session_id,  # Phase 2: Session linking
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

# Agent workflow optimization (Phase 2)
from ._agent import (
    log_llm_call,
    log_tool_call,
    log_prompt,
    log_response,
    llm_call,
    tool_call,
)

# Schema validation and exports (Phase 3)
from ._schema import (
    validate_entry,
    validate_value_descriptor,
    export_schema_json,
    export_schema_typescript,
    export_schema_go,
    validate_jsonl_file,
)

# Framework adapters (Phase 3)
from ._adapters import (
    fastapi_middleware,
    flask_before_request,
    flask_after_request,
    DjangoMiddleware,
    log_endpoint,
    asgi_middleware,
    wsgi_middleware,
)

# Context budget
from ._buffer import (
    get_context,
    get_context_smart,
    get_debug_context,
    summary,
    token_summary,
    set_buffer_size,
)

# File sink
from ._sink import (
    to_file,
    close_file,
)

# Automatic failure capture
from ._failure import (
    install_failure_hook,
    uninstall_failure_hook,
)

# Phase 2: Cross-run correlation
from ._correlation import (
    hash_error,
    record_error_pattern,
    get_error_pattern,
    get_all_patterns,
    find_similar_errors,
    correlate_error,
    get_pattern_stats,
)

# Phase 2: Workspace state snapshots
from ._workspace import (
    snapshot_workspace,
    compare_snapshots,
    save_snapshot,
    load_snapshot,
    snapshot_session,
    compare_to_session_baseline,
    hash_file,
)

# Install failure hook automatically if enabled
if is_enabled():
    install_failure_hook()

__all__ = [
    # Version
    "__version__",
    # Configuration
    "enable",
    "disable",
    "configure",
    "is_enabled",
    # Session
    "start_session",
    "end_session",
    "get_session_id",
    "get_parent_session_id",  # Phase 2
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
    "get_context_smart",
    "get_debug_context",
    "summary",
    "token_summary",
    "set_buffer_size",
    # File sink
    "to_file",
    "close_file",
    # Automatic failure capture
    "install_failure_hook",
    "uninstall_failure_hook",
    # Phase 2: Cross-run correlation
    "hash_error",
    "record_error_pattern",
    "get_error_pattern",
    "get_all_patterns",
    "find_similar_errors",
    "correlate_error",
    "get_pattern_stats",
    # Phase 2: Workspace snapshots
    "snapshot_workspace",
    "compare_snapshots",
    "save_snapshot",
    "load_snapshot",
    "snapshot_session",
    "compare_to_session_baseline",
    "hash_file",
    # Agent workflow (Phase 2)
    "log_llm_call",
    "log_tool_call",
    "log_prompt",
    "log_response",
    "llm_call",
    "tool_call",
    # Schema validation (Phase 3)
    "validate_entry",
    "validate_value_descriptor",
    "export_schema_json",
    "export_schema_typescript",
    "export_schema_go",
    "validate_jsonl_file",
    # Framework adapters (Phase 3)
    "fastapi_middleware",
    "flask_before_request",
    "flask_after_request",
    "DjangoMiddleware",
    "log_endpoint",
    "asgi_middleware",
    "wsgi_middleware",
]
