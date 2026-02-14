"""Tests for agentlog._decorator — @log_func."""

import json
import asyncio
import pytest
from agentlog import log_func


def _get_entries(capsys):
    """Parse all AGENTLOG entries from captured output."""
    out = capsys.readouterr().out
    entries = []
    for line in out.strip().split('\n'):
        if '[AGENTLOG:' in line:
            json_str = line.split('] ', 1)[1]
            entries.append(json.loads(json_str))
    return entries


def test_sync_function(capsys):
    @log_func
    def add(a, b):
        return a + b

    result = add(1, 2)
    assert result == 3

    entries = _get_entries(capsys)
    entry_ev = [e for e in entries if e.get("ev") == "entry"]
    exit_ev = [e for e in entries if e.get("ev") == "exit"]
    assert len(entry_ev) == 1
    assert len(exit_ev) == 1
    assert exit_ev[0]["ret"]["v"] == 3
    assert "ms" in exit_ev[0]


def test_async_function(capsys):
    @log_func
    async def async_add(a, b):
        return a + b

    result = asyncio.run(async_add(3, 4))
    assert result == 7

    entries = _get_entries(capsys)
    entry_ev = [e for e in entries if e.get("ev") == "entry"]
    exit_ev = [e for e in entries if e.get("ev") == "exit"]
    assert len(entry_ev) == 1
    assert len(exit_ev) == 1
    assert exit_ev[0]["ret"]["v"] == 7


def test_exception_logged(capsys):
    @log_func
    def failing():
        raise ValueError("test error")

    with pytest.raises(ValueError):
        failing()

    entries = _get_entries(capsys)
    exc_ev = [e for e in entries if e.get("ev") == "exception"]
    assert len(exc_ev) == 1
    assert exc_ev[0]["err"] == "ValueError"
    assert exc_ev[0]["err_msg"] == "test error"


def test_async_exception_logged(capsys):
    @log_func
    async def async_failing():
        raise RuntimeError("async error")

    with pytest.raises(RuntimeError):
        asyncio.run(async_failing())

    entries = _get_entries(capsys)
    exc_ev = [e for e in entries if e.get("ev") == "exception"]
    assert len(exc_ev) == 1
    assert exc_ev[0]["err"] == "RuntimeError"


def test_log_func_with_options(capsys):
    @log_func(log_return=False, log_time=False)
    def multiply(a, b):
        return a * b

    result = multiply(3, 4)
    assert result == 12

    entries = _get_entries(capsys)
    exit_ev = [e for e in entries if e.get("ev") == "exit"]
    assert len(exit_ev) == 1
    assert "ret" not in exit_ev[0]
    assert "ms" not in exit_ev[0]


def test_preserves_function_metadata():
    @log_func
    def documented_func():
        """This is documented."""
        pass

    assert documented_func.__name__ == "documented_func"
    assert documented_func.__doc__ == "This is documented."


def test_noop_when_disabled(capsys):
    from agentlog import disable, enable
    disable()

    @log_func
    def silent_func():
        return 42

    result = silent_func()
    assert result == 42
    out = capsys.readouterr().out
    assert "AGENTLOG" not in out
    enable()
