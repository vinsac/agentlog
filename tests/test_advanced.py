"""Tests for agentlog._advanced — decision, flow, diff, query, perf."""

import json
import pytest
from agentlog import log_decision, log_flow, log_diff, log_query, log_perf


def _get_entry(capsys):
    """Parse the first AGENTLOG entry from captured output."""
    out = capsys.readouterr().out
    for line in out.strip().split('\n'):
        if '[AGENTLOG:' in line:
            json_str = line.split('] ', 1)[1]
            return json.loads(json_str)
    return None


def test_log_decision(capsys):
    log_decision("Use cache?", True, reason="TTL not expired", ttl=300)
    entry = _get_entry(capsys)
    assert entry["question"] == "Use cache?"
    assert entry["answer"]["v"] is True
    assert entry["reason"] == "TTL not expired"
    assert entry["ctx"]["ttl"]["v"] == 300


def test_log_decision_minimal(capsys):
    log_decision("Retry?", False)
    entry = _get_entry(capsys)
    assert entry["question"] == "Retry?"
    assert entry["answer"]["v"] is False
    assert "reason" not in entry


def test_log_flow(capsys):
    log_flow("skill_pipeline", "raw_input", "Python Programming")
    entry = _get_entry(capsys)
    assert entry["pipeline"] == "skill_pipeline"
    assert entry["step"] == "raw_input"
    assert entry["value"]["v"] == "Python Programming"


def test_log_flow_with_context(capsys):
    log_flow("pipeline", "step1", [1, 2, 3], confidence=0.95)
    entry = _get_entry(capsys)
    assert entry["value"]["t"] == "list"
    assert entry["ctx"]["confidence"]["v"] == 0.95


def test_log_diff_with_changes(capsys):
    before = {"name": "Alice", "score": 80}
    after = {"name": "Alice", "score": 95, "rank": 1}
    log_diff("profile", before, after)
    entry = _get_entry(capsys)
    assert entry["label"] == "profile"
    assert "rank" in entry["added"]
    assert "score" in entry["changed"]
    assert entry["changed"]["score"]["from"]["v"] == 80
    assert entry["changed"]["score"]["to"]["v"] == 95


def test_log_diff_no_changes(capsys):
    log_diff("same", {"a": 1}, {"a": 1})
    out = capsys.readouterr().out
    assert "AGENTLOG" not in out  # no diff = no log


def test_log_diff_removed(capsys):
    log_diff("shrink", {"a": 1, "b": 2}, {"a": 1})
    entry = _get_entry(capsys)
    assert "b" in entry["removed"]


def test_log_query(capsys):
    log_query("SELECT", "skills", 12.3, rows=42, where="active=true")
    entry = _get_entry(capsys)
    assert entry["op"] == "SELECT"
    assert entry["target"] == "skills"
    assert entry["ms"] == 12.3
    assert entry["rows"] == 42
    assert entry["ctx"]["where"]["v"] == "active=true"


def test_log_query_minimal(capsys):
    log_query("cache_get", "redis:sessions")
    entry = _get_entry(capsys)
    assert entry["op"] == "cache_get"
    assert entry["target"] == "redis:sessions"
    assert "ms" not in entry
    assert "rows" not in entry


def test_log_perf(capsys):
    log_perf("checkpoint", batch_size=100)
    entry = _get_entry(capsys)
    assert entry["label"] == "checkpoint"
    assert "pid" in entry
    assert entry["ctx"]["batch_size"]["v"] == 100


def test_log_perf_minimal(capsys):
    log_perf()
    entry = _get_entry(capsys)
    assert "pid" in entry
    assert "label" not in entry
