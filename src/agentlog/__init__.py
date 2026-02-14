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

# Session management
from ._session import (
    start_session,
    end_session,
    get_session_id,
    get_parent_session_id,
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

# Agent workflow optimization
from ._agent import (
    log_llm_call,
    log_tool_call,
    log_prompt,
    log_response,
    llm_call,
    tool_call,
)

# Schema validation and exports
from ._schema import (
    validate_entry,
    validate_value_descriptor,
    export_schema_json,
    export_schema_typescript,
    export_schema_go,
    validate_jsonl_file,
)

# Framework adapters
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

# Cross-run correlation
from ._correlation import (
    hash_error,
    record_error_pattern,
    get_error_pattern,
    get_all_patterns,
    find_similar_errors,
    correlate_error,
    get_pattern_stats,
)

# Workspace state snapshots
from ._workspace import (
    snapshot_workspace,
    compare_snapshots,
    save_snapshot,
    load_snapshot,
    snapshot_session,
    compare_to_session_baseline,
    hash_file,
)

# Evaluation & Outcome Tagging
from ._outcome import (
    tag_outcome,
    tag_session_outcome,
    get_outcome,
    get_all_outcomes,
    get_outcome_stats,
    detect_outcome_from_logs,
    auto_tag_session,
    OUTCOME_SUCCESS,
    OUTCOME_FAILURE,
    OUTCOME_PARTIAL,
    OUTCOME_UNKNOWN,
)

# Regression Detection
from ._regression import (
    set_baseline,
    get_baseline,
    list_baselines,
    delete_baseline,
    detect_regression,
    compare_to_baseline,
    generate_regression_report,
)

# Structured Output Templates
from ._formats import (
    get_formatted_context,
    list_formats,
    get_format_description,
    to_mcp_resource,
    to_mcp_tool_result,
)

# OpenTelemetry Bridge
from ._otel import (
    to_otlp_logs,
    to_otlp_spans,
    export_otlp_json,
    export_otlp_proto,
    export_spans_json,
)

# MCP Server
from ._mcp import (
    run_mcp_server,
    mcp_entry,
    handle_list_resources,
    handle_read_resource,
    handle_list_tools,
    handle_call_tool,
)

# Remote Sync (Optional D1)
from ._remote import (
    is_d1_enabled,
    init_d1_schema,
    sync_session_to_d1,
    load_session_from_d1,
    list_d1_sessions,
    delete_d1_session,
    share_session,
    import_shared_session,
)

# Intelligent Context Pruning
from ._prune import (
    prune_context,
    compress_context,
    get_context_summary,
    score_entry_importance,
    summarize_entries,
)

# Visual Diff Rendering
from ._visual import (
    render_git_diff,
    render_session_diff,
    get_diff_summary,
    export_diff_for_review,
    render_diff_markdown,
    render_diff_html,
)

# Team Analytics
from ._analytics import (
    record_session_analytics,
    get_team_stats,
    get_error_trends,
    get_common_issues,
    get_agent_performance,
    compare_periods,
    generate_team_report,
    export_analytics,
    clear_analytics,
)

# Clear Winner Feature 1: One-Shot Crash Fixer
from ._fixer import (
    fix_this_crash,
    analyze_crash,
)

# Clear Winner Feature 2: Multi-Agent Flow Visualizer
from ._flow import (
    visualize_agent_flow,
    get_cascade_summary,
)

# Clear Winner Feature 3: Regression Validator
from ._validate import (
    validate_refactoring,
    quick_validate,
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
    "get_parent_session_id",
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
    # Cross-run correlation
    "hash_error",
    "record_error_pattern",
    "get_error_pattern",
    "get_all_patterns",
    "find_similar_errors",
    "correlate_error",
    "get_pattern_stats",
    # Workspace snapshots
    "snapshot_workspace",
    "compare_snapshots",
    "save_snapshot",
    "load_snapshot",
    "snapshot_session",
    "compare_to_session_baseline",
    "hash_file",
    # Evaluation & Outcomes
    "tag_outcome",
    "tag_session_outcome",
    "get_outcome",
    "get_all_outcomes",
    "get_outcome_stats",
    "detect_outcome_from_logs",
    "auto_tag_session",
    "OUTCOME_SUCCESS",
    "OUTCOME_FAILURE",
    "OUTCOME_PARTIAL",
    "OUTCOME_UNKNOWN",
    # Regression Detection
    "set_baseline",
    "get_baseline",
    "list_baselines",
    "delete_baseline",
    "detect_regression",
    "compare_to_baseline",
    "generate_regression_report",
    # Structured Output Templates
    "get_formatted_context",
    "list_formats",
    "get_format_description",
    "to_mcp_resource",
    "to_mcp_tool_result",
    # OpenTelemetry Bridge
    "to_otlp_logs",
    "to_otlp_spans",
    "export_otlp_json",
    "export_spans_json",
    # MCP Server
    "run_mcp_server",
    "mcp_entry",
    # Remote Sync
    "is_d1_enabled",
    "sync_session_to_d1",
    "load_session_from_d1",
    "list_d1_sessions",
    "share_session",
    "import_shared_session",
    # Intelligent Context Pruning
    "prune_context",
    "compress_context",
    "get_context_summary",
    "score_entry_importance",
    "summarize_entries",
    # Visual Diff Rendering
    "render_git_diff",
    "render_session_diff",
    "get_diff_summary",
    "export_diff_for_review",
    # Team Analytics
    "record_session_analytics",
    "get_team_stats",
    "get_error_trends",
    "get_common_issues",
    "get_agent_performance",
    "compare_periods",
    "generate_team_report",
    "export_analytics",
    "clear_analytics",
    # One-Shot Crash Fixer ⭐
    "fix_this_crash",
    "analyze_crash",
    # Multi-Agent Flow Visualizer 🌊
    "visualize_agent_flow",
    "get_cascade_summary",
    # Regression Validator ✅
    "validate_refactoring",
    "quick_validate",
    # Agent workflow
    "log_llm_call",
    "log_tool_call",
    "log_prompt",
    "log_response",
    "llm_call",
    "tool_call",
    # Schema validation
    "validate_entry",
    "validate_value_descriptor",
    "export_schema_json",
    "export_schema_typescript",
    "export_schema_go",
    "validate_jsonl_file",
    # Framework adapters
    "fastapi_middleware",
    "flask_before_request",
    "flask_after_request",
    "DjangoMiddleware",
    "log_endpoint",
    "asgi_middleware",
    "wsgi_middleware",
]
