"""
MCP (Model Context Protocol) server for agentlog (Phase 4).

Provides native integration with Cursor, Claude Desktop, and other MCP clients.
"""

import json
import sys
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# MCP Resource Handlers
# ---------------------------------------------------------------------------

def handle_list_resources() -> Dict[str, Any]:
    """
    Handle MCP list_resources request.
    
    Returns available resources for the client.
    """
    from ._session import get_session_id
    
    session_id = get_session_id() or "unknown"
    
    return {
        "resources": [
            {
                "uri": f"agentlog://debug/{session_id}",
                "name": f"AgentLog Debug Context ({session_id[:8]}...)",
                "mimeType": "application/x-ndjson",
                "description": "Current session debug context with errors and events"
            },
            {
                "uri": "agentlog://summary",
                "name": "AgentLog Session Summary",
                "mimeType": "application/json",
                "description": "Compact summary of current session"
            },
            {
                "uri": "agentlog://patterns",
                "name": "Error Patterns",
                "mimeType": "application/json",
                "description": "Detected error patterns across sessions"
            }
        ]
    }


def handle_read_resource(uri: str) -> Optional[Dict[str, Any]]:
    """
    Handle MCP read_resource request.
    
    Args:
        uri: Resource URI to read
        
    Returns:
        Resource content or None if not found
    """
    from ._buffer import get_debug_context, summary
    from ._correlation import get_all_patterns
    from ._session import get_session_id
    
    if uri.startswith("agentlog://debug/"):
        context = get_debug_context(max_tokens=8000)
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/x-ndjson",
                    "text": context
                }
            ]
        }
    
    elif uri == "agentlog://summary":
        s = summary()
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(s, default=str, indent=2)
                }
            ]
        }
    
    elif uri == "agentlog://patterns":
        patterns = get_all_patterns()
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(patterns, default=str, indent=2)
                }
            ]
        }
    
    return None


# ---------------------------------------------------------------------------
# MCP Tool Handlers
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "get_debug_context",
        "description": "Get agentlog debug context for the current session",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to return",
                    "default": 4000
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["raw", "cursor", "claude", "codex"],
                    "default": "raw"
                }
            }
        }
    },
    {
        "name": "get_error_patterns",
        "description": "Get detected error patterns across sessions",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "check_regression",
        "description": "Check for regressions compared to baseline",
        "inputSchema": {
            "type": "object",
            "properties": {
                "baseline_id": {
                    "type": "string",
                    "description": "Baseline to compare against",
                    "default": "stable"
                }
            }
        }
    },
    {
        "name": "tag_session",
        "description": "Tag current session with outcome",
        "inputSchema": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "description": "Session outcome",
                    "enum": ["success", "failure", "partial", "unknown"]
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for outcome"
                }
            },
            "required": ["outcome"]
        }
    }
]


def handle_list_tools() -> Dict[str, Any]:
    """Handle MCP list_tools request."""
    return {"tools": MCP_TOOLS}


def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle MCP call_tool request.
    
    Args:
        name: Tool name to call
        arguments: Tool arguments
        
    Returns:
        Tool result or None if tool not found
    """
    from ._buffer import get_debug_context
    from ._correlation import get_all_patterns, get_pattern_stats
    from ._regression import detect_regression, generate_regression_report
    from ._outcome import tag_session_outcome
    from ._formats import get_formatted_context
    
    if name == "get_debug_context":
        max_tokens = arguments.get("max_tokens", 4000)
        format = arguments.get("format", "raw")
        
        context = get_formatted_context(format, max_tokens)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": context
                }
            ]
        }
    
    elif name == "get_error_patterns":
        patterns = get_all_patterns()
        stats = get_pattern_stats()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "patterns": patterns,
                        "stats": stats
                    }, default=str, indent=2)
                }
            ]
        }
    
    elif name == "check_regression":
        baseline_id = arguments.get("baseline_id", "stable")
        
        report = generate_regression_report(baseline_id)
        
        if report is None:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No baseline set. Use set_baseline() first."
                    }
                ],
                "isError": True
            }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(report, default=str, indent=2)
                }
            ]
        }
    
    elif name == "tag_session":
        outcome = arguments.get("outcome")
        reason = arguments.get("reason", "")
        
        success = tag_session_outcome(outcome, reason)
        
        if not success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Failed to tag session. Is a session active?"
                    }
                ],
                "isError": True
            }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Session tagged with outcome: {outcome}"
                }
            ]
        }
    
    return None


# ---------------------------------------------------------------------------
# MCP Server Loop
# ---------------------------------------------------------------------------

def run_mcp_server():
    """
    Run MCP server over stdin/stdout.
    
    This implements the Model Context Protocol for Cursor/Claude Desktop.
    """
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")
            
            response = {"jsonrpc": "2.0", "id": request_id}
            
            if method == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "resources": {},
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "agentlog",
                        "version": "1.0.0"
                    }
                }
            
            elif method == "resources/list":
                response["result"] = handle_list_resources()
            
            elif method == "resources/read":
                uri = request.get("params", {}).get("uri")
                result = handle_read_resource(uri)
                if result:
                    response["result"] = result
                else:
                    response["error"] = {
                        "code": -32602,
                        "message": f"Resource not found: {uri}"
                    }
            
            elif method == "tools/list":
                response["result"] = handle_list_tools()
            
            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})
                
                result = handle_call_tool(name, arguments)
                if result:
                    response["result"] = result
                else:
                    response["error"] = {
                        "code": -32601,
                        "message": f"Tool not found: {name}"
                    }
            
            elif method == "notifications/initialized":
                # No response needed for notifications
                continue
            
            else:
                response["error"] = {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            # Skip invalid JSON lines
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            # Log error but keep running
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response), flush=True)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def mcp_entry():
    """Entry point for `agentlog mcp` command."""
    run_mcp_server()


if __name__ == "__main__":
    mcp_entry()
