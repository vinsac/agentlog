"""Tests for agentlog._trace — distributed tracing and spans."""

import json
import pytest
from agentlog import trace, trace_end, get_trace_id, span, log, enable


def _get_entries(capsys):
    """Parse all AGENTLOG entries from captured output."""
    out = capsys.readouterr().out
    entries = []
    for line in out.strip().split('\n'):
        if '[AGENTLOG:' in line:
            json_str = line.split('] ', 1)[1]
            entries.append(json.loads(json_str))
    return entries


def test_trace_generates_id():
    tid = trace()
    assert tid is not None
    assert len(tid) == 16
    trace_end()


def test_trace_uses_provided_id():
    tid = trace("custom-trace-123")
    assert tid == "custom-trace-123"
    trace_end()


def test_get_trace_id():
    assert get_trace_id() is None
    tid = trace()
    assert get_trace_id() == tid
    trace_end()
    assert get_trace_id() is None


def test_trace_id_injected_into_logs(capsys):
    tid = trace("test-trace")
    log("inside trace")
    entries = _get_entries(capsys)
    # Find the info log
    info_entries = [e for e in entries if e.get("msg") == "inside trace"]
    assert len(info_entries) == 1
    assert info_entries[0]["trace"] == "test-trace"
    trace_end()


def test_span_basic(capsys):
    with span("test_operation"):
        pass
    entries = _get_entries(capsys)
    starts = [e for e in entries if e.get("ev") == "start"]
    ends = [e for e in entries if e.get("ev") == "end"]
    assert len(starts) == 1
    assert starts[0]["span_name"] == "test_operation"
    assert len(ends) == 1
    assert "ms" in ends[0]


def test_span_with_context(capsys):
    with span("normalize", input="python"):
        pass
    entries = _get_entries(capsys)
    starts = [e for e in entries if e.get("ev") == "start"]
    assert starts[0]["ctx"]["input"]["v"] == "python"


def test_span_error(capsys):
    with pytest.raises(ValueError):
        with span("failing_op"):
            raise ValueError("test error")
    entries = _get_entries(capsys)
    errors = [e for e in entries if e.get("ev") == "error"]
    assert len(errors) == 1
    assert errors[0]["err"] == "ValueError"
    assert errors[0]["err_msg"] == "test error"


def test_nested_spans(capsys):
    with span("outer"):
        with span("inner"):
            pass
    entries = _get_entries(capsys)
    starts = [e for e in entries if e.get("ev") == "start"]
    assert len(starts) == 2
    assert starts[0]["span_name"] == "outer"
    assert starts[1]["span_name"] == "inner"
    # Inner span should have a span ID from outer
    assert "span" in starts[1]


def test_span_yields_id():
    with span("test") as sid:
        assert sid is not None
        assert len(sid) == 12
