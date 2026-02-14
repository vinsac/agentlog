"""Tests for agentlog.compat — backward compatibility with devlog API names."""

import json
import pytest


def test_compat_imports():
    from agentlog.compat import (
        devlog, devlog_vars, devlog_state, devlog_error,
        devlog_check, devlog_http, devlog_func,
        devlog_trace, devlog_trace_end, devlog_span,
        devlog_decision, devlog_flow, devlog_diff,
        devlog_query, devlog_perf,
        devlog_to_file, devlog_close_file,
        devlog_get_context, devlog_set_buffer_size, devlog_summary,
        enable, disable, get_trace_id,
    )
    # All should be callable
    assert callable(devlog)
    assert callable(devlog_vars)
    assert callable(devlog_func)
    assert callable(devlog_trace)
    assert callable(devlog_span)


def test_compat_devlog_works(capsys):
    from agentlog.compat import devlog
    devlog("compat test", x=42)
    out = capsys.readouterr().out
    assert "AGENTLOG:info" in out
    assert "compat test" in out


def test_compat_devlog_check_works(capsys):
    from agentlog.compat import devlog_check
    result = devlog_check(False, "compat check")
    assert result is False
    out = capsys.readouterr().out
    assert "AGENTLOG:check" in out
