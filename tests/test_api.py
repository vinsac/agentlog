"""Tests for agentlog._api — core public API functions."""

import json
import logging
import pytest
from agentlog import log, log_vars, log_state, log_error, log_check, log_http, enable


def _capture_output(capsys, fn, *args, **kwargs):
    """Call fn and return the parsed JSON from the AGENTLOG output line."""
    fn(*args, **kwargs)
    out = capsys.readouterr().out
    # Find the AGENTLOG line
    for line in out.strip().split('\n'):
        if '[AGENTLOG:' in line:
            json_str = line.split('] ', 1)[1]
            return json.loads(json_str)
    return None


def test_log_basic(capsys):
    entry = _capture_output(capsys, log, "hello world")
    assert entry["msg"] == "hello world"
    assert entry["seq"] == 1
    assert "ts" in entry
    assert "at" in entry


def test_log_with_context(capsys):
    entry = _capture_output(capsys, log, "test", x=42, name="foo")
    assert entry["msg"] == "test"
    assert entry["ctx"]["x"]["v"] == 42
    assert entry["ctx"]["name"]["v"] == "foo"


def test_log_noop_when_disabled(capsys):
    from agentlog import disable
    disable()
    log("should not appear")
    out = capsys.readouterr().out
    assert "AGENTLOG" not in out
    enable()


def test_log_vars_kwargs(capsys):
    entry = _capture_output(capsys, log_vars, score=0.95, name="python")
    assert entry["vars"]["score"]["v"] == 0.95
    assert entry["vars"]["name"]["v"] == "python"


def test_log_state(capsys):
    entry = _capture_output(capsys, log_state, "before", {"a": 1, "b": 2})
    assert entry["label"] == "before"
    assert entry["state"]["t"] == "dict"
    assert entry["state"]["n"] == 2


def test_log_error_basic(capsys):
    entry = _capture_output(capsys, log_error, "Something failed")
    assert entry["msg"] == "Something failed"


def test_log_error_with_exception(capsys):
    try:
        raise ValueError("bad value")
    except ValueError as e:
        entry = _capture_output(capsys, log_error, "Failed", error=e, input="test")
    assert entry["err"] == "ValueError"
    assert entry["err_msg"] == "bad value"
    assert entry["ctx"]["input"]["v"] == "test"


def test_log_check_pass(capsys):
    result = log_check(True, "should pass")
    assert result is True
    out = capsys.readouterr().out
    # Passing checks don't emit
    assert "AGENTLOG" not in out


def test_log_check_fail(capsys):
    result = log_check(False, "expected positive", value=-1)
    assert result is False
    out = capsys.readouterr().out
    assert "AGENTLOG:check" in out
    entry = json.loads(out.strip().split('] ', 1)[1])
    assert entry["msg"] == "expected positive"
    assert entry["passed"] is False


def test_log_http(capsys):
    entry = _capture_output(capsys, log_http, "POST", "/api/skills", 201, 45.2)
    assert entry["method"] == "POST"
    assert entry["url"] == "/api/skills"
    assert entry["status"] == 201
    assert entry["ms"] == 45.2


def test_log_http_minimal(capsys):
    entry = _capture_output(capsys, log_http, "GET", "/health")
    assert entry["method"] == "GET"
    assert entry["url"] == "/health"
    assert "status" not in entry
    assert "ms" not in entry


def test_sequence_increments(capsys):
    e1 = _capture_output(capsys, log, "first")
    e2 = _capture_output(capsys, log, "second")
    assert e2["seq"] > e1["seq"]
