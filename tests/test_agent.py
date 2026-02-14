"""
Tests for agent workflow optimization features (Phase 2).
"""

import pytest
from agentlog import (
    enable, disable,
    log_llm_call, log_tool_call, log_prompt, log_response,
    llm_call, tool_call
)


def test_log_llm_call_basic(capsys):
    """Test basic LLM call logging."""
    enable()
    
    call_id = log_llm_call(
        "gpt-4",
        "Explain Python decorators",
        response="A decorator is a function...",
        duration_ms=1250.5,
        tokens_in=10,
        tokens_out=150
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:llm]" in output
    assert "gpt-4" in output
    assert "Explain Python decorators" in output
    assert "1250.5" in output
    assert call_id  # Should return correlation ID


def test_log_llm_call_with_context(capsys):
    """Test LLM call with additional context."""
    enable()
    
    log_llm_call(
        "claude-3-opus",
        "Write a Python function",
        temperature=0.7,
        max_tokens=500
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:llm]" in output
    assert "claude-3-opus" in output
    assert "temperature" in output


def test_log_tool_call_basic(capsys):
    """Test basic tool call logging."""
    enable()
    
    call_id = log_tool_call(
        "search_database",
        {"query": "Python skills", "limit": 10},
        result={"count": 5, "items": []},
        duration_ms=45.2,
        success=True
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:tool]" in output
    assert "search_database" in output
    assert "Python skills" in output
    assert "45.2" in output
    assert call_id


def test_log_tool_call_failure(capsys):
    """Test tool call with failure."""
    enable()
    
    log_tool_call(
        "fetch_data",
        {"url": "http://example.com"},
        success=False
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:tool]" in output
    assert "fetch_data" in output
    assert "false" in output.lower()


def test_log_prompt_response_correlation(capsys):
    """Test prompt/response correlation."""
    enable()
    
    # Log prompt
    prompt_id = log_prompt(
        "Explain decorators",
        model="gpt-4",
        temperature=0.7
    )
    
    # Log response
    log_response(
        prompt_id,
        "A decorator is...",
        duration_ms=1200,
        tokens_out=150
    )
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should have both prompt and response
    assert "[AGENTLOG:prompt]" in output
    assert "[AGENTLOG:response]" in output
    assert prompt_id in output
    assert "Explain decorators" in output


def test_llm_call_context_manager(capsys):
    """Test LLM call context manager."""
    enable()
    
    with llm_call("gpt-4", "Test prompt") as call:
        # Simulate API call
        call["response"] = "Test response"
        call["tokens_out"] = 50
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:llm]" in output
    assert "gpt-4" in output
    assert "Test prompt" in output
    assert "Test response" in output


def test_llm_call_context_manager_with_error(capsys):
    """Test LLM call context manager with exception."""
    enable()
    
    with pytest.raises(ValueError):
        with llm_call("gpt-4", "Test prompt") as call:
            raise ValueError("API error")
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should still log even with error
    assert "[AGENTLOG:llm]" in output
    assert "ValueError" in output


def test_tool_call_context_manager(capsys):
    """Test tool call context manager."""
    enable()
    
    with tool_call("search_db", {"query": "Python"}) as call:
        # Simulate tool execution
        call["result"] = {"count": 5}
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "[AGENTLOG:tool]" in output
    assert "search_db" in output
    assert "Python" in output


def test_tool_call_context_manager_with_error(capsys):
    """Test tool call context manager with exception."""
    enable()
    
    with pytest.raises(RuntimeError):
        with tool_call("fetch_data", {"url": "test"}) as call:
            raise RuntimeError("Connection failed")
    
    captured = capsys.readouterr()
    output = captured.out
    
    # Should still log even with error
    assert "[AGENTLOG:tool]" in output
    assert "RuntimeError" in output
    assert "false" in output.lower()  # success=false


def test_llm_call_when_disabled():
    """Test that LLM call is no-op when disabled."""
    disable()
    
    call_id = log_llm_call("gpt-4", "test")
    assert call_id == ""


def test_tool_call_when_disabled():
    """Test that tool call is no-op when disabled."""
    disable()
    
    call_id = log_tool_call("test_tool", {})
    assert call_id == ""


def test_prompt_when_disabled():
    """Test that prompt is no-op when disabled."""
    disable()
    
    prompt_id = log_prompt("test")
    assert prompt_id == ""


def test_context_manager_when_disabled():
    """Test that context managers work when disabled."""
    disable()
    
    # Should not raise errors
    with llm_call("gpt-4", "test") as call:
        call["response"] = "test"
    
    with tool_call("test_tool", {}) as call:
        call["result"] = "test"
