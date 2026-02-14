"""Tests for agentlog._buffer — ringbuffer, context export, summary."""

import json
import pytest
from agentlog import log, log_error, log_check, get_context, summary, set_buffer_size, enable
from agentlog import _buffer


def test_ringbuffer_captures_entries():
    log("entry 1")
    log("entry 2")
    s = summary()
    assert s["total"] >= 2


def test_get_context_returns_jsonl():
    log("test line")
    ctx = get_context()
    assert len(ctx) > 0
    # Each line should be valid JSON
    for line in ctx.strip().split('\n'):
        if line:
            parsed = json.loads(line)
            assert "seq" in parsed


def test_get_context_respects_token_budget():
    for i in range(100):
        log(f"message {i}", data="x" * 100)
    # Very small budget
    ctx = get_context(max_tokens=50)
    assert len(ctx) < 50 * 4 + 100  # some slack


def test_get_context_filters_by_tag():
    log("info msg")
    log_error("error msg")
    ctx = get_context(tags=["error"])
    lines = [l for l in ctx.strip().split('\n') if l]
    for line in lines:
        parsed = json.loads(line)
        assert parsed["tag"] == "error"


def test_get_context_last_n():
    for i in range(20):
        log(f"msg {i}")
    ctx = get_context(last_n=5)
    lines = [l for l in ctx.strip().split('\n') if l]
    assert len(lines) == 5


def test_summary_counts_tags():
    log("info 1")
    log("info 2")
    log_error("err 1")
    s = summary()
    assert s["by_tag"].get("info", 0) >= 2
    assert s["by_tag"].get("error", 0) >= 1


def test_summary_captures_errors():
    try:
        raise ValueError("test error")
    except ValueError as e:
        log_error("Failed", error=e)
    s = summary()
    assert len(s["errors"]) >= 1
    assert "Failed" in s["errors"][-1]


def test_summary_captures_failed_checks():
    log_check(False, "should be positive")
    s = summary()
    assert "should be positive" in s["failed_checks"]


def test_set_buffer_size():
    for i in range(100):
        log(f"msg {i}")
    set_buffer_size(10)
    s = summary()
    assert s["total"] <= 10


def test_summary_structure():
    s = summary()
    assert "total" in s
    assert "by_tag" in s
    assert "errors" in s
    assert "failed_checks" in s
    assert "slowest_funcs" in s
    assert "traces" in s
