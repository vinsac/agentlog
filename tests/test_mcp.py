"""
Tests for MCP server module (Phase 4).
"""

import pytest
import json
from agentlog._mcp import (
    handle_list_resources,
    handle_read_resource,
    handle_list_tools,
    handle_call_tool,
    MCP_TOOLS,
)


class TestListResources:
    """Test resource listing."""
    
    def test_list_resources_structure(self):
        """Resources have expected structure."""
        result = handle_list_resources()
        
        assert "resources" in result
        assert isinstance(result["resources"], list)
        assert len(result["resources"]) >= 3
        
        # Check for expected resources
        uris = [r["uri"] for r in result["resources"]]
        assert any("agentlog://debug/" in uri for uri in uris)
        assert "agentlog://summary" in uris
        assert "agentlog://patterns" in uris
    
    def test_resource_has_required_fields(self):
        """Each resource has required fields."""
        result = handle_list_resources()
        
        for resource in result["resources"]:
            assert "uri" in resource
            assert "name" in resource
            assert "mimeType" in resource
            assert "description" in resource


class TestReadResource:
    """Test resource reading."""
    
    def test_read_debug_resource(self):
        """Read debug context resource."""
        result = handle_read_resource("agentlog://debug/test-session")
        
        assert result is not None
        assert "contents" in result
        assert len(result["contents"]) == 1
        assert "text" in result["contents"][0]
    
    def test_read_summary_resource(self):
        """Read summary resource."""
        result = handle_read_resource("agentlog://summary")
        
        assert result is not None
        assert "contents" in result
    
    def test_read_patterns_resource(self):
        """Read patterns resource."""
        result = handle_read_resource("agentlog://patterns")
        
        assert result is not None
        assert "contents" in result
    
    def test_read_unknown_resource(self):
        """Unknown resource returns None."""
        result = handle_read_resource("agentlog://unknown")
        assert result is None


class TestListTools:
    """Test tool listing."""
    
    def test_list_tools_structure(self):
        """Tools have expected structure."""
        result = handle_list_tools()
        
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) >= 4
    
    def test_tool_definitions(self):
        """Each tool has required fields."""
        for tool in MCP_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool


class TestCallTool:
    """Test tool calling."""
    
    def test_call_get_debug_context(self):
        """Call get_debug_context tool."""
        result = handle_call_tool("get_debug_context", {"max_tokens": 1000, "format": "raw"})
        
        assert result is not None
        assert "content" in result
        assert isinstance(result["content"], list)
    
    def test_call_get_error_patterns(self):
        """Call get_error_patterns tool."""
        result = handle_call_tool("get_error_patterns", {})
        
        assert result is not None
        assert "content" in result
    
    def test_call_unknown_tool(self):
        """Unknown tool returns None."""
        result = handle_call_tool("unknown_tool", {})
        assert result is None
    
    def test_tools_have_descriptions(self):
        """All tools have descriptions."""
        for tool in MCP_TOOLS:
            assert tool["description"]
            assert len(tool["description"]) > 0
