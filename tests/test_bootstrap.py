"""Tests for environment-driven bootstrap behavior in agentlog."""

import json

import agentlog
from agentlog import close_file, log, summary
from agentlog import _buffer


def test_bootstrap_enables_file_sink_from_env(monkeypatch, tmp_path):
    log_path = tmp_path / "logs" / "agentlog.jsonl"
    monkeypatch.setenv("AGENTLOG_FILE", str(log_path))

    agentlog._bootstrap_from_env()

    log("bootstrapped file sink")
    close_file()

    assert log_path.exists()
    with open(log_path, encoding="utf-8") as f:
        entry = json.loads(f.readline())
    assert entry["msg"] == "bootstrapped file sink"


def test_bootstrap_sets_buffer_size_from_env(monkeypatch):
    monkeypatch.setenv("AGENTLOG_BUFFER_SIZE", "7")

    agentlog._bootstrap_from_env()

    for i in range(20):
        log(f"message {i}")

    assert _buffer._ringbuffer.maxlen == 7
    assert summary()["total"] <= 7


def test_bootstrap_ignores_invalid_buffer_size(monkeypatch):
    monkeypatch.setenv("AGENTLOG_BUFFER_SIZE", "not-an-int")

    agentlog._bootstrap_from_env()

    assert _buffer._ringbuffer.maxlen == 500


def test_bootstrap_ignores_non_positive_buffer_size(monkeypatch):
    monkeypatch.setenv("AGENTLOG_BUFFER_SIZE", "0")

    agentlog._bootstrap_from_env()

    assert _buffer._ringbuffer.maxlen == 500
