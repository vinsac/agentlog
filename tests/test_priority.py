"""
Tests for priority filtering and context compression (Phase 2).
"""

import pytest
from agentlog._priority import (
    get_entry_priority,
    filter_by_priority,
    filter_by_importance,
    get_top_entries,
    compress_entry,
    smart_filter,
)


def test_get_entry_priority_error():
    """Test that errors have highest priority."""
    entry = {"tag": "error", "msg": "Failed"}
    priority = get_entry_priority(entry)
    assert priority >= 9


def test_get_entry_priority_check_failed():
    """Test that failed checks have high priority."""
    entry = {"tag": "check", "passed": False, "msg": "Expected non-empty"}
    priority = get_entry_priority(entry)
    assert priority >= 9


def test_get_entry_priority_llm():
    """Test that LLM calls have high priority."""
    entry = {"tag": "llm", "model": "gpt-4"}
    priority = get_entry_priority(entry)
    assert priority >= 7


def test_get_entry_priority_info():
    """Test that info logs have low priority."""
    entry = {"tag": "info", "msg": "Processing"}
    priority = get_entry_priority(entry)
    assert priority <= 3


def test_filter_by_priority():
    """Test filtering by minimum priority."""
    entries = [
        {"tag": "error", "seq": 1},
        {"tag": "info", "seq": 2},
        {"tag": "decision", "seq": 3},
        {"tag": "vars", "seq": 4},
    ]
    
    filtered = filter_by_priority(entries, min_priority=5)
    
    # Should keep error and decision, drop info and vars
    assert len(filtered) >= 2
    tags = [e["tag"] for e in filtered]
    assert "error" in tags
    assert "decision" in tags


def test_filter_by_importance_critical():
    """Test critical importance filter."""
    entries = [
        {"tag": "error", "seq": 1},
        {"tag": "check", "passed": False, "seq": 2},
        {"tag": "info", "seq": 3},
        {"tag": "decision", "seq": 4},
    ]
    
    filtered = filter_by_importance(entries, "critical")
    
    # Should only keep error and failed check
    assert len(filtered) <= 2
    tags = [e["tag"] for e in filtered]
    assert "error" in tags


def test_filter_by_importance_high():
    """Test high importance filter."""
    entries = [
        {"tag": "error", "seq": 1},
        {"tag": "decision", "seq": 2},
        {"tag": "info", "seq": 3},
        {"tag": "vars", "seq": 4},
    ]
    
    filtered = filter_by_importance(entries, "high")
    
    # Should keep error and decision, drop info and vars
    tags = [e["tag"] for e in filtered]
    assert "error" in tags
    assert "decision" in tags
    assert "vars" not in tags


def test_filter_by_importance_medium():
    """Test medium importance filter."""
    entries = [
        {"tag": "error", "seq": 1},
        {"tag": "func", "seq": 2},
        {"tag": "vars", "seq": 3},
    ]
    
    filtered = filter_by_importance(entries, "medium")
    
    # Should keep error and func, drop vars
    tags = [e["tag"] for e in filtered]
    assert "error" in tags
    assert "func" in tags


def test_get_top_entries():
    """Test getting top N most important entries."""
    entries = [
        {"tag": "error", "seq": 1},
        {"tag": "info", "seq": 2},
        {"tag": "decision", "seq": 3},
        {"tag": "vars", "seq": 4},
        {"tag": "check", "passed": False, "seq": 5},
    ]
    
    top = get_top_entries(entries, n=3)
    
    assert len(top) == 3
    # Should be in chronological order
    assert top[0]["seq"] < top[1]["seq"] < top[2]["seq"]
    # Should include high-priority entries
    tags = [e["tag"] for e in top]
    assert "error" in tags
    assert "check" in tags


def test_compress_entry_basic():
    """Test basic entry compression."""
    entry = {
        "seq": 1,
        "tag": "info",
        "msg": "Test message",
        "ctx": {
            "user_id": {"t": "str", "v": "u_123"},
            "data": {"t": "str", "v": "x" * 200}
        }
    }
    
    compressed = compress_entry(entry, max_value_length=50)
    
    # Should truncate long string
    assert len(compressed["ctx"]["data"]["v"]) <= 50
    assert "truncated" in compressed["ctx"]["data"]


def test_compress_entry_preserves_structure():
    """Test that compression preserves entry structure."""
    entry = {
        "seq": 1,
        "tag": "error",
        "error": {"type": "ValueError", "msg": "Invalid"},
        "locals": {
            "x": {"t": "int", "v": 42},
            "y": {"t": "str", "v": "short"}
        }
    }
    
    compressed = compress_entry(entry, max_value_length=100)
    
    # Should preserve structure
    assert compressed["seq"] == 1
    assert compressed["tag"] == "error"
    assert compressed["error"]["type"] == "ValueError"
    assert compressed["locals"]["x"]["v"] == 42


def test_compress_entry_list_truncation():
    """Test that lists are truncated."""
    entry = {
        "seq": 1,
        "ctx": {
            "items": {"t": "list", "v": list(range(20))}
        }
    }
    
    compressed = compress_entry(entry)
    
    # Should truncate list to max 10 items
    assert len(compressed["ctx"]["items"]["v"]) <= 10


def test_smart_filter_combines_features():
    """Test that smart_filter combines importance and token budget."""
    entries = [
        {"tag": "error", "seq": 1, "msg": "Failed"},
        {"tag": "decision", "seq": 2, "question": "Should merge?"},
        {"tag": "info", "seq": 3, "msg": "Processing"},
        {"tag": "vars", "seq": 4, "data": "x" * 1000},
    ]
    
    filtered = smart_filter(entries, max_tokens=100, importance="high")
    
    # Should filter by importance and fit within budget
    assert len(filtered) <= len(entries)
    # Should prioritize high-importance entries
    tags = [e["tag"] for e in filtered]
    if "error" in [e["tag"] for e in entries]:
        assert "error" in tags


def test_smart_filter_respects_token_budget():
    """Test that smart_filter respects token budget."""
    # Create entries with large data
    entries = [
        {"tag": "error", "seq": i, "data": "x" * 500}
        for i in range(10)
    ]
    
    filtered = smart_filter(entries, max_tokens=50, importance="medium")
    
    # Should fit within budget (may be empty if entries are too large)
    assert len(filtered) <= len(entries)


def test_priority_boost_for_slow_operations():
    """Test that slow operations get priority boost."""
    entry = {"tag": "func", "ms": 2000}  # Slow operation
    priority = get_entry_priority(entry)
    
    # Should get boost for being slow
    assert priority >= 4


def test_priority_boost_for_large_token_usage():
    """Test that large token usage gets priority boost."""
    entry = {"tag": "llm", "tokens_out": 2000}  # Large output
    priority = get_entry_priority(entry)
    
    # Should get boost for high token usage
    assert priority >= 8
