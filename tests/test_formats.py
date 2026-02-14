"""
Tests for structured output formats module (Phase 4).
"""

import pytest
import json
from agentlog._formats import (
    get_formatted_context,
    list_formats,
    get_format_description,
    to_mcp_resource,
    to_mcp_tool_result,
    _cursor_template,
    _claude_template,
    _codex_template,
    _raw_template,
)


class TestFormatList:
    """Test format listing."""
    
    def test_list_formats(self):
        """List available formats."""
        formats = list_formats()
        assert "cursor" in formats
        assert "claude" in formats
        assert "codex" in formats
        assert "raw" in formats
        assert "jsonl" in formats
    
    def test_format_descriptions(self):
        """Get format descriptions."""
        assert "Cursor" in get_format_description("cursor")
        assert "Claude" in get_format_description("claude")
        assert "Codex" in get_format_description("codex")
        assert "raw" in get_format_description("raw")


class TestTemplates:
    """Test individual templates."""
    
    def test_cursor_template_structure(self):
        """Cursor template has expected structure."""
        entries = [{"tag": "error", "msg": "test"}]
        header = {"session_id": "sess_123", "git": {"branch": "main", "commit": "abc1234"}}
        
        result = _cursor_template(entries, header)
        
        assert "AgentLog Debug Context" in result
        assert "sess_123" in result
        assert "main@abc123" in result
        assert "ERROR" in result
    
    def test_claude_template_structure(self):
        """Claude template has expected XML structure."""
        entries = [{"tag": "error", "msg": "test"}]
        header = {"session_id": "sess_123"}
        
        result = _claude_template(entries, header)
        
        assert "<debug_context>" in result
        assert "<metadata>" in result
        assert "<events>" in result
        assert "<event type=\"error\">" in result
    
    def test_codex_template_structure(self):
        """Codex template has expected markdown structure."""
        entries = [{"tag": "error", "msg": "test"}]
        header = {"session_id": "sess_123"}
        
        result = _codex_template(entries, header)
        
        assert "## Debug Context" in result
        assert "**ERROR**" in result
        assert "```json" in result
    
    def test_raw_template_structure(self):
        """Raw template has JSONL structure."""
        entries = [{"tag": "error", "msg": "test", "seq": 1}]
        header = {"session_id": "sess_123", "git": {"branch": "main", "commit": "abc1234"}}
        
        result = _raw_template(entries, header)
        
        assert "# agentlog debug context" in result
        assert "sess_123" in result
        assert '"tag":"error"' in result or '"tag": "error"' in result


class TestFormattedContext:
    """Test get_formatted_context function."""
    
    def test_get_formatted_context_raw(self):
        """Get context in raw format."""
        context = get_formatted_context("raw", max_tokens=1000)
        assert isinstance(context, str)
    
    def test_get_formatted_context_cursor(self):
        """Get context in cursor format."""
        context = get_formatted_context("cursor", max_tokens=1000)
        assert isinstance(context, str)
        assert "AgentLog Debug Context" in context
    
    def test_get_formatted_context_claude(self):
        """Get context in claude format."""
        context = get_formatted_context("claude", max_tokens=1000)
        assert isinstance(context, str)
        assert "<debug_context>" in context
    
    def test_get_formatted_context_codex(self):
        """Get context in codex format."""
        context = get_formatted_context("codex", max_tokens=1000)
        assert isinstance(context, str)
        assert "## Debug Context" in context
    
    def test_get_formatted_context_invalid_format(self):
        """Invalid format falls back to raw."""
        context = get_formatted_context("invalid_format", max_tokens=1000)
        assert isinstance(context, str)


class TestMCPHelpers:
    """Test MCP integration helpers."""
    
    def test_to_mcp_resource_structure(self):
        """MCP resource has expected structure."""
        resource = to_mcp_resource()
        
        assert "uri" in resource
        assert "mimeType" in resource
        assert "text" in resource
        assert resource["mimeType"] == "application/x-ndjson"
    
    def test_to_mcp_tool_result_structure(self):
        """MCP tool result has expected structure."""
        result = to_mcp_tool_result()
        
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0
        assert "type" in result["content"][0]
        assert "text" in result["content"][0]
