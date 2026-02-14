"""
Tests for token estimation.
"""

import pytest
from agentlog._tokens import estimate_tokens, estimate_tokens_dict, fit_entries_to_budget


def test_estimate_tokens_empty():
    """Test token estimation for empty string."""
    assert estimate_tokens("") == 0


def test_estimate_tokens_short():
    """Test token estimation for short strings."""
    assert estimate_tokens("hi") >= 1
    assert estimate_tokens("hello") >= 1


def test_estimate_tokens_sentence():
    """Test token estimation for a sentence."""
    text = "The quick brown fox jumps over the lazy dog"
    tokens = estimate_tokens(text)
    # Should be roughly 9-12 tokens
    assert 8 <= tokens <= 15


def test_estimate_tokens_json():
    """Test token estimation for JSON structure."""
    text = '{"name":"test","value":123,"items":[1,2,3]}'
    tokens = estimate_tokens(text)
    # JSON structure adds extra tokens
    assert tokens > 5


def test_estimate_tokens_long_word():
    """Test that long words are split into subwords."""
    text = "supercalifragilisticexpialidocious"
    tokens = estimate_tokens(text)
    # Long word should be multiple tokens
    assert tokens > 3


def test_estimate_tokens_dict():
    """Test token estimation for dictionaries."""
    data = {"name": "test", "value": 123, "items": [1, 2, 3]}
    tokens = estimate_tokens_dict(data)
    assert tokens > 0


def test_estimate_tokens_dict_complex():
    """Test token estimation for complex nested structures."""
    data = {
        "user_id": "u_123",
        "profile": {
            "name": "Alice",
            "age": 30,
            "skills": ["Python", "JavaScript", "Go"]
        },
        "metadata": {
            "created_at": "2026-02-14",
            "updated_at": "2026-02-14"
        }
    }
    tokens = estimate_tokens_dict(data)
    # Should be roughly 30-50 tokens
    assert 20 <= tokens <= 60


def test_fit_entries_to_budget_empty():
    """Test fitting empty entries list."""
    result = fit_entries_to_budget([], 1000)
    assert result == []


def test_fit_entries_to_budget_single():
    """Test fitting single entry within budget."""
    entries = [{"msg": "test", "value": 123}]
    result = fit_entries_to_budget(entries, 1000)
    assert len(result) == 1
    assert result[0] == entries[0]


def test_fit_entries_to_budget_multiple():
    """Test fitting multiple entries within budget."""
    entries = [
        {"msg": "entry1", "value": 1},
        {"msg": "entry2", "value": 2},
        {"msg": "entry3", "value": 3},
    ]
    result = fit_entries_to_budget(entries, 1000)
    assert len(result) == 3


def test_fit_entries_to_budget_exceeds():
    """Test that entries are truncated when budget is exceeded."""
    entries = [
        {"msg": "entry1", "data": "x" * 100},
        {"msg": "entry2", "data": "y" * 100},
        {"msg": "entry3", "data": "z" * 100},
    ]
    # Small budget should only fit 1-2 entries
    result = fit_entries_to_budget(entries, 20)
    assert len(result) < len(entries)


def test_fit_entries_to_budget_chronological_order():
    """Test that entries are returned in chronological order."""
    entries = [
        {"seq": 1, "msg": "first"},
        {"seq": 2, "msg": "second"},
        {"seq": 3, "msg": "third"},
    ]
    result = fit_entries_to_budget(entries, 1000)
    assert result[0]["seq"] == 1
    assert result[1]["seq"] == 2
    assert result[2]["seq"] == 3


def test_fit_entries_to_budget_most_recent():
    """Test that most recent entries are prioritized."""
    entries = [
        {"seq": 1, "msg": "old", "data": "x" * 100},
        {"seq": 2, "msg": "recent", "data": "y" * 100},
    ]
    # Small budget should only fit the most recent
    result = fit_entries_to_budget(entries, 50)
    assert len(result) == 1
    assert result[0]["seq"] == 2  # Most recent


def test_fit_entries_to_budget_realistic():
    """Test with realistic log entries."""
    entries = [
        {
            "seq": 1,
            "ts": 1234567890.0,
            "at": "main.py:42 process_skill",
            "msg": "Processing request",
            "ctx": {"user_id": {"t": "str", "v": "u_123"}}
        },
        {
            "seq": 2,
            "ts": 1234567891.0,
            "at": "main.py:45 process_skill",
            "error": {"type": "ValueError", "msg": "Invalid input"},
            "locals": {"confidence": {"t": "float", "v": 0.3}}
        },
    ]
    result = fit_entries_to_budget(entries, 100)
    # Should fit at least one entry
    assert len(result) >= 1
